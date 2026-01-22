"""
Planning Agent for MileSync.

Transforms goals into SMART objectives with detailed execution plans.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.agents.base_agent import (
    AgentContext,
    AgentResponse,
    AgentType,
    BaseAgent,
    MilestoneOutput,
    PlanningOutput,
    SMARTGoal,
    TaskFrequency,
    TaskSchedule,
    TaskScheduleItem,
)

logger = logging.getLogger(__name__)


PLANNING_SYSTEM_PROMPT = """You are the Planning Agent for MileSync, an AI goal coaching platform.

Your role is to transform user goals into actionable, measurable plans with precise task breakdowns.

## PLANNING PROTOCOL:

1. **SMART Conversion** - Refine the goal to be:
   - Specific: Clear, unambiguous goal statement
   - Measurable: Quantifiable success metrics
   - Achievable: Realistic given constraints
   - Relevant: Aligned with user's values and priorities
   - Time-bound: Clear deadline and milestones

2. **Work Breakdown Structure (WBS)**
   - Break goal into 3-5 major milestones
   - Each milestone has clear deliverables
   - Milestones are sequenced logically

3. **Task Generation**
   - DAILY tasks: Max 3 items, <30 min each (micro-habits, quick wins)
   - WEEKLY tasks: Max 5 items, clear deliverables (major work blocks)
   - MONTHLY tasks: Major milestones, measurable outcomes

4. **Time Allocation**
   - Estimate realistic time for each task
   - Add 20% buffer for unexpected delays
   - Consider user's available time constraints

5. **Dependency Mapping**
   - Identify which tasks depend on others
   - Create logical sequencing
   - Flag critical path items

