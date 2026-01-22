"""
Sustainability Agent for MileSync.

Handles long-term habit formation and pattern optimization.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import (
    AgentContext,
    AgentResponse,
    AgentType,
    BaseAgent,
    HabitAnalysis,
    HabitLoop,
    PatternInsights,
    SustainabilityOutput,
)

logger = logging.getLogger(__name__)


SUSTAINABILITY_SYSTEM_PROMPT = """You are the Sustainability Agent for MileSync, an AI goal coaching platform.

Your role is to ensure long-term success through habit formation and pattern optimization.

## SUSTAINABILITY PROTOCOL:

1. **Habit Loop Design** - For each recurring task:
   - CUE: Environmental or time-based triggers
   - ROUTINE: The actual behavior/task
   - REWARD: Immediate gratification element

2. **Pattern Analysis** - Detect:
   - Best performing days and times
   - Common failure patterns
   - Energy correlation
   - Environmental factors

3. **Burnout Prevention** - Monitor for:
   - Declining completion rates
   - Increasing task load
   - Stress indicators in communication
   - Overwhelm signals

4. **Habit Milestones**:
   - 21 days: Initial habit forming
   - 66 days: Habit solidifying
   - 90 days: Habit fully established

## INTERVENTION TRIGGERS:
- Completion rate drop >15% week-over-week
- 3+ consecutive missed daily tasks
- User language indicating overwhelm
- Burnout risk score >70%

