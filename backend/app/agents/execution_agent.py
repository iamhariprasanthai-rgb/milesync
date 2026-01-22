"""
Execution Agent for MileSync.

Handles active task management, progress tracking, and real-time adjustments.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from app.agents.base_agent import (
    AgentContext,
    AgentResponse,
    AgentType,
    BaseAgent,
    DailySummary,
    ExecutionOutput,
)

logger = logging.getLogger(__name__)


EXECUTION_SYSTEM_PROMPT = """You are the Execution Agent for MileSync, an AI goal coaching platform.

Your role is to actively manage task execution and maintain user momentum.

## EXECUTION PROTOCOL:

1. **Monitor Progress** - Track task completion status in real-time
2. **Smart Reminders** - Send contextual, non-annoying reminders
3. **Streak Tracking** - Celebrate consistency and streaks
4. **Pattern Detection** - Identify patterns in missed tasks
5. **Schedule Adjustments** - Propose adjustments proactively
6. **Progress Logging** - Record all progress with timestamps

## ADJUSTMENT CRITERIA:
- Completion rate <60%: Reduce daily task count
- Completion rate >90%: Consider adding stretch tasks
- Pattern of evening failures: Suggest morning shift
- 3+ consecutive misses: Recommend plan revision

## REMINDER INTELLIGENCE:
- Consider time of day preferences
- Adjust frequency based on completion history
- Use motivational framing when needed
- Include progress context

