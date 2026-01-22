"""
Psychological Agent for MileSync.

Handles motivation, mindset coaching, and behavioral science application.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import (
    AgentContext,
    AgentResponse,
    AgentType,
    BaseAgent,
    EmotionalAssessment,
    Intervention,
    PsychologicalOutput,
)

logger = logging.getLogger(__name__)


PSYCHOLOGICAL_SYSTEM_PROMPT = """You are the Psychological Agent for MileSync, an AI goal coaching platform.

Your role is to support users' mental and emotional wellbeing throughout their goal journey.

## PSYCHOLOGICAL PROTOCOL:

1. **Monitor Emotional Tone** - Detect mood from communication
2. **Assess Motivation** - Track motivation fluctuations
3. **Identify Patterns** - Spot cognitive distortions
4. **Provide Reframing** - Offer perspective shifts
5. **Offer Interventions** - Evidence-based techniques
6. **Celebrate Progress** - Build self-efficacy

## INTERVENTION TOOLKIT:

**Motivational Boosters:**
- Progress visualization
- Past success reminders
- Future self visualization
- Small wins celebration

**Reframing Techniques:**
- Cognitive restructuring
- Perspective shifts
- All-or-nothing thinking correction
- Catastrophizing reduction

**Anxiety Management:**
- Deep breathing exercises
- Worry time scheduling
- Progressive relaxation
- Grounding techniques

**Procrastination Busters:**
- 2-minute rule
- Temptation bundling
- Implementation intentions
- Environment design

**Self-Compassion:**
- Normalize setbacks
- Growth mindset reinforcement
- Self-kindness prompts
- Common humanity reminders

## COMMUNICATION STYLE:
- Warm and empathetic
- Non-judgmental
- Solution-focused
- Evidence-based
- Empowering, not dependency-creating

