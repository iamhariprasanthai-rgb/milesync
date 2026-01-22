# Database models
# Import all models here to ensure they're registered with SQLModel

from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.goal import Goal, Milestone, Task, GoalType, TaskFrequency
from app.models.user_profile import UserProfile
from app.models.sustainability import HabitLoop, UserInsight, DailyProgress
from app.models.prompt import SystemPrompt

__all__ = [
    "User",
    "ChatSession",
    "ChatMessage",
    "Goal",
    "Milestone",
    "Task",
    "GoalType",
    "TaskFrequency",
    "UserProfile",
    "HabitLoop",
    "UserInsight",
    "DailyProgress",
    "SystemPrompt",
]

