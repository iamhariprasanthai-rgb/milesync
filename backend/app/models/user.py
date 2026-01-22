"""User database model."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel
from app.config import settings


class AuthProvider(str, Enum):
    """Authentication provider types."""
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"


class User(SQLModel, table=True):
    """User model for authentication and profile data."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: Optional[str] = Field(default=None, max_length=255)
    name: str = Field(max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    auth_provider: AuthProvider = Field(default=AuthProvider.EMAIL)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Token quota fields for OpenAI usage limits
    token_limit: int = Field(default_factory=lambda: settings.DEFAULT_USER_QUOTA)
    tokens_used: int = Field(default=0)
    quota_reset_at: Optional[datetime] = Field(default=None)

    class Config:
        """Pydantic config."""
        use_enum_values = True

    def reset_quota_if_needed(self) -> bool:
        """Reset tokens_used if quota_reset_at has passed. Returns True if reset."""
        if self.quota_reset_at and datetime.utcnow() >= self.quota_reset_at:
            self.tokens_used = 0
            self.quota_reset_at = None
            return True
        return False
    
    def has_quota_remaining(self, required_tokens: int = 0) -> bool:
        """Check if user has quota remaining."""
        self.reset_quota_if_needed()
        return self.tokens_used + required_tokens <= self.token_limit
    
    def remaining_quota(self) -> int:
        """Get remaining token quota."""
        self.reset_quota_if_needed()
        return max(0, self.token_limit - self.tokens_used)
