"""
Foundation Agent for MileSync.

Handles initial goal intake, user profiling, and baseline establishment.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import (
    AgentContext,
    AgentResponse,
    AgentType,
    BaseAgent,
    FoundationOutput,
    GoalType,
)

logger = logging.getLogger(__name__)


FOUNDATION_SYSTEM_PROMPT = """You are the Foundation Agent for MileSync, an AI goal coaching platform.

Your role is to deeply understand the user's goals and create a comprehensive foundation for achievement.

## INTAKE PROTOCOL:

1. **Ask Clarifying Questions** - Understand the FULL context of the goal
2. **Identify the WHY** - Uncover intrinsic motivation behind the goal
3. **Assess Current State** - Understand where the user is now vs where they want to be
4. **Evaluate Resources** - Time, energy, money, and support available
5. **Identify Obstacles** - Proactively spot potential challenges
6. **Classify Goal Type**:
   - SHORT_TERM: <3 months (quick wins, skill building)
   - LONG_TERM: 3-12 months (career changes, major projects)
   - RESOLUTION: Year-long commitments (lifestyle changes, transformations)

## CONVERSATION STYLE:
- Be warm, curious, and encouraging
- Ask one or two questions at a time (don't overwhelm)
- Reflect back what you hear to show understanding
- Celebrate their ambition while being realistic

## WHEN READY TO ASSESS:
After enough conversation, provide a structured assessment. Include:
- Goal summary in clear, concise language
- Goal type classification with reasoning
- Scores (1-10) for motivation, feasibility, and clarity
- Identified obstacles and how to address them
- Success criteria that are observable and measurable
- Any recommended adjustments to make the goal more achievable

Remember: Your job is to set users up for success by creating a solid foundation."""


class FoundationAgent(BaseAgent):
    """
    Foundation Agent for goal intake and user profiling.
    
    Conducts comprehensive goal intake interviews, builds user profiles,
    assesses feasibility, and identifies potential obstacles.
    """
    
    agent_type = AgentType.FOUNDATION
    agent_name = "Foundation Agent"
    agent_description = "Initial goal intake, user profiling, and baseline establishment"
    
    def get_system_prompt(self) -> str:
        """Get the Foundation Agent system prompt."""
        from app.services.ai_service import get_system_prompt
        return get_system_prompt("foundation_system_prompt", FOUNDATION_SYSTEM_PROMPT)
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a foundation request.
        
        Args:
            context: Agent context with user messages
            
        Returns:
            Foundation Agent response
        """
        self.logger.info(f"Foundation Agent processing for user {context.user_id}")
        
        # Check if we have enough information for assessment
        if self._should_generate_assessment(context):
            return await self._generate_assessment(context)
        else:
            return await self._continue_intake(context)
    
    def _should_generate_assessment(self, context: AgentContext) -> bool:
        """
        Determine if we have enough information for assessment.
        
        Criteria:
        - At least 4 message exchanges
        - User has provided goal details, timeline, and motivation
        - Additional context indicates readiness
        """
        # Check message count
        if len(context.messages) < 4:
            return False
        
        # Check for explicit request
        if context.additional_context:
            if context.additional_context.get("generate_assessment"):
                return True
        
        # Analyze conversation for completeness
        conversation_text = " ".join(
            msg.get("content", "") for msg in context.messages
            if msg.get("role") == "user"
        ).lower()
        
        # Look for key information signals
        has_timeline = any(word in conversation_text for word in [
            "month", "week", "year", "by", "until", "before", "deadline"
        ])
        has_motivation = any(word in conversation_text for word in [
            "because", "want to", "need to", "hoping", "goal is", "dream"
        ])
        has_specifics = len(conversation_text) > 200  # Substantial conversation
        
        return has_timeline and has_motivation and has_specifics
    
    async def _continue_intake(self, context: AgentContext) -> AgentResponse:
        """
        Continue the intake conversation.
        
        Generate clarifying questions based on what we know.
        """
        # Get the last user message
        last_message = ""
        for msg in reversed(context.messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
        
        # Generate response
        try:
            response_text = await self.generate_response(context, last_message)
            
            return self.create_response(
                success=True,
                message=response_text,
                data={"stage": "intake", "ready_for_assessment": False},
                requires_user_input=True
            )
        except Exception as e:
            self.logger.error(f"Error in intake: {e}")
            return self.create_response(
                success=False,
                message=f"I encountered an issue. Let's try again. What goal would you like to work on?"
            )
    
    async def _generate_assessment(self, context: AgentContext) -> AgentResponse:
        """
        Generate a structured assessment from the conversation.
        """
        # Create assessment prompt
        conversation_summary = self._summarize_conversation(context.messages)
        
        assessment_prompt = f"""Based on this conversation about the user's goal:

{conversation_summary}

Generate a structured assessment in JSON format with these fields:
{{
    "goal_summary": "Clear, concise goal statement",
    "goal_type": "SHORT_TERM or LONG_TERM or RESOLUTION",
    "motivation_score": 1-10,
    "feasibility_score": 1-10,
    "clarity_score": 1-10,
    "identified_obstacles": ["obstacle1", "obstacle2"],
    "success_criteria": ["criterion1", "criterion2"],
    "baseline_metrics": {{"current_state": "...", "target_state": "..."}},
    "user_constraints": {{"time": "...", "resources": "..."}},
    "recommended_adjustments": ["adjustment1", "adjustment2"]
}}

Respond with ONLY the JSON, no other text."""

        try:
            from app.services.ai_service import get_openai_client
            
            client = get_openai_client()
            if not client:
                raise ValueError("OpenAI client not configured")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": assessment_prompt}
                ],
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                # Clean up response if needed
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                assessment_data = json.loads(response_text.strip())
                
                # Validate with Pydantic
                output = FoundationOutput(
                    goal_summary=assessment_data.get("goal_summary", ""),
                    goal_type=GoalType(assessment_data.get("goal_type", "long_term").lower()),
                    motivation_score=assessment_data.get("motivation_score", 5),
                    feasibility_score=assessment_data.get("feasibility_score", 5),
                    clarity_score=assessment_data.get("clarity_score", 5),
                    identified_obstacles=assessment_data.get("identified_obstacles", []),
                    success_criteria=assessment_data.get("success_criteria", []),
                    baseline_metrics=assessment_data.get("baseline_metrics", {}),
                    user_constraints=assessment_data.get("user_constraints", {}),
                    recommended_adjustments=assessment_data.get("recommended_adjustments", [])
                )
                
                return self.create_response(
                    success=True,
                    message=self._format_assessment_message(output),
                    data=output.model_dump(),
                    next_agent=AgentType.PLANNING  # Chain to Planning Agent
                )
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parse error: {e}")
                return self.create_response(
                    success=False,
                    message="I had trouble processing the assessment. Let me try again."
                )
                
        except Exception as e:
            self.logger.error(f"Assessment generation error: {e}")
            return self.create_response(
                success=False,
                message=f"Error generating assessment: {str(e)}"
            )
    
    def _summarize_conversation(self, messages: list) -> str:
        """Create a summary of the conversation."""
        summary_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:500]  # Limit length
            summary_parts.append(f"{role.upper()}: {content}")
        return "\n".join(summary_parts)
    
    def _format_assessment_message(self, output: FoundationOutput) -> str:
        """Format the assessment as a readable message."""
        return f"""## Goal Foundation Assessment

**Your Goal:** {output.goal_summary}

**Goal Type:** {output.goal_type.value.replace('_', ' ').title()}

### Scores
- 🎯 Motivation: {output.motivation_score}/10
- ✅ Feasibility: {output.feasibility_score}/10
- 💡 Clarity: {output.clarity_score}/10

### Potential Challenges
{chr(10).join(f'- {o}' for o in output.identified_obstacles) if output.identified_obstacles else '- None identified yet'}

### Success Looks Like
{chr(10).join(f'- {c}' for c in output.success_criteria) if output.success_criteria else '- To be defined'}

I'm now ready to help you create a detailed action plan!"""
