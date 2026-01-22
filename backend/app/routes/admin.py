from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_db
from datetime import datetime
from app.models.prompt import SystemPrompt
from app.schemas.admin import UserAdminView, UserAdminUpdate, SystemPromptView, SystemPromptUpdate

from app.models.user import User
from app.utils.dependencies import get_current_admin
from app.services.quota_service import set_quota_reset_date

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/prompts", response_model=List[SystemPromptView])
async def list_prompts(db: Session = Depends(get_db)):
    """List all system prompts (Admin only)"""
    return db.exec(select(SystemPrompt)).all()

@router.put("/prompts/{prompt_key}", response_model=SystemPromptView)
async def update_prompt(
    prompt_key: str,
    update: SystemPromptUpdate,
    db: Session = Depends(get_db)
):
    """Update a system prompt (Admin only)"""
    prompt = db.exec(select(SystemPrompt).where(SystemPrompt.key == prompt_key)).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
        
    prompt.content = update.content
    prompt.updated_at = datetime.utcnow()
    
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    # Invalidate cache if implemented
    from app.services.ai_service import clear_prompt_cache
    clear_prompt_cache()
    
    return prompt



@router.get("/users", response_model=List[UserAdminView])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all users (Admin only)"""
    users = db.exec(select(User).offset(skip).limit(limit)).all()
    return users

@router.put("/users/{user_id}", response_model=UserAdminView)
async def update_user(
    user_id: int,
    user_update: UserAdminUpdate,
    db: Session = Depends(get_db)
):
    """Update user status and quota (Admin only)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    if user_update.is_superuser is not None:
        user.is_superuser = user_update.is_superuser

        
    if user_update.token_limit is not None:
        user.token_limit = user_update.token_limit
        # If limit changed, ensure reset date is set if not already
        if not user.quota_reset_at:
             set_quota_reset_date(db, user.id)
             
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
