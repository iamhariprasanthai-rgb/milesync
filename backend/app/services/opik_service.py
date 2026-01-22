"""Opik service for LLM observability, tracing, and evaluation.

This module provides comprehensive integration with Opik for:
- Tracing all AI interactions (chat responses, goal extraction)
- Evaluating AI coaching quality using LLM-as-judge metrics
- Tracking experiments for prompt optimization
- Monitoring goal generation quality with custom metrics
"""

import os
from typing import Any, Dict, List, Optional
from functools import wraps
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Track whether Opik is properly configured
_opik_configured = False
_opik_client = None


def configure_opik() -> bool:
    """
    Configure Opik with API credentials.
    
    Returns:
        True if Opik was configured successfully, False otherwise
    """
    global _opik_configured
    
    if not settings.OPIK_API_KEY:
        logger.warning("OPIK_API_KEY not configured - Opik tracing disabled")
        return False
    
    try:
        import opik
        
        # Set environment variables for Opik
        os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY
        os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT_NAME
        
        if settings.OPIK_WORKSPACE:
            os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
        
        # Configure Opik
        opik.configure(
            api_key=settings.OPIK_API_KEY,
            workspace=settings.OPIK_WORKSPACE if settings.OPIK_WORKSPACE else None,
        )
        
        _opik_configured = True
        logger.info(f"Opik configured successfully for project: {settings.OPIK_PROJECT_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Opik: {e}")
        return False


def is_opik_enabled() -> bool:
    """Check if Opik is enabled and configured."""
    return _opik_configured


def get_tracked_openai_client():
    """
    Get an OpenAI client wrapped with Opik tracing.
    
    Returns:
        Tracked OpenAI client if Opik is configured, regular client otherwise
    """
    from openai import OpenAI
    
    if not settings.OPENAI_API_KEY:
        return None
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    if not _opik_configured:
        return client
    
    try:
        from opik.integrations.openai import track_openai
        return track_openai(client)
    except ImportError:
        logger.warning("Opik OpenAI integration not available")
        return client


# ============================
# Custom Evaluation Metrics
# ============================

class GoalCoachingQualityMetric:
    """
    Custom LLM-as-judge metric for evaluating AI goal coaching quality.
    
    Evaluates responses on:
    - SMART goal alignment (Specific, Measurable, Achievable, Relevant, Time-bound)
    - Motivational effectiveness
    - Actionability of suggestions
    - Clarity and helpfulness
    """
    
    EVALUATION_PROMPT = """You are an expert evaluator for AI goal coaching systems.
    
Evaluate the AI coach's response based on these criteria:
1. **SMART Alignment**: Does the response help the user define goals that are Specific, Measurable, Achievable, Relevant, and Time-bound?
2. **Motivational Quality**: Is the response encouraging and supportive while being realistic?
3. **Actionability**: Does the response provide concrete, actionable next steps?
4. **Clarity**: Is the response clear, well-structured, and easy to understand?

User Message: {user_input}
AI Coach Response: {ai_response}

Rate the response on a scale of 0.0 to 1.0 where:
- 0.0-0.3: Poor coaching (unhelpful, generic, or discouraging)
- 0.4-0.6: Average coaching (somewhat helpful but lacking specifics)
- 0.7-0.8: Good coaching (helpful, specific, and encouraging)
- 0.9-1.0: Excellent coaching (exceptional guidance with SMART methodology)

Respond with ONLY a JSON object in this format:
{{"score": 0.X, "reason": "Brief explanation of the rating"}}
"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
    
    def score(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """
        Score the AI coaching response quality.
        
        Args:
            user_input: The user's message
            ai_response: The AI coach's response
            
        Returns:
            Dict with 'score' (0-1) and 'reason'
        """
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = self.EVALUATION_PROMPT.format(
                user_input=user_input,
                ai_response=ai_response
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1,
            )
            
            result_text = response.choices[0].message.content or ""
            
            # Parse the JSON response
            try:
                result = json.loads(result_text)
                return {
                    "score": float(result.get("score", 0.5)),
                    "reason": result.get("reason", "No explanation provided")
                }
            except json.JSONDecodeError:
                return {"score": 0.5, "reason": "Failed to parse evaluation response"}
                
        except Exception as e:
            logger.error(f"Error scoring coaching quality: {e}")
            return {"score": 0.5, "reason": f"Evaluation error: {str(e)}"}


class GoalExtractionQualityMetric:
    """
    Custom metric for evaluating AI-extracted goal quality.
    
    Evaluates extracted goals on:
    - Completeness (all necessary fields present)
    - SMART criteria alignment
    - Milestone structure quality
    - Task actionability
    """
    
    EVALUATION_PROMPT = """You are an expert evaluator for goal extraction systems.

Evaluate the extracted goal structure from a coaching conversation:

Conversation Context: {conversation_summary}

