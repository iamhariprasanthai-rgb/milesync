"""Chat routes for AI coaching conversations.

Integrated with Opik for automatic evaluation and observability.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.database import get_db
from app.models.chat import ChatMessage, ChatSession, ChatStatus, MessageRole
from app.models.user import User
from app.schemas.chat import (
    ChatListItem,
    ChatSessionResponse,
    ChatSessionWithMessages,
    FinalizeRequest,
    FinalizeResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
    StartChatResponse,
)
from app.schemas.goal import FinalizeWithGoalResponse, GoalResponse
from app.services import ai_service, goal_service
from app.services.quota_service import check_user_quota, track_openai_usage
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/start", response_model=StartChatResponse, status_code=status.HTTP_201_CREATED)
async def start_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new chat session.

    Creates a new session and returns the initial AI greeting message.
    """
    # Create new session
    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    # Create initial assistant message
    initial_content = ai_service.generate_initial_message()
    message = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=initial_content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return StartChatResponse(
        session=ChatSessionResponse.model_validate(session),
        initial_message=MessageResponse.model_validate(message),
    )


@router.get("/sessions", response_model=List[ChatListItem])
async def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all chat sessions for the current user.

    Returns sessions sorted by most recent first.
    """
    # Get sessions with message counts
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = db.exec(statement).all()

    result = []
    for session in sessions:
        # Get message count
        count_stmt = (
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == session.id)
        )
        message_count = db.exec(count_stmt).one()

        # Get last message preview
        last_msg_stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_message = db.exec(last_msg_stmt).first()
        preview = last_message.content[:100] if last_message else None

        result.append(ChatListItem(
            id=session.id,
            title=session.title,
            status=session.status,
            message_count=message_count,
            last_message_preview=preview,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ))

    return result


@router.get("/{session_id}", response_model=ChatSessionWithMessages)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a chat session with all its messages.

    Returns the session metadata and full message history.
    """
    # Get session
    session = db.get(ChatSession, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get messages
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = db.exec(statement).all()

    return ChatSessionWithMessages(
        session=ChatSessionResponse.model_validate(session),
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.post("/{session_id}/message", response_model=SendMessageResponse)
async def send_message(
    session_id: int,
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message in a chat session.

    Saves the user message, generates AI response, and returns both.
    """
    # Get session
    session = db.get(ChatSession, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Check session is active
    if session.status != ChatStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send messages to a completed session",
        )

    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=data.content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get conversation history for context
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = db.exec(statement).all()

    # Generate AI response
    ai_response = None
    token_usage = None
    
    try:
        # Try to use Agent System
        from app.agents.coordinator import get_agent_coordinator
        from app.agents.base_agent import AgentContext
        
        coordinator = get_agent_coordinator()
        
        # Prepare context
        context_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        # Get goal info if available
        current_goal = None
        if session.goal_id:
            from app.models.goal import Goal
            goal = db.get(Goal, session.goal_id)
            if goal:
                current_goal = goal.model_dump()
        
        agent_context = AgentContext(
            user_id=current_user.id,
            goal_id=session.goal_id,
            session_id=session_id,
            messages=context_messages,
            current_goal=current_goal,
            additional_context={"request_type": None}  # Allow routing to infer
        )
        
        # Route request
        agent_response = await coordinator.route(agent_context)
        
        if agent_response.success and agent_response.message:
            ai_response = agent_response.message
            # Combine generic message with specific output if available
            if agent_response.agent_type == "psychological" and agent_response.data:
                 pass # Message is already formatted by agent
        else:
            # Fallback if agent failed silently
            logger.warning(f"Agent returned failure: {agent_response.message}")
            raise Exception("Agent system did not produce response")
            
    except Exception as e:
        logger.warning(f"Falling back to legacy AI service: {e}")
        # Legacy AI service fallback
        try:
            # Format for OpenAI
            message_history = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]
            
            # Check quota before making API call
            check_user_quota(db, current_user.id)
            
            ai_response, token_usage = await ai_service.generate_chat_response_with_usage(message_history)
        except ValueError:
            ai_response = (
                "I apologize, but I'm currently unable to process your request. "
                "The AI service is not configured. Please contact support."
            )
        except Exception as inner_e:
            if hasattr(inner_e, 'status_code') and inner_e.status_code == 429:
                raise
            logger.error(f"AI service error: {type(inner_e).__name__}: {inner_e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable",
            )
    
    # Track token usage separately - don't fail the request if tracking fails
    if token_usage:
        try:
            usage_info = track_openai_usage(db, current_user.id, token_usage)
            logger.info(f"User {current_user.id} token usage: {usage_info.get('tokens_used_this_call', 0)} tokens")
        except Exception as e:
            logger.warning(f"Failed to track token usage: {type(e).__name__}: {e}")

    # Save assistant message
    assistant_message = ChatMessage(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=ai_response,
    )
    db.add(assistant_message)

    # Update session timestamp
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(assistant_message)

    # Log evaluation to Opik (async, non-blocking)
    try:
        from app.services.opik_service import log_chat_evaluation, is_opik_enabled
        if is_opik_enabled():
            trace_id = str(uuid.uuid4())
            evaluation_result = log_chat_evaluation(
                trace_id=trace_id,
                user_input=data.content,
                ai_response=ai_response,
                session_id=session_id,
                user_id=current_user.id,
            )
            if evaluation_result:
                logger.info(
                    f"Chat evaluation logged - Score: {evaluation_result.get('score', 'N/A')}"
                )
    except Exception as e:
        # Non-blocking - don't fail the request if logging fails
        logger.warning(f"Failed to log chat evaluation: {e}")

    return SendMessageResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )


@router.post("/{session_id}/finalize", response_model=FinalizeWithGoalResponse)
async def finalize_session(
    session_id: int,
    data: FinalizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Finalize a chat session and create a goal from the conversation.

    Uses AI to extract structured goal data with milestones and tasks.
    """
    # Get session
    session = db.get(ChatSession, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if session.status != ChatStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already finalized",
        )

    # Get messages for goal extraction
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = db.exec(statement).all()

    if len(messages) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough conversation to create a goal. Please discuss your goal more.",
        )

    # Extract goal using AI
    message_history = [{"role": m.role, "content": m.content} for m in messages]

    try:
        goal_data = await ai_service.extract_goal_from_conversation(message_history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable",
        )

    if not goal_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract a clear goal from the conversation. Please provide more details about your goal.",
        )

    # Create goal with milestones and tasks
    goal = goal_service.create_goal_from_ai(
        db=db,
        user_id=current_user.id,
        chat_session_id=session_id,
        data=goal_data,
    )

    # Update session
    session.status = ChatStatus.FINALIZED
    session.title = goal.title
    session.goal_id = goal.id
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()
    db.refresh(session)

    # Log goal extraction evaluation to Opik
    try:
        from app.services.opik_service import log_goal_extraction_evaluation, is_opik_enabled
        if is_opik_enabled():
            trace_id = str(uuid.uuid4())
            
            # Convert goal_data to dict for logging
            goal_dict = {
                "title": goal_data.title,
                "description": goal_data.description,
                "category": goal_data.category,
                "milestones": [
                    {"title": m.title, "tasks": len(m.tasks)} 
                    for m in goal_data.milestones
                ]
            }
            
            extraction_result = log_goal_extraction_evaluation(
                trace_id=trace_id,
                conversation=message_history,
                goal_data=goal_dict,
                user_id=current_user.id,
            )
            if extraction_result:
                logger.info(
                    f"Goal extraction logged - Score: {extraction_result.get('score', 'N/A')}"
                )
    except Exception as e:
        logger.warning(f"Failed to log goal extraction evaluation: {e}")

    return FinalizeWithGoalResponse(
        goal=GoalResponse.model_validate(goal),
        message=f"Goal '{goal.title}' created with roadmap!",
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a chat session and all its messages.
    """
    # Get session
    session = db.get(ChatSession, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Delete messages first
    statement = select(ChatMessage).where(ChatMessage.session_id == session_id)
    messages = db.exec(statement).all()
    for message in messages:
        db.delete(message)

    # Delete session
    db.delete(session)
    db.commit()
