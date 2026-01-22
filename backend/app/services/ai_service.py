"""AI service for OpenAI chat completions and goal extraction.

Integrated with Opik for comprehensive LLM observability and evaluation.
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional

from openai import OpenAI

from app.config import settings
from app.schemas.goal import AIGoalGeneration, AIMilestoneGeneration, AITaskGeneration

# Opik integration imports
try:
    from opik import track
    from opik.integrations.openai import track_openai
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    # Create a no-op decorator if Opik is not available
    def track(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else args[0]
    track_openai = lambda x: x

# Default model for all AI conversations
AI_MODEL = "gpt-4o-mini"

from sqlmodel import Session, select, create_engine
from app.models.prompt import SystemPrompt

# ... imports ...

# Default model for all AI conversations
AI_MODEL = "gpt-4o-mini"

# In-memory cache for prompts
_prompt_cache = {}

def get_db_session():
    """Create a new database session."""
    connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
    return Session(engine)

def get_system_prompt(key: str, default: str) -> str:
    """Get system prompt from cache or DB."""
    if key in _prompt_cache:
        return _prompt_cache[key]
        
    try:
        with get_db_session() as session:
            prompt = session.exec(select(SystemPrompt).where(SystemPrompt.key == key)).first()
            if prompt:
                _prompt_cache[key] = prompt.content
                return prompt.content
    except Exception as e:
        print(f"Error fetching prompt {key}: {e}")
        
    return default

def clear_prompt_cache():
    """Clear the prompt cache."""
    global _prompt_cache
    _prompt_cache = {}

# Default prompts
DEFAULT_CHAT_SYSTEM = """You are an AI goal coach for MileSync. Your role is to help users define SMART goals
(Specific, Measurable, Achievable, Relevant, Time-bound), understand their motivations,
identify potential obstacles, and create actionable plans.

Guidelines:
1. Ask clarifying questions to deeply understand the user's goal before suggesting a roadmap
2. Help break down large goals into manageable milestones
3. Be encouraging but realistic about timelines and effort required
4. Identify potential obstacles and suggest strategies to overcome them
5. When the conversation feels complete, summarize the goal and key milestones

Keep responses concise but helpful. Use a friendly, supportive tone."""

# Global tracked client - initialized once
_tracked_client = None


def get_openai_client() -> Optional[OpenAI]:
    """
    Get OpenAI client instance wrapped with Opik tracing.

    Returns:
        OpenAI client if API key is configured, None otherwise
    """
    global _tracked_client
    
    if not settings.OPENAI_API_KEY:
        return None
    
    if _tracked_client is None:
        base_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Wrap with Opik tracking if available
        if OPIK_AVAILABLE and settings.OPIK_API_KEY:
            _tracked_client = track_openai(base_client)
        else:
            _tracked_client = base_client
    
    return _tracked_client


def format_messages_for_openai(
    messages: List[dict],
    include_system: bool = True
) -> List[dict]:
    """
    Format chat messages for OpenAI API.

    Args:
        messages: List of message dicts with 'role' and 'content'
        include_system: Whether to include system prompt

    Returns:
        Formatted messages list for OpenAI
    """
    formatted = []

    if include_system:
        formatted.append({
            "role": "system",
            "content": get_system_prompt("chat_system_prompt", DEFAULT_CHAT_SYSTEM)
        })

    for msg in messages:
        formatted.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    return formatted


@track(name="generate_chat_response", tags=["chat", "ai-coaching"])
async def generate_chat_response(
    messages: List[dict],
    model: str = AI_MODEL
) -> str:
    """
    Generate AI response for chat messages.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)

    Returns:
        AI-generated response text

    Raises:
        ValueError: If OpenAI API key is not configured
        Exception: If OpenAI API call fails
    """
    client = get_openai_client()

    if not client:
        raise ValueError("OpenAI API key not configured")

    formatted_messages = format_messages_for_openai(messages)

    response = client.chat.completions.create(
        model=model,
        messages=formatted_messages,
        max_tokens=1000,
        temperature=0.7,
    )

    return response.choices[0].message.content or ""


@track(name="generate_chat_response_with_usage", tags=["chat", "ai-coaching", "quota"])
async def generate_chat_response_with_usage(
    messages: List[dict],
    model: str = AI_MODEL
) -> tuple:
    """
    Generate AI response and return token usage for quota tracking.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: OpenAI model to use

    Returns:
        Tuple of (response_text, usage_dict)
        usage_dict contains: total_tokens, prompt_tokens, completion_tokens

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    client = get_openai_client()

    if not client:
        raise ValueError("OpenAI API key not configured")

    formatted_messages = format_messages_for_openai(messages)

    response = client.chat.completions.create(
        model=model,
        messages=formatted_messages,
        max_tokens=1000,
        temperature=0.7,
    )

    # Extract usage information
    usage = None
    if response.usage:
        usage = {
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }

    return response.choices[0].message.content or "", usage


def generate_initial_message() -> str:
    """
    Generate the initial greeting message for a new chat session.

    Returns:
        Welcome message string
    """
    return (
        "Hi! I'm your AI goal coach. Tell me about a goal you'd like to achieve. "
        "It could be a New Year resolution, a short-term target, or a long-term dream. "
        "What's on your mind?"
    )


