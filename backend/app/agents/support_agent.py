"""
Support Agent for MileSync.

Handles resource curation, tool recommendations, and external support coordination.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import (
    AgentContext,
    AgentResponse,
    AgentType,
    BaseAgent,
    Resource,
    SupportOutput,
)

logger = logging.getLogger(__name__)


SUPPORT_SYSTEM_PROMPT = """You are the Support Agent for MileSync, an AI goal coaching platform.

Your role is to provide comprehensive support resources and connections to help users succeed.

## SUPPORT PROTOCOL:

1. **Analyze Goal Requirements** - Understand what resources would help
2. **Identify Resource Gaps** - What knowledge/tools are missing
3. **Curate Relevant Materials** - Find the best-fit resources
4. **Match to Learning Style** - Consider how the user learns best
5. **Prioritize Accessibility** - Free/freemium first

## RESOURCE CATEGORIES:

1. **Educational Resources**
   - Online courses (Coursera, Udemy, YouTube)
   - Books and audiobooks
   - Tutorials and guides
   - Podcasts

2. **Productivity Tools**
   - Task management apps
   - Time tracking tools
   - Note-taking systems
   - Automation tools

3. **Community Support**
   - Online communities
   - Accountability groups
   - Forums and Discord servers
   - Local meetups

4. **Professional Help**
   - Coaches and mentors
   - Subject matter experts
   - Therapists (for wellness goals)
   - Trainers (for fitness goals)

## RECOMMENDATION CRITERIA:
- High relevance to specific goal
- Matches user's time availability
- Within budget constraints
- Appropriate skill level
- Good reviews/reputation

Always explain WHY each resource is recommended."""


class SupportAgent(BaseAgent):
    """
    Support Agent for resource curation and recommendations.
    
    Discovers resources, recommends tools, suggests communities,
    and routes to expert help when needed.
    """
    
    agent_type = AgentType.SUPPORT
    agent_name = "Support Agent"
    agent_description = "Resource curation, tool recommendations, and support connections"
    
    def get_system_prompt(self) -> str:
        """Get the Support Agent system prompt."""
        from app.services.ai_service import get_system_prompt
        return get_system_prompt("support_system_prompt", SUPPORT_SYSTEM_PROMPT)
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a support request.
        
        Args:
            context: Agent context with goal information
            
        Returns:
            Support Agent response with resources
        """
        self.logger.info(f"Support Agent processing for user {context.user_id}")
        
        return await self._generate_recommendations(context)
    
    async def _generate_recommendations(self, context: AgentContext) -> AgentResponse:
        """Generate resource recommendations based on goal."""
        # Get goal information
        goal_info = self._extract_goal_info(context)
        
        # Generate recommendations via LLM
        recommendation_prompt = f"""Based on this goal information, recommend helpful resources:

{goal_info}

Provide recommendations in JSON format:
{{
    "recommended_resources": [
        {{
            "type": "COURSE|BOOK|TOOL|COMMUNITY|EXPERT",
            "name": "Resource name",
            "url": "URL if available, or null",
            "relevance_score": 0.0-1.0,
            "time_commitment": "e.g., 2 hours/week",
            "cost": "Free|$XX|Subscription",
            "why": "Brief explanation of why this helps"
        }}
    ],
    "integration_suggestions": ["Tool integrations that could help"],
    "community_matches": ["Relevant communities to join"],
    "expert_recommendations": ["Types of experts that could help"]
}}

Rules:
- Recommend 3-5 resources total
- Prioritize free options
- Match to goal category
- Explain relevance

Respond with ONLY valid JSON."""

        try:
            from app.services.ai_service import get_openai_client
            
            client = get_openai_client()
            if not client:
                return self._generate_fallback_recommendations(context)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": recommendation_prompt}
                ],
                temperature=0.5
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                data = json.loads(response_text.strip())
                output = self._build_support_output(data)
                
                return self.create_response(
                    success=True,
                    message=self._format_recommendations_message(output),
                    data=output.model_dump()
                )
                
            except json.JSONDecodeError:
                return self._generate_fallback_recommendations(context)
                
        except Exception as e:
            self.logger.error(f"Support recommendation error: {e}")
            return self._generate_fallback_recommendations(context)
    
    def _extract_goal_info(self, context: AgentContext) -> str:
        """Extract goal information for recommendations."""
        parts = []
        
        if context.current_goal:
            goal = context.current_goal
            parts.append(f"Goal: {goal.get('title', 'Not specified')}")
            parts.append(f"Category: {goal.get('category', 'general')}")
            parts.append(f"Description: {goal.get('description', '')}")
        
        if context.messages:
            recent = context.messages[-3:]
            for msg in recent:
                if msg.get("role") == "user":
                    parts.append(f"User said: {msg.get('content', '')}")
        
        return "\n".join(parts) or "General goal support needed"
    
    def _build_support_output(self, data: dict) -> SupportOutput:
        """Build SupportOutput from parsed data."""
        resources = []
        for r in data.get("recommended_resources", []):
            resources.append(Resource(
                type=r.get("type", "TOOL"),
                name=r.get("name", ""),
                url=r.get("url"),
                relevance_score=float(r.get("relevance_score", 0.5)),
                time_commitment=r.get("time_commitment"),
                cost=r.get("cost", "Free")
            ))
        
        return SupportOutput(
            recommended_resources=resources,
            integration_suggestions=data.get("integration_suggestions", []),
            community_matches=data.get("community_matches", []),
            expert_recommendations=data.get("expert_recommendations", [])
        )
    
    def _generate_fallback_recommendations(self, context: AgentContext) -> AgentResponse:
        """Generate fallback recommendations without LLM."""
        # Generic helpful resources
        resources = [
            Resource(
                type="TOOL",
                name="Google Calendar",
                url="https://calendar.google.com",
                relevance_score=0.8,
                time_commitment="Setup: 30 min",
                cost="Free"
            ),
            Resource(
                type="COMMUNITY",
                name="Reddit Goal Setting",
                url="https://reddit.com/r/getdisciplined",
                relevance_score=0.7,
                time_commitment="As needed",
                cost="Free"
            )
        ]
        
        output = SupportOutput(
            recommended_resources=resources,
            integration_suggestions=["Sync with calendar for reminders"],
            community_matches=["Online accountability groups"],
            expert_recommendations=[]
        )
        
        return self.create_response(
            success=True,
            message=self._format_recommendations_message(output),
            data=output.model_dump()
        )
    
    def _format_recommendations_message(self, output: SupportOutput) -> str:
        """Format recommendations as readable message."""
        resources_list = "\n".join(
            f"  • **{r.name}** ({r.type}) - {r.cost}\n    {r.url or 'Search online'}"
            for r in output.recommended_resources
        ) or "  • No specific resources recommended yet"
        
        communities = ", ".join(output.community_matches) or "None suggested"
        
        return f"""## Recommended Resources

### Tools & Learning
{resources_list}

### Communities
{communities}

### Integration Ideas
{chr(10).join(f'  • {s}' for s in output.integration_suggestions) or '  • None yet'}

💡 These resources are curated based on your specific goal!"""
