from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserAdminView(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_superuser: bool
    token_limit: int
    tokens_used: int
    quota_reset_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserAdminUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    token_limit: Optional[int] = None

class SystemPromptView(BaseModel):
    id: int
    key: str
    description: str
    content: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SystemPromptUpdate(BaseModel):
    content: str