@track(name="summarize_conversation", tags=["summarization"])
async def summarize_conversation(messages: List[dict]) -> str:
    """
    Generate a summary/title for a conversation.

    Args:
        messages: List of message dicts

    Returns:
        Short summary suitable for session title
    """
    client = get_openai_client()

    if not client:
        # Reason: Fallback when OpenAI not configured
        return "Goal Discussion"

    # Build context from messages
    context = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in messages[:5]])

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Summarize this goal coaching conversation in 5 words or less. Just return the title, nothing else."
            },
            {
                "role": "user",
                "content": context
            }
        ],
        max_tokens=20,
        temperature=0.3,
    )

    return response.choices[0].message.content or "Goal Discussion"


# OpenAI tool/function definition for goal extraction
GOAL_EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_goal_roadmap",
        "description": "Extract a structured goal with milestones and tasks from the conversation",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A concise, action-oriented title for the goal (e.g., 'Learn Spanish to conversational level')"
                },
                "description": {
                    "type": "string",
                    "description": "A 1-2 sentence description of the goal and why it matters"
                },
                "category": {
                    "type": "string",
                    "enum": ["health", "career", "education", "finance", "personal", "other"],
                    "description": "The category that best fits this goal"
                },
                "target_date": {
                    "type": "string",
                    "description": "Target completion date in YYYY-MM-DD format"
                },
                "milestones": {
                    "type": "array",
                    "description": "3-7 major checkpoints to achieve the goal",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Milestone title"
                            },
                            "description": {
                                "type": "string",
                                "description": "Brief description of what this milestone involves"
                            },
                            "target_date": {
                                "type": "string",
                                "description": "Target date for this milestone in YYYY-MM-DD format"
                            },
                            "tasks": {
                                "type": "array",
                                "description": "2-5 specific, actionable tasks for this milestone",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Task title - should be specific and actionable"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Optional details about the task"
                                        },
                                        "priority": {
                                            "type": "string",
                                            "enum": ["low", "medium", "high"],
                                            "description": "Task priority level"
                                        }
                                    },
                                    "required": ["title"]
                                }
                            }
                        },
                        "required": ["title", "tasks"]
                    }
                }
            },
            "required": ["title", "description", "category", "milestones"]
        }
    }
}


@track(name="extract_goal_from_conversation", tags=["goal-extraction", "function-calling"])
async def extract_goal_from_conversation(messages: List[dict]) -> Optional[AIGoalGeneration]:
    """
    Extract structured goal data from a conversation using OpenAI function calling.

    Args:
        messages: List of message dicts from the conversation

    Returns:
        AIGoalGeneration with extracted goal structure, or None if extraction fails
    """
    client = get_openai_client()

    if not client:
        return None

    # Build conversation context
    conversation = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in messages
    ])

    default_template = """Based on the following goal coaching conversation, extract a structured goal with milestones and tasks.

The goal should be SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
Today's date is {date}. IMPORTANT: Ensure all target dates (goal and milestones) are strictly in the future, starting after {date}.
Create 3-7 milestones that logically progress toward the goal.
Each milestone should have 2-5 specific, actionable tasks.

Conversation:
{conversation}

Extract the goal structure using the provided function."""

    template = get_system_prompt("goal_extraction_template", default_template)
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    # Use formatted date in prompt to ground the model
    try:
        extraction_prompt = template.format(conversation=conversation, date=current_date)
    except KeyError:
        # Fallback if custom template doesn't support {date}
        extraction_prompt = template.format(conversation=conversation) + f"\n\nToday's date is {current_date}."""
    
    system_role = get_system_prompt("goal_extraction_system", "You are a goal extraction assistant. Analyze conversations and extract structured goals.")

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_role
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ],
        tools=[GOAL_EXTRACTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "create_goal_roadmap"}},
        max_tokens=2000,
        temperature=0.3,
    )

    # Extract the function call arguments
    message = response.choices[0].message
    if not message.tool_calls:
        return None

    tool_call = message.tool_calls[0]
    if tool_call.function.name != "create_goal_roadmap":
        return None

    try:
        goal_data = json.loads(tool_call.function.arguments)

        # Parse milestones
        milestones = []
        for m in goal_data.get("milestones", []):
            tasks = [
                AITaskGeneration(
                    title=t.get("title", ""),
                    description=t.get("description"),
                    priority=t.get("priority", "medium"),
                )
                for t in m.get("tasks", [])
            ]
            milestones.append(AIMilestoneGeneration(
                title=m.get("title", ""),
                description=m.get("description"),
                target_date=m.get("target_date"),
                tasks=tasks,
            ))

        return AIGoalGeneration(
            title=goal_data.get("title", "My Goal"),
            description=goal_data.get("description"),
            category=goal_data.get("category", "other"),
            target_date=goal_data.get("target_date"),
            milestones=milestones,
        )

    except (json.JSONDecodeError, KeyError) as e:
        # Reason: Fallback if parsing fails
        return None