Extracted Goal:
- Title: {goal_title}
- Description: {goal_description}
- Category: {goal_category}
- Milestones: {milestones_summary}

Evaluate on:
1. **Completeness**: Does the goal capture the user's actual intent from the conversation?
2. **SMART Criteria**: Is the goal Specific, Measurable, Achievable, Relevant, Time-bound?
3. **Milestone Quality**: Are milestones logical, sequential, and appropriately sized?
4. **Task Clarity**: Are tasks specific and actionable?

Rate 0.0 to 1.0:
- 0.0-0.3: Poor extraction (misses key elements, unclear milestones)
- 0.4-0.6: Average (captures basics but lacks detail)
- 0.7-0.8: Good (well-structured, mostly SMART)
- 0.9-1.0: Excellent (comprehensive, fully SMART, actionable)

Respond with ONLY a JSON object:
{{"score": 0.X, "reason": "Brief explanation", "improvements": ["suggestion1", "suggestion2"]}}
"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
    
    def score(
        self,
        conversation_summary: str,
        goal_title: str,
        goal_description: str,
        goal_category: str,
        milestones_summary: str,
    ) -> Dict[str, Any]:
        """Score the extracted goal quality."""
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = self.EVALUATION_PROMPT.format(
                conversation_summary=conversation_summary,
                goal_title=goal_title,
                goal_description=goal_description,
                goal_category=goal_category,
                milestones_summary=milestones_summary,
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1,
            )
            
            result_text = response.choices[0].message.content or ""
            
            try:
                result = json.loads(result_text)
                return {
                    "score": float(result.get("score", 0.5)),
                    "reason": result.get("reason", "No explanation"),
                    "improvements": result.get("improvements", [])
                }
            except json.JSONDecodeError:
                return {"score": 0.5, "reason": "Parse error", "improvements": []}
                
        except Exception as e:
            logger.error(f"Error scoring goal extraction: {e}")
            return {"score": 0.5, "reason": str(e), "improvements": []}


class UserFrustrationDetector:
    """
    Detects user frustration in coaching conversations.
    
    Helps identify when the AI coach isn't meeting user needs.
    """
    
    DETECTION_PROMPT = """Analyze this coaching conversation exchange for signs of user frustration.

User Message: {user_input}
Previous AI Response: {previous_response}
Current User Reply: {current_reply}

Signs of frustration include:
- Repetitive questions (AI didn't answer properly)
- Short/dismissive replies
- Expressions of confusion or annoyance
- Requests to restart or change topic abruptly

Rate frustration level 0.0 to 1.0:
- 0.0-0.2: User is engaged and satisfied
- 0.3-0.5: Minor confusion or mild frustration
- 0.6-0.8: Noticeable frustration
- 0.9-1.0: High frustration, poor experience

Respond with ONLY JSON: {{"score": 0.X, "indicators": ["indicator1"]}}
"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
    
    def detect(
        self,
        user_input: str,
        previous_response: str,
        current_reply: str,
    ) -> Dict[str, Any]:
        """Detect user frustration level."""
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = self.DETECTION_PROMPT.format(
                user_input=user_input,
                previous_response=previous_response,
                current_reply=current_reply,
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1,
            )
            
            result_text = response.choices[0].message.content or ""
            
            try:
                result = json.loads(result_text)
                return {
                    "frustration_score": float(result.get("score", 0.0)),
                    "indicators": result.get("indicators", [])
                }
            except json.JSONDecodeError:
                return {"frustration_score": 0.0, "indicators": []}
                
        except Exception as e:
            logger.error(f"Error detecting frustration: {e}")
            return {"frustration_score": 0.0, "indicators": []}


# ============================
# Opik Integration Functions
# ============================

def log_chat_evaluation(
    trace_id: str,
    user_input: str,
    ai_response: str,
    session_id: int,
    user_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Log chat interaction with evaluation metrics to Opik.
    
    Args:
        trace_id: Unique trace identifier
        user_input: User's message
        ai_response: AI coach's response
        session_id: Chat session ID
        user_id: User ID
        
    Returns:
        Evaluation results or None if evaluation failed
    """
    if not _opik_configured:
        return None
    
    try:
        import opik
        
        # Evaluate coaching quality
        coach_metric = GoalCoachingQualityMetric()
        quality_result = coach_metric.score(user_input, ai_response)
        
        # Log to Opik using client.trace() method
        # Don't pass custom id - let Opik generate UUIDv7 automatically
        client = opik.Opik()
        trace = client.trace(
            name="chat_evaluation",
            input={
                "user_input": user_input,
                "session_id": session_id,
                "user_id": user_id,
            },
            output={
                "ai_response": ai_response,
                "coaching_quality": quality_result,
            },
            metadata={
                "evaluation_type": "coaching_quality",
            },
            tags=["chat", "evaluation"],
        )
        trace.end()
        
        return quality_result
        
    except Exception as e:
        logger.error(f"Error logging chat evaluation: {e}")
        return None


