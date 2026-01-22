from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class SystemPrompt(SQLModel, table=True):
    """System prompts for AI agents."""
    
    __tablename__ = "system_prompts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True, max_length=100)
    description: str = Field(max_length=255)
    content: str = Field(sa_column_kwargs={"nullable": False})
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