## WHEN TO ESCALATE:
If user shows signs of clinical depression, anxiety disorders, or crisis,
gently recommend professional support while being supportive."""


class PsychologicalAgent(BaseAgent):
    """
    Psychological Agent for motivation and mindset coaching.
    
    Provides motivation assessment, mindset coaching, stress management,
    and cognitive behavioral techniques.
    """
    
    agent_type = AgentType.PSYCHOLOGICAL
    agent_name = "Psychological Agent"
    agent_description = "Motivation, mindset coaching, and behavioral science support"
    
    def get_system_prompt(self) -> str:
        """Get the Psychological Agent system prompt."""
        from app.services.ai_service import get_system_prompt
        return get_system_prompt("psychological_system_prompt", PSYCHOLOGICAL_SYSTEM_PROMPT)
    
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a psychological support request.
        
        Args:
            context: Agent context with emotional cues
            
        Returns:
            Psychological Agent response with support
        """
        self.logger.info(f"Psychological Agent processing for user {context.user_id}")
        
        # Assess emotional state
        emotional_assessment = self._assess_emotional_state(context)
        
        # Determine if intervention needed
        needs_intervention = (
            emotional_assessment.motivation_level < 4 or
            emotional_assessment.stress_level > 7 or
            emotional_assessment.confidence_level < 4 or
            len(emotional_assessment.detected_patterns) > 0
        )
        
        if needs_intervention:
            return await self._provide_intervention(context, emotional_assessment)
        else:
            return await self._provide_encouragement(context, emotional_assessment)
    
    def _assess_emotional_state(self, context: AgentContext) -> EmotionalAssessment:
        """Assess user's emotional state from context."""
        motivation_level = 5
        stress_level = 5
        confidence_level = 5
        detected_patterns = []
        
        # Analyze messages for emotional cues
        if context.messages:
            all_text = " ".join(
                msg.get("content", "").lower()
                for msg in context.messages
                if msg.get("role") == "user"
            )
            
            # Motivation indicators
            low_motivation = ["can't", "won't", "tired", "exhausted", "giving up", "quit"]
            high_motivation = ["excited", "eager", "ready", "motivated", "pumped"]
            
            for word in low_motivation:
                if word in all_text:
                    motivation_level -= 1
            for word in high_motivation:
                if word in all_text:
                    motivation_level += 1
            
            # Stress indicators
            stress_words = ["stressed", "anxious", "overwhelmed", "panic", "worried"]
            for word in stress_words:
                if word in all_text:
                    stress_level += 1
            
            # Confidence indicators
            low_confidence = ["stupid", "can't do", "not good enough", "failure", "imposter"]
            high_confidence = ["confident", "capable", "proud", "achieved", "succeeded"]
            
            for word in low_confidence:
                if word in all_text:
                    confidence_level -= 1
            for word in high_confidence:
                if word in all_text:
                    confidence_level += 1
            
            # Detect cognitive patterns
            if "always" in all_text or "never" in all_text:
                detected_patterns.append("All-or-nothing thinking")
            if "should" in all_text or "must" in all_text:
                detected_patterns.append("Should statements")
            if "worst" in all_text or "terrible" in all_text:
                detected_patterns.append("Catastrophizing")
            if "my fault" in all_text or "blame myself" in all_text:
                detected_patterns.append("Personalization")
        
        # Clamp values
        motivation_level = max(1, min(10, motivation_level))
        stress_level = max(1, min(10, stress_level))
        confidence_level = max(1, min(10, confidence_level))
        
        return EmotionalAssessment(
            motivation_level=motivation_level,
            stress_level=stress_level,
            confidence_level=confidence_level,
            detected_patterns=detected_patterns[:3]
        )
    
    async def _provide_intervention(
        self,
        context: AgentContext,
        assessment: EmotionalAssessment
    ) -> AgentResponse:
        """Provide psychological intervention based on assessment."""
        # Determine intervention type
        if assessment.stress_level > 7:
            intervention = self._create_stress_intervention()
        elif assessment.motivation_level < 4:
            intervention = self._create_motivation_intervention()
        elif assessment.confidence_level < 4:
            intervention = self._create_confidence_intervention()
        elif assessment.detected_patterns:
            intervention = self._create_reframing_intervention(
                assessment.detected_patterns[0]
            )
        else:
            intervention = self._create_general_support()
        
        # Generate personalized affirmations
        affirmations = self._generate_affirmations(assessment)
        
        # Create progress celebration if applicable
        progress_celebration = ""
        if context.task_history:
            completed = sum(
                1 for t in context.task_history 
                if t.get("status") == "completed"
            )
            if completed > 0:
                progress_celebration = f"✨ Remember: You've already completed {completed} tasks. That's real progress!"
        
        output = PsychologicalOutput(
            emotional_assessment=assessment,
            intervention=intervention,
            affirmations=affirmations,
            progress_celebration=progress_celebration
        )
        
        return self.create_response(
            success=True,
            message=self._format_support_message(output),
            data=output.model_dump()
        )
    
    async def _provide_encouragement(
        self,
        context: AgentContext,
        assessment: EmotionalAssessment
    ) -> AgentResponse:
        """Provide general encouragement using the System Prompt."""
        
        # Build prompt for specific encouragement
        prompt = f"""Analyze the user's current state:
        Motivation: {assessment.motivation_level}/10
        Stress: {assessment.stress_level}/10
        Confidence: {assessment.confidence_level}/10
        
        Provide a warm, encouraging response that acknowledges this state.
        Focus on their progress and potential."""
        
        try:
            # Use the LLM with the System Prompt to generate the response
            message = await self.generate_response(context, prompt)
        except Exception as e:
            self.logger.error(f"Error generating encouragement: {e}")
            message = "You're doing great! Even small steps count. Keep going!"
            
        output = PsychologicalOutput(
            emotional_assessment=assessment,
            progress_celebration="Keep moving forward!"
        )
        
        return self.create_response(
            success=True,
            message=message,
            data=output.model_dump()
        )
    
    def _create_stress_intervention(self) -> Intervention:
        """Create stress management intervention."""
        return Intervention(
            type="STRESS_MANAGEMENT",
            technique="4-7-8 Breathing",
            message="I notice you might be feeling stressed. Let's take a moment to breathe.",
            exercises=[
                "Breathe in through your nose for 4 counts",
                "Hold your breath for 7 counts",
                "Exhale slowly through your mouth for 8 counts",
                "Repeat 3-4 times"
            ]
        )
    
    def _create_motivation_intervention(self) -> Intervention:
        """Create motivation boosting intervention."""
        return Intervention(
            type="MOTIVATION_BOOST",
            technique="2-Minute Rule",
            message="Feeling unmotivated? Let's use a proven technique to get started.",
            exercises=[
                "Pick the smallest possible version of your task",
                "Commit to just 2 minutes of work",
                "Often, starting is the hardest part",
                "Once you start, you'll likely want to continue"
            ]
        )
    
    def _create_confidence_intervention(self) -> Intervention:
        """Create confidence building intervention."""
        return Intervention(
            type="CONFIDENCE_BUILDING",
            technique="Past Wins Reflection",
            message="Let's remind ourselves of what you've already accomplished.",
            exercises=[
                "Think of 3 challenges you've overcome before",
                "Remember how you felt after succeeding",
                "Recognize that those same skills apply here",
                "You've done hard things before - you can do this too"
            ]
        )
    
    def _create_reframing_intervention(self, pattern: str) -> Intervention:
        """Create cognitive reframing intervention."""
        reframes = {
            "All-or-nothing thinking": (
                "Replace 'always/never' with 'sometimes/often'. "
                "Progress isn't all-or-nothing."
            ),
            "Should statements": (
                "Replace 'should' with 'could' or 'want to'. "
                "You have choices, not obligations."
            ),
            "Catastrophizing": (
                "Ask: What's the realistic worst case? "
                "Usually it's more manageable than we fear."
            ),
            "Personalization": (
                "Remember: Many factors affect outcomes. "
                "Not everything is within your control."
            )
        }
        
        return Intervention(
            type="COGNITIVE_REFRAMING",
            technique="Thought Challenging",
            message=f"I noticed a pattern: {pattern}. Let's reframe this.",
            exercises=[
                reframes.get(pattern, "Consider an alternative perspective"),
                "Write down the thought",
                "Ask: Is this thought helpful?",
                "Create a more balanced alternative"
            ]
        )
    
    def _create_general_support(self) -> Intervention:
        """Create general supportive intervention."""
        return Intervention(
            type="GENERAL_SUPPORT",
            technique="Self-Compassion",
            message="Remember to be kind to yourself on this journey.",
            exercises=[
                "Acknowledge that this is challenging",
                "Remind yourself that struggle is part of growth",
                "Treat yourself as you would a good friend",
                "Take one small step forward today"
            ]
        )
    
    def _generate_affirmations(self, assessment: EmotionalAssessment) -> list:
        """Generate personalized affirmations."""
        affirmations = []
        
        if assessment.motivation_level < 5:
            affirmations.append("Your small efforts today create big results tomorrow.")
        if assessment.stress_level > 5:
            affirmations.append("You are capable of handling whatever comes your way.")
        if assessment.confidence_level < 5:
            affirmations.append("You have already proven you can do hard things.")
        
        # Always include at least one
        if not affirmations:
            affirmations.append("You are making progress, even when it doesn't feel like it.")
        
        return affirmations
    
    def _format_support_message(self, output: PsychologicalOutput) -> str:
        """Format support message."""
        assessment = output.emotional_assessment
        intervention = output.intervention
        
        exercises = "\n".join(
            f"  {i+1}. {e}" for i, e in enumerate(intervention.exercises)
        ) if intervention else ""
        
        affirmations = "\n".join(
            f"  💫 {a}" for a in output.affirmations
        )
        
        return f"""## Mindset Check-In

**How You're Doing:**
- 🎯 Motivation: {assessment.motivation_level}/10
- 😌 Stress: {assessment.stress_level}/10  
- 💪 Confidence: {assessment.confidence_level}/10

### {intervention.technique if intervention else 'Support'}
{intervention.message if intervention else 'You are doing well!'}

**Try This:**
{exercises}

### Affirmations
{affirmations}

{output.progress_celebration}"""
    
    def _format_encouragement_message(self, output: PsychologicalOutput) -> str:
        """Format encouragement message."""
        affirmations = "\n".join(f"  💫 {a}" for a in output.affirmations)
        
        return f"""## You're Doing Great! 🌟

Your emotional state looks balanced and positive.

### Today's Affirmations
{affirmations}

{output.progress_celebration}

Keep going - you've got this!"""
