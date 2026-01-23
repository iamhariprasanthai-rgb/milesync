"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "MileSync"
    DEBUG: bool = False

    # Database (SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./milesync.db"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # OAuth - Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "https://milesync.onrender.com/api/auth/google/callback"

    # OAuth - GitHub
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Opik - LLM Observability & Evaluation
    OPIK_API_KEY: str = ""
    OPIK_WORKSPACE: str = ""
    OPIK_PROJECT_NAME: str = "MileSync-AI-Coach"
    
    # Token Quota Settings
    DEFAULT_USER_QUOTA: int = 100000  # Default tokens per user per period
    QUOTA_RESET_DAYS: int = 30  # Days until quota resets

    # Frontend URL (for CORS and redirects)
    FRONTEND_URL: str = "http://localhost:3000"


settings = Settings()