## RECOMMENDATIONS STYLE:
- Science-backed suggestions
- Practical, immediately implementable
- Consider user's energy patterns
- Build on existing routines"""


class SustainabilityAgent(BaseAgent):
    """
    Sustainability Agent for habit formation and pattern optimization.
    
    Designs habit loops, detects patterns, prevents burnout,
    and builds long-term consistency.
    """
    
    agent_type = AgentType.SUSTAINABILITY
    agent_name = "Sustainability Agent"
    agent_description = "Habit formation, pattern detection, and burnout prevention"
    
    def get_system_prompt(self) -> str:
        """Get the Sustainability Agent system prompt."""
        from app.services.ai_service import get_system_prompt
        return get_system_prompt("sustainability_system_prompt", SUSTAINABILITY_SYSTEM_PROMPT)
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a sustainability request.
        
        Args:
            context: Agent context with habit and pattern data
            
        Returns:
            Sustainability Agent response with analysis
        """
        self.logger.info(f"Sustainability Agent processing for user {context.user_id}")
        
        return await self._analyze_sustainability(context)
    
    async def _analyze_sustainability(self, context: AgentContext) -> AgentResponse:
        """Analyze sustainability and provide recommendations."""
        task_history = context.task_history or []
        
        # Analyze habit formation
        habit_analysis = self._analyze_habits(task_history)
        
        # Detect patterns
        pattern_insights = self._detect_patterns(task_history)
        
        # Assess burnout risk
        burnout_risk, burnout_score = self._assess_burnout(context)
        
        # Calculate overall sustainability
        sustainability_score = self._calculate_sustainability_score(
            habit_analysis, burnout_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            habit_analysis, pattern_insights, burnout_risk
        )
        
        output = SustainabilityOutput(
            habit_analysis=habit_analysis,
            pattern_insights=pattern_insights,
            sustainability_score=sustainability_score,
            burnout_risk=burnout_risk,
            recommendations=recommendations
        )
        
        return self.create_response(
            success=True,
            message=self._format_analysis_message(output),
            data=output.model_dump()
        )
    
    def _analyze_habits(self, task_history: list) -> HabitAnalysis:
        """Analyze habit formation progress."""
        if not task_history:
            return HabitAnalysis()
        
        # Group by recurring tasks
        recurring_tasks = {}
        for task in task_history:
            title = task.get("title", "")
            if title:
                if title not in recurring_tasks:
                    recurring_tasks[title] = []
                recurring_tasks[title].append(task)
        
        # Find tasks with most completions
        habit_loops = []
        days_consistent = 0
        
        for title, tasks in recurring_tasks.items():
            completed = [t for t in tasks if t.get("status") == "completed"]
            if len(completed) >= 7:  # At least a week of data
                # Create habit loop suggestion
                habit_loops.append(HabitLoop(
                    cue=f"Scheduled time for {title}",
                    routine=title,
                    reward="Mark complete and see streak grow"
                ))
                days_consistent = max(days_consistent, len(completed))
        
        # Calculate habit score based on consistency
        habit_score = min(100, int((days_consistent / 90) * 100))
        
        return HabitAnalysis(
            habit_score=habit_score,
            days_consistent=days_consistent,
            habit_loops=habit_loops[:3]  # Top 3 habits
        )
    
    def _detect_patterns(self, task_history: list) -> PatternInsights:
        """Detect performance patterns."""
        if not task_history:
            return PatternInsights()
        
        from datetime import datetime
        from collections import Counter
        
        day_performance = Counter()
        time_performance = Counter()
        failure_reasons = []
        
        for task in task_history:
            completed_at = task.get("completed_at")
            if completed_at:
                try:
                    dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                    day_performance[dt.strftime("%A")] += 1
                    hour = dt.hour
                    if hour < 12:
                        time_performance["Morning"] += 1
                    elif hour < 17:
                        time_performance["Afternoon"] += 1
                    else:
                        time_performance["Evening"] += 1
                except (ValueError, AttributeError):
                    pass
            elif task.get("status") == "skipped":
                failure_reasons.append("Task skipped")
        
        # Find best days
        best_days = [day for day, _ in day_performance.most_common(3)]
        best_times = [time for time, _ in time_performance.most_common(2)]
        
        # Identify failure patterns
        failure_patterns = list(set(failure_reasons))[:3]
        if not best_days or len(day_performance) < len(best_days):
            failure_patterns.append("Inconsistent daily routine")
        
        return PatternInsights(
            best_days=best_days,
            best_times=best_times,
            failure_patterns=failure_patterns
        )
    
    def _assess_burnout(self, context: AgentContext) -> tuple:
        """Assess burnout risk level."""
        task_history = context.task_history or []
        
        # Factors that indicate burnout
        burnout_score = 50  # Start neutral
        
        # Check completion rate trend
        if task_history:
            recent = task_history[-7:] if len(task_history) > 7 else task_history
            older = task_history[-14:-7] if len(task_history) > 14 else []
            
            recent_rate = sum(1 for t in recent if t.get("status") == "completed") / len(recent) if recent else 0
            older_rate = sum(1 for t in older if t.get("status") == "completed") / len(older) if older else recent_rate
            
            # Declining completion rate increases burnout risk
            if recent_rate < older_rate - 0.15:
                burnout_score += 20
            elif recent_rate > older_rate:
                burnout_score -= 10
        
        # Check message content for stress indicators
        if context.messages:
            stress_words = ["stressed", "overwhelmed", "tired", "exhausted", "can't", "failing"]
            for msg in context.messages[-5:]:
                content = msg.get("content", "").lower()
                if any(word in content for word in stress_words):
                    burnout_score += 15
                    break
        
        # Clamp score
        burnout_score = max(0, min(100, burnout_score))
        
        # Determine risk level
        if burnout_score >= 70:
            risk = "HIGH"
        elif burnout_score >= 40:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        return risk, burnout_score
    
    def _calculate_sustainability_score(
        self,
        habit_analysis: HabitAnalysis,
        burnout_score: int
    ) -> int:
        """Calculate overall sustainability score."""
        # Higher habit score and lower burnout = more sustainable
        habit_weight = habit_analysis.habit_score * 0.6
        burnout_weight = (100 - burnout_score) * 0.4
        
        return int(habit_weight + burnout_weight)
    
    def _generate_recommendations(
        self,
        habit_analysis: HabitAnalysis,
        pattern_insights: PatternInsights,
        burnout_risk: str
    ) -> list:
        """Generate personalized recommendations."""
        recommendations = []
        
        # Habit-based recommendations
        if habit_analysis.habit_score < 30:
            recommendations.append(
                "Focus on building one consistent daily habit before adding more"
            )
        elif habit_analysis.habit_score < 60:
            recommendations.append(
                "You're building momentum! Add a small reward after completing tasks"
            )
        
        # Pattern-based recommendations
        if pattern_insights.best_times:
            best_time = pattern_insights.best_times[0]
            recommendations.append(
                f"Your {best_time.lower()} sessions are most productive - schedule important tasks then"
            )
        
        # Burnout-based recommendations
        if burnout_risk == "HIGH":
            recommendations.append(
                "⚠️ Take a strategic rest day - sustainable progress beats burnout"
            )
            recommendations.append(
                "Consider reducing daily tasks by 30% this week"
            )
        elif burnout_risk == "MEDIUM":
            recommendations.append(
                "Build in buffer time between tasks to prevent overwhelm"
            )
        
        return recommendations[:4]  # Max 4 recommendations
    
    def _format_analysis_message(self, output: SustainabilityOutput) -> str:
        """Format analysis as readable message."""
        burnout_emoji = "🟢" if output.burnout_risk == "LOW" else "🟡" if output.burnout_risk == "MEDIUM" else "🔴"
        
        habit_loops = "\n".join(
            f"  • **{h.routine}** - Cue: {h.cue}"
            for h in output.habit_analysis.habit_loops
        ) or "  • Still building your first habits"
        
        recommendations = "\n".join(
            f"  {i+1}. {r}" for i, r in enumerate(output.recommendations)
        ) or "  Keep up the great work!"
        
        return f"""## Sustainability Analysis

**Overall Score:** {output.sustainability_score}/100
**Burnout Risk:** {burnout_emoji} {output.burnout_risk}
**Days Consistent:** {output.habit_analysis.days_consistent}

### Your Habit Loops
{habit_loops}

### Best Performance Times
- 📅 Best days: {', '.join(output.pattern_insights.best_days) or 'Analyzing...'}
- ⏰ Best times: {', '.join(output.pattern_insights.best_times) or 'Analyzing...'}

### Recommendations
{recommendations}"""