## COMMUNICATION STYLE:
- Action-oriented and clear
- Celebrate wins (big and small)
- Non-judgmental about misses
- Solution-focused for challenges"""


class ExecutionAgent(BaseAgent):
    """
    Execution Agent for task management and progress tracking.
    
    Handles task scheduling, progress monitoring, streak tracking,
    and recommends schedule adjustments.
    """
    
    agent_type = AgentType.EXECUTION
    agent_name = "Execution Agent"
    agent_description = "Task scheduling, progress tracking, and real-time adjustments"
    
    def get_system_prompt(self) -> str:
        """Get the Execution Agent system prompt."""
        from app.services.ai_service import get_system_prompt
        return get_system_prompt("execution_system_prompt", EXECUTION_SYSTEM_PROMPT)
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process an execution request.
        
        Args:
            context: Agent context with task and progress data
            
        Returns:
            Execution Agent response with daily summary
        """
        self.logger.info(f"Execution Agent processing for user {context.user_id}")
        
        # Check request type
        request_type = None
        if context.additional_context:
            request_type = context.additional_context.get("request_type")
        
        if request_type == "daily_summary":
            return await self._generate_daily_summary(context)
        elif request_type == "task_complete":
            return await self._handle_task_completion(context)
        else:
            return await self._generate_checkin_response(context)
    
    async def _generate_daily_summary(self, context: AgentContext) -> AgentResponse:
        """Generate daily summary with recommendations."""
        task_history = context.task_history or []
        
        # Calculate metrics
        today_tasks = [t for t in task_history if self._is_today(t.get("created_at"))]
        completed = sum(1 for t in today_tasks if t.get("status") == "completed")
        pending = len(today_tasks) - completed
        completion_rate = completed / len(today_tasks) if today_tasks else 0
        
        # Calculate streak
        streak = self._calculate_streak(task_history)
        
        # Generate recommendations
        adjustments = []
        if completion_rate < 0.6 and len(today_tasks) > 2:
            adjustments.append("Consider reducing daily tasks to 2 for better consistency")
        if completion_rate > 0.9:
            adjustments.append("Great progress! Ready for a stretch goal?")
        
        # Format next actions
        next_actions = []
        for t in today_tasks:
            if t.get("status") != "completed":
                next_actions.append(t.get("title", "Unnamed task"))
        
        # Generate motivational message
        if completion_rate >= 0.8:
            motivational = "🎉 You're crushing it! Keep up the amazing work!"
        elif completion_rate >= 0.5:
            motivational = "💪 Good progress! Let's finish strong today."
        else:
            motivational = "🌟 Every step counts. What's one thing you can do right now?"
        
        output = ExecutionOutput(
            daily_summary=DailySummary(
                tasks_completed=completed,
                tasks_pending=pending,
                streak_count=streak,
                completion_rate=round(completion_rate, 2)
            ),
            adjustments_recommended=adjustments,
            blockers_identified=[],
            next_actions=next_actions[:3],
            motivational_message=motivational
        )
        
        return self.create_response(
            success=True,
            message=self._format_summary_message(output),
            data=output.model_dump()
        )
    
    async def _handle_task_completion(self, context: AgentContext) -> AgentResponse:
        """Handle task completion event."""
        task_id = None
        if context.additional_context:
            task_id = context.additional_context.get("task_id")
        
        # Generate celebratory response
        streak = self._calculate_streak(context.task_history or [])
        
        messages = [
            "✅ Task completed! Great job!",
            f"🔥 {streak} day streak! You're on fire!",
            "💯 Another one done! Keep the momentum going!",
            "⭐ Excellent work! Every task brings you closer."
        ]
        
        import random
        message = random.choice(messages)
        
        if streak > 0 and streak % 7 == 0:
            message += f"\n🏆 Wow! A full week streak! That's {streak} days!"
        
        return self.create_response(
            success=True,
            message=message,
            data={
                "task_id": task_id,
                "streak_count": streak,
                "action": "completed"
            }
        )
    
    async def _generate_checkin_response(self, context: AgentContext) -> AgentResponse:
        """Generate a check-in response based on conversation."""
        last_message = ""
        for msg in reversed(context.messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
        
        try:
            response_text = await self.generate_response(context, last_message)
            
            return self.create_response(
                success=True,
                message=response_text,
                data={"type": "checkin"},
                requires_user_input=True
            )
        except Exception as e:
            self.logger.error(f"Check-in error: {e}")
            return self.create_response(
                success=False,
                message="How is your progress going today? Any blockers I can help with?"
            )
    
    def _is_today(self, date_str: Optional[str]) -> bool:
        """Check if a date string is today."""
        if not date_str:
            return False
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.date() == datetime.utcnow().date()
        except (ValueError, AttributeError):
            return False
    
    def _calculate_streak(self, task_history: list) -> int:
        """Calculate current completion streak."""
        if not task_history:
            return 0
        
        # Sort by date
        completed = [
            t for t in task_history
            if t.get("status") == "completed" and t.get("completed_at")
        ]
        
        if not completed:
            return 0
        
        # Count consecutive days with completions
        streak = 0
        current_date = datetime.utcnow().date()
        
        dates_with_completions = set()
        for t in completed:
            try:
                date = datetime.fromisoformat(
                    t["completed_at"].replace("Z", "+00:00")
                ).date()
                dates_with_completions.add(date)
            except (ValueError, KeyError):
                continue
        
        # Count streak
        from datetime import timedelta
        while current_date in dates_with_completions:
            streak += 1
            current_date = current_date - timedelta(days=1)
        
        return streak
    
    def _format_summary_message(self, output: ExecutionOutput) -> str:
        """Format daily summary as readable message."""
        summary = output.daily_summary
        
        rate_emoji = "🎉" if summary.completion_rate >= 0.8 else "💪" if summary.completion_rate >= 0.5 else "🌱"
        
        next_actions = "\n".join(
            f"  • {action}" for action in output.next_actions
        ) or "  • All caught up!"
        
        return f"""## Daily Progress {rate_emoji}

**Today's Stats:**
- ✅ Completed: {summary.tasks_completed}
- ⏳ Pending: {summary.tasks_pending}
- 🔥 Streak: {summary.streak_count} days
- 📊 Completion: {int(summary.completion_rate * 100)}%

**Up Next:**
{next_actions}

{output.motivational_message}"""
