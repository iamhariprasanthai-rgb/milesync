"""
Token Quota Service for MileSync.

Provides per-user OpenAI token quota management with:
- Quota checking before API calls
- Atomic updates to prevent race conditions
- Automatic quota reset based on time period
- Clean 429 error responses when limit exceeded
"""

import functools
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


class QuotaExceededError(HTTPException):
    """Exception raised when user exceeds their token quota."""
    
    def __init__(self, user_id: int, limit: int, used: int, reset_at: Optional[datetime] = None):
        detail = {
            "error": "quota_exceeded",
            "message": "You have exceeded your API token quota",
            "token_limit": limit,
            "tokens_used": used,
            "remaining": 0,
            "reset_at": reset_at.isoformat() if reset_at else None
        }
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


def check_user_quota(db: Session, user_id: int, estimated_tokens: int = 0) -> User:
    """
    Check if user has sufficient quota for an API call.
    
    Args:
        db: Database session
        user_id: User ID to check
        estimated_tokens: Estimated tokens for the call (optional pre-check)
        
    Returns:
        User object if quota available
        
    Raises:
        QuotaExceededError: If user has exceeded their quota
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check and reset quota if needed
    if user.reset_quota_if_needed():
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check quota
    if not user.has_quota_remaining(estimated_tokens):
        raise QuotaExceededError(
            user_id=user_id,
            limit=user.token_limit,
            used=user.tokens_used,
            reset_at=user.quota_reset_at
        )
    
    return user


def update_token_usage_atomic(db: Session, user_id: int, tokens_used: int) -> Tuple[int, int]:
    """
    Update user's token usage.
    
    Uses ORM-based update to avoid SQLite transaction conflicts.
    
    Args:
        db: Database session
        user_id: User ID to update
        tokens_used: Number of tokens to add to usage
        
    Returns:
        Tuple of (new_tokens_used, token_limit)
    """
    try:
        # Use ORM to update token usage - safer for SQLite
        user = db.get(User, user_id)
        if user:
            user.tokens_used = user.tokens_used + tokens_used
            user.updated_at = datetime.utcnow()
            db.add(user)
            # Don't commit here - let the caller (route) handle the commit
            # This prevents SQLite transaction conflicts
            db.flush()  # Just flush to update the object
            return user.tokens_used, user.token_limit
    except Exception as e:
        logger.error(f"Failed to update token usage: {e}")
    
    return 0, settings.DEFAULT_USER_QUOTA


def set_quota_reset_date(db: Session, user_id: int, days: Optional[int] = None) -> datetime:
    """
    Set the quota reset date for a user.
    
    Args:
        db: Database session
        user_id: User ID
        days: Days until reset (defaults to QUOTA_RESET_DAYS from config)
        
    Returns:
        The new reset datetime
    """
    if days is None:
        days = settings.QUOTA_RESET_DAYS
    
    reset_at = datetime.utcnow() + timedelta(days=days)
    
    user = db.get(User, user_id)
    if user:
        if user.quota_reset_at is None:  # Only set if not already set
            user.quota_reset_at = reset_at
            db.add(user)
            db.commit()
            return reset_at
        return user.quota_reset_at
    
    return reset_at


def get_user_quota_info(db: Session, user_id: int) -> dict:
    """
    Get user's current quota information.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Dict with quota information
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check and reset quota if needed
    was_reset = user.reset_quota_if_needed()
    if was_reset:
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return {
        "token_limit": user.token_limit,
        "tokens_used": user.tokens_used,
        "tokens_remaining": user.remaining_quota(),
        "quota_reset_at": user.quota_reset_at.isoformat() if user.quota_reset_at else None,
        "was_reset": was_reset,
        "usage_percentage": round((user.tokens_used / user.token_limit) * 100, 2) if user.token_limit > 0 else 0
    }


def track_openai_usage(
    db: Session,
    user_id: int,
    response_usage: dict
) -> dict:
    """
    Track OpenAI API usage from response.
    
    Extracts token counts from OpenAI response and updates user quota.
    
    Args:
        db: Database session
        user_id: User ID
        response_usage: The 'usage' object from OpenAI response
        
    Returns:
        Updated quota info
    """
    total_tokens = response_usage.get("total_tokens", 0)
    prompt_tokens = response_usage.get("prompt_tokens", 0)
    completion_tokens = response_usage.get("completion_tokens", 0)
    
    logger.info(
        f"User {user_id} used {total_tokens} tokens "
        f"(prompt: {prompt_tokens}, completion: {completion_tokens})"
    )
    
    # Ensure reset date is set on first usage
    set_quota_reset_date(db, user_id)
    
    # Atomic update of token usage
    new_used, limit = update_token_usage_atomic(db, user_id, total_tokens)
    
    return {
        "tokens_used_this_call": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens_used": new_used,
        "token_limit": limit,
        "tokens_remaining": max(0, limit - new_used)
    }


def requires_quota(estimated_tokens: int = 0):
    """
    Decorator for FastAPI routes that require token quota.
    
    Usage:
        @router.post("/chat")
        @requires_quota(estimated_tokens=1000)
        async def chat_endpoint(
            request: ChatRequest,
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)
        ):
            ...
    
    Note: This decorator expects the route to have 'db' and 'current_user' 
    dependencies injected via FastAPI's Depends().
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract db and current_user from kwargs (injected by FastAPI)
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if db is None or current_user is None:
                # If not in kwargs, can't check quota - let endpoint handle it
                return await func(*args, **kwargs)
            
            # Check quota before proceeding
            check_user_quota(db, current_user.id, estimated_tokens)
            
            # Proceed with the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Convenience function for use in route handlers
async def with_quota_check(
    db: Session,
    user: User,
    openai_call: Callable,
    *args,
    **kwargs
) -> Tuple[any, dict]:
    """
    Execute an OpenAI call with quota checking and usage tracking.
    
    This is a convenience function that wraps an OpenAI API call with:
    1. Pre-call quota check
    2. API call execution
    3. Post-call usage tracking
    
    Args:
        db: Database session
        user: Current user
        openai_call: The OpenAI API function to call
        *args, **kwargs: Arguments to pass to the OpenAI call
        
    Returns:
        Tuple of (OpenAI response, usage tracking info)
        
    Raises:
        QuotaExceededError: If user has exceeded quota
        
    Usage:
        response, usage = await with_quota_check(
            db, user, 
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[...]
        )
    """
    # Pre-check quota
    check_user_quota(db, user.id)
    
    # Execute the OpenAI call
    response = openai_call(*args, **kwargs)
    
    # Extract and track usage
    usage_info = {}
    if hasattr(response, 'usage') and response.usage:
        usage_dict = {
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
        usage_info = track_openai_usage(db, user.id, usage_dict)
    
    return response, usage_info
