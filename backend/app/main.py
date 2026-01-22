"""MileSync API - Main FastAPI Application.

Integrated with Opik for comprehensive LLM observability and evaluation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: create database tables
    create_db_and_tables()
    
    # Configure Opik for LLM observability
    try:
        from app.services.opik_service import configure_opik
        opik_configured = configure_opik()
        if opik_configured:
            logger.info("✅ Opik LLM observability enabled")
        else:
            logger.warning("⚠️ Opik not configured - running without observability")
    except ImportError as e:
        logger.warning(f"⚠️ Opik package not installed: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to configure Opik: {e}")
    
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Goal Coach - Set, track, and achieve your goals. Powered by Opik observability.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    try:
        from app.services.opik_service import is_opik_enabled
        opik_status = "enabled" if is_opik_enabled() else "disabled"
    except ImportError:
        opik_status = "not_installed"
    
    return {
        "message": "Welcome to MileSync API",
        "docs": "/docs",
        "status": "healthy",
        "observability": {
            "opik": opik_status,
            "project": settings.OPIK_PROJECT_NAME if opik_status == "enabled" else None,
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


# Import models to register with SQLModel
from app.models import (  # noqa: F401
    User, ChatSession, ChatMessage, Goal, Milestone, Task,
    UserProfile, HabitLoop, UserInsight, DailyProgress
)

# Import and include routers
from app.routes import auth, chat, goals, dashboard, analytics, agents, admin

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(goals.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