def log_goal_extraction_evaluation(
    trace_id: str,
    conversation: List[Dict],
    goal_data: Dict[str, Any],
    user_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Log goal extraction with evaluation metrics to Opik.
    
    Args:
        trace_id: Unique trace identifier
        conversation: List of conversation messages
        goal_data: Extracted goal data
        user_id: User ID
        
    Returns:
        Evaluation results or None
    """
    if not _opik_configured:
        return None
    
    try:
        import opik
        
        # Create conversation summary
        conv_summary = " | ".join([
            f"{m['role']}: {m['content'][:100]}"
            for m in conversation[:5]
        ])
        
        # Create milestones summary
        milestones = goal_data.get("milestones", [])
        milestones_summary = ", ".join([
            m.get("title", "Untitled")
            for m in milestones[:5]
        ])
        
        # Evaluate extraction quality
        extraction_metric = GoalExtractionQualityMetric()
        extraction_result = extraction_metric.score(
            conversation_summary=conv_summary,
            goal_title=goal_data.get("title", ""),
            goal_description=goal_data.get("description", ""),
            goal_category=goal_data.get("category", ""),
            milestones_summary=milestones_summary,
        )
        
        # Log to Opik using client.trace() method
        # Don't pass custom id - let Opik generate UUIDv7 automatically
        client = opik.Opik()
        trace = client.trace(
            name="goal_extraction_evaluation",
            input={
                "conversation_summary": conv_summary,
                "user_id": user_id,
            },
            output={
                "goal_title": goal_data.get("title"),
                "goal_category": goal_data.get("category"),
                "milestone_count": len(milestones),
                "extraction_quality": extraction_result,
            },
            metadata={
                "evaluation_type": "goal_extraction",
            },
            tags=["goal-extraction", "evaluation"],
        )
        trace.end()
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"Error logging goal extraction evaluation: {e}")
        return None


def create_experiment_dataset(
    name: str,
    description: str,
    items: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Create a dataset for running experiments.
    
    Args:
        name: Dataset name
        description: Dataset description
        items: List of dataset items with input/expected_output
        
    Returns:
        Dataset ID or None
    """
    if not _opik_configured:
        return None
    
    try:
        import opik
        
        client = opik.Opik()
        
        dataset = client.create_dataset(
            name=name,
            description=description,
        )
        
        for item in items:
            dataset.insert([{
                "input": item.get("input"),
                "expected_output": item.get("expected_output"),
                "metadata": item.get("metadata", {}),
            }])
        
        return dataset.id
        
    except Exception as e:
        logger.error(f"Error creating experiment dataset: {e}")
        return None


def run_evaluation_experiment(
    dataset_name: str,
    experiment_name: str,
    task_func: callable,
    metrics: List[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Run an evaluation experiment on a dataset.
    
    Args:
        dataset_name: Name of the dataset to use
        experiment_name: Name for this experiment run
        task_func: Function to evaluate (takes dataset item, returns output)
        metrics: List of metric names to use
        
    Returns:
        Experiment results or None
    """
    if not _opik_configured:
        return None
    
    try:
        import opik
        from opik.evaluation import evaluate
        from opik.evaluation.metrics import Hallucination, AnswerRelevance
        
        client = opik.Opik()
        dataset = client.get_dataset(name=dataset_name)
        
        # Default metrics for goal coaching
        eval_metrics = []
        if metrics is None or "hallucination" in metrics:
            eval_metrics.append(Hallucination())
        if metrics is None or "relevance" in metrics:
            eval_metrics.append(AnswerRelevance())
        
        # Run evaluation
        result = evaluate(
            experiment_name=experiment_name,
            dataset=dataset,
            task=task_func,
            scoring_metrics=eval_metrics,
        )
        
        return {
            "experiment_name": experiment_name,
            "dataset_name": dataset_name,
            "metrics": [m.__class__.__name__ for m in eval_metrics],
            "status": "completed",
        }
        
    except Exception as e:
        logger.error(f"Error running experiment: {e}")
        return None


# ============================
# Metrics Summary & Analytics
# ============================

def get_evaluation_summary() -> Dict[str, Any]:
    """
    Get summary of evaluation metrics from Opik.
    
    Returns:
        Summary of recent evaluations
    """
    if not _opik_configured:
        return {"enabled": False, "message": "Opik not configured"}
    
    try:
        import opik
        
        client = opik.Opik()
        
        # Get recent traces
        # Note: Actual implementation depends on Opik SDK version
        return {
            "enabled": True,
            "project_name": settings.OPIK_PROJECT_NAME,
            "workspace": settings.OPIK_WORKSPACE,
            "message": "Opik evaluation active",
        }
        
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {e}")
        return {"enabled": True, "error": str(e)}