## OUTPUT FORMAT:
Always provide structured plans that are:
- Immediately actionable
- Not overwhelming (progressive difficulty)
- Balanced between challenge and achievability
- Front-loaded with quick wins for momentum"""


class PlanningAgent(BaseAgent):
    """
    Planning Agent for SMART goal conversion and task breakdown.
    
    Creates hierarchical task breakdowns, generates schedules,
    and builds dependency chains.
    """
    
    agent_type = AgentType.PLANNING
    agent_name = "Planning Agent"
    agent_description = "SMART goal conversion, task breakdown, and schedule generation"
    
    def get_system_prompt(self) -> str:
        """Get the Planning Agent system prompt."""
        from app.services.ai_service import get_system_prompt
        return get_system_prompt("planning_system_prompt", PLANNING_SYSTEM_PROMPT)
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a planning request.
        
        Args:
            context: Agent context with goal information
            
        Returns:
            Planning Agent response with SMART goal and task breakdown
        """
        self.logger.info(f"Planning Agent processing for user {context.user_id}")
        
        # Get foundation data if available
        foundation_data = None
        if context.additional_context:
            foundation_data = context.additional_context.get("previous_output")
        
        # Generate plan
        return await self._generate_plan(context, foundation_data)
    
    async def _generate_plan(
        self,
        context: AgentContext,
        foundation_data: Optional[dict] = None
    ) -> AgentResponse:
        """
        Generate a comprehensive plan from goal information.
        """
        # Build planning prompt
        goal_info = self._extract_goal_info(context, foundation_data)
        
        planning_prompt = f"""Create a detailed action plan for this goal:

{goal_info}

Generate a structured plan in JSON format:
{{
    "smart_goal": {{
        "specific": "What exactly will be accomplished",
        "measurable": "How progress will be measured",
        "achievable": "Why this is realistic",
        "relevant": "Why this matters to the user",
        "time_bound": "When this will be completed"
    }},
    "milestones": [
        {{
            "id": "M1",
            "title": "Milestone title",
            "description": "What this milestone achieves",
            "deadline": "YYYY-MM-DD",
            "success_criteria": ["criterion1", "criterion2"],
            "tasks": [
                {{
                    "title": "Task title",
                    "description": "Brief description",
                    "frequency": "daily|weekly|monthly|one_time",
                    "estimated_minutes": 30,
                    "priority": "high|medium|low"
                }}
            ]
        }}
    ],
    "task_schedule": {{
        "daily": [
            {{"title": "...", "frequency": "daily", "estimated_minutes": 15, "priority": "high"}}
        ],
        "weekly": [
            {{"title": "...", "frequency": "weekly", "estimated_minutes": 60, "priority": "medium"}}
        ],
        "monthly": [
            {{"title": "...", "frequency": "monthly", "estimated_minutes": 120, "priority": "high"}}
        ]
    }},
    "dependencies": [
        {{"task": "Task A", "depends_on": "Task B"}}
    ],
    "total_estimated_hours": 50,
    "critical_path": ["M1", "M2", "M3"]
}}

Rules:
- Daily tasks: Max 3, under 30 min each
- Weekly tasks: Max 5, focused on major work
- Monthly tasks: Major checkpoints
- Include realistic time estimates
- Sequence milestones logically
- Front-load with quick wins

Respond with ONLY valid JSON."""

        try:
            from app.services.ai_service import get_openai_client
            
            client = get_openai_client()
            if not client:
                raise ValueError("OpenAI client not configured")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.4
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                # Clean up response
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                plan_data = json.loads(response_text.strip())
                
                # Build output
                output = self._build_planning_output(plan_data)
                
                return self.create_response(
                    success=True,
                    message=self._format_plan_message(output),
                    data=output.model_dump(),
                    next_agent=AgentType.EXECUTION  # Chain to Execution Agent
                )
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parse error: {e}\nResponse: {response_text[:500]}")
                return self.create_response(
                    success=False,
                    message="I had trouble creating the plan structure. Let me try again."
                )
                
        except Exception as e:
            self.logger.error(f"Plan generation error: {e}")
            return self.create_response(
                success=False,
                message=f"Error generating plan: {str(e)}"
            )
    
    def _extract_goal_info(
        self,
        context: AgentContext,
        foundation_data: Optional[dict]
    ) -> str:
        """Extract goal information from context."""
        parts = []
        
        if foundation_data:
            parts.append(f"Goal Summary: {foundation_data.get('goal_summary', 'Not specified')}")
            parts.append(f"Goal Type: {foundation_data.get('goal_type', 'long_term')}")
            parts.append(f"Motivation Score: {foundation_data.get('motivation_score', 'N/A')}/10")
            parts.append(f"Feasibility Score: {foundation_data.get('feasibility_score', 'N/A')}/10")
            
            obstacles = foundation_data.get('identified_obstacles', [])
            if obstacles:
                parts.append(f"Obstacles to Address: {', '.join(obstacles)}")
            
            constraints = foundation_data.get('user_constraints', {})
            if constraints:
                parts.append(f"Constraints: {json.dumps(constraints)}")
        
        if context.current_goal:
            goal = context.current_goal
            parts.append(f"Existing Goal: {goal.get('title', 'Untitled')}")
            parts.append(f"Description: {goal.get('description', 'No description')}")
            parts.append(f"Target Date: {goal.get('target_date', 'Not set')}")
        
        # Add message context
        if context.messages:
            recent_messages = context.messages[-5:]
            conversation = "\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                for m in recent_messages
            )
            parts.append(f"\nRecent Conversation:\n{conversation}")
        
        return "\n".join(parts)
    
    def _build_planning_output(self, plan_data: dict) -> PlanningOutput:
        """Build a PlanningOutput from parsed JSON."""
        # Build SMART goal
        smart_data = plan_data.get("smart_goal", {})
        smart_goal = SMARTGoal(
            specific=smart_data.get("specific", ""),
            measurable=smart_data.get("measurable", ""),
            achievable=smart_data.get("achievable", ""),
            relevant=smart_data.get("relevant", ""),
            time_bound=smart_data.get("time_bound", "")
        )
        
        # Build milestones
        milestones = []
        for m in plan_data.get("milestones", []):
            tasks = []
            for t in m.get("tasks", []):
                try:
                    freq = TaskFrequency(t.get("frequency", "one_time"))
                except ValueError:
                    freq = TaskFrequency.ONE_TIME
                
                tasks.append(TaskScheduleItem(
                    title=t.get("title", ""),
                    description=t.get("description"),
                    frequency=freq,
                    estimated_minutes=t.get("estimated_minutes", 30),
                    priority=t.get("priority", "medium")
                ))
            
            milestones.append(MilestoneOutput(
                id=m.get("id", ""),
                title=m.get("title", ""),
                description=m.get("description"),
                deadline=m.get("deadline"),
                success_criteria=m.get("success_criteria", []),
                tasks=tasks
            ))
        
        # Build task schedule
        schedule_data = plan_data.get("task_schedule", {})
        
        def parse_tasks(task_list):
            result = []
            for t in task_list:
                try:
                    freq = TaskFrequency(t.get("frequency", "one_time"))
                except ValueError:
                    freq = TaskFrequency.ONE_TIME
                result.append(TaskScheduleItem(
                    title=t.get("title", ""),
                    description=t.get("description"),
                    frequency=freq,
                    estimated_minutes=t.get("estimated_minutes", 30),
                    priority=t.get("priority", "medium")
                ))
            return result
        
        task_schedule = TaskSchedule(
            daily=parse_tasks(schedule_data.get("daily", [])),
            weekly=parse_tasks(schedule_data.get("weekly", [])),
            monthly=parse_tasks(schedule_data.get("monthly", []))
        )
        
        return PlanningOutput(
            smart_goal=smart_goal,
            milestones=milestones,
            task_schedule=task_schedule,
            dependencies=plan_data.get("dependencies", []),
            total_estimated_hours=plan_data.get("total_estimated_hours", 0),
            critical_path=plan_data.get("critical_path", [])
        )
    
    def _format_plan_message(self, output: PlanningOutput) -> str:
        """Format the plan as a readable message."""
        milestone_list = "\n".join(
            f"  {i+1}. **{m.title}** - {m.deadline or 'No deadline'}"
            for i, m in enumerate(output.milestones)
        )
        
        daily_tasks = "\n".join(
            f"  - {t.title} ({t.estimated_minutes}min)"
            for t in output.task_schedule.daily[:3]
        ) or "  - None scheduled"
        
        return f"""## Your Action Plan

### SMART Goal
- **Specific:** {output.smart_goal.specific}
- **Measurable:** {output.smart_goal.measurable}
- **Time-bound:** {output.smart_goal.time_bound}

### Milestones
{milestone_list}

### Daily Habits
{daily_tasks}

**Estimated Total Time:** {output.total_estimated_hours} hours

Ready to start tracking your progress!"""
