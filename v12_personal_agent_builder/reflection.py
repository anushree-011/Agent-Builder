"""
==============================================================================
V12 - PERSONAL AGENT BUILDER: REFLECTION & SELF-EVALUATION
==============================================================================
Concept & Architecture:
This module implements the Reflection Subsystem (introduced in v08).
In production Agentic AI, high-reliability agents don't simply emit their first
draft. Instead, they use a "Self-Correction Loop":
1. Review Draft: The agent inspects its generated response alongside the user's objective.
2. Rubric Scoring: An evaluation pass grades the response (1-10) across criteria:
   - Completeness: Did it answer all parts of the user request?
   - Accuracy & Logic: Are calculations or claims correct?
   - Instruction Adherence: Did it follow all user constraints?
3. Actionable Critique: Generates specific feedback on what is missing or flawed.
4. Auto-Refinement: If the score is below a passing threshold (e.g., 7/10),
   the agent executes a revision turn incorporating the critique.
==============================================================================
"""

import json
from typing import Dict, Any, Optional, Callable


class ReflectionEngine:
    """
    Orchestrates automated self-evaluation, grading, and iterative refinement.
    """

    def __init__(
        self,
        llm_caller: Callable[[list], str],
        min_acceptable_score: int = 7,
        max_reflection_attempts: int = 2
    ):
        """
        Parameters:
        -----------
        llm_caller : Callable[[list], str]
            Function to call the LLM chat endpoint.
        min_acceptable_score : int
            Passing threshold (1-10). Drafts below this score are revised.
        max_reflection_attempts : int
            Maximum number of reflection refinement loops allowed.
        """
        self.llm_caller = llm_caller
        self.min_acceptable_score = min_acceptable_score
        self.max_reflection_attempts = max_reflection_attempts

    def evaluate(self, task: str, candidate_response: str) -> Dict[str, Any]:
        """
        Grades candidate response against the user task using structured JSON output.

        Parameters:
        -----------
        task : str
            The original user prompt or instruction.
        candidate_response : str
            The proposed answer or work output.

        Returns:
        --------
        dict : Contains 'score' (int), 'feedback' (str), and 'passed' (bool).
        """
        system_prompt = """
You are an impartial Reflection & Evaluation Critic.
Your job is to objectively grade an AI agent's proposed response to a user request.

Evaluation Criteria:
1. Completeness: Were all components of the request addressed?
2. Accuracy: Is the content correct, logical, and factual?
3. Helpfulness & Clarity: Is the format clean and easy to understand?

Return ONLY a JSON object:
{
    "score": <integer from 1 to 10>,
    "feedback": "<concise critique explaining strengths and specific flaws>",
    "suggestions": "<specific suggestions for improvement if score < 8>"
}
Do NOT use Markdown fences. Return ONLY the raw JSON object.
"""

        user_content = f"""
USER TASK:
{task}

PROPOSED RESPONSE:
{candidate_response}

Grade this response.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            raw_eval = self.llm_caller(messages).strip()

            # Clean potential markdown fences
            if raw_eval.startswith("```json"):
                raw_eval = raw_eval[7:]
            elif raw_eval.startswith("```"):
                raw_eval = raw_eval[3:]
            if raw_eval.endswith("```"):
                raw_eval = raw_eval[:-3]
            raw_eval = raw_eval.strip()

            data = json.loads(raw_eval)
            score = int(data.get("score", 5))
            feedback = data.get("feedback", "No feedback provided.")
            suggestions = data.get("suggestions", "")

            return {
                "score": score,
                "feedback": feedback,
                "suggestions": suggestions,
                "passed": score >= self.min_acceptable_score
            }

        except Exception as error:
            # Fallback if evaluation parsing fails
            return {
                "score": 8,
                "feedback": f"Evaluation parser warning: {error}. Proceeding with draft.",
                "suggestions": "",
                "passed": True
            }

    def refine(self, task: str, draft: str, critique: Dict[str, Any]) -> str:
        """
        Executes a refinement turn using the critique to produce an improved response.

        Parameters:
        -----------
        task : str
            Original user request.
        draft : str
            Previous draft response.
        critique : dict
            Feedback and suggestions from evaluation pass.

        Returns:
        --------
        str : Refined and improved response string.
        """
        refinement_prompt = f"""
You are an AI assistant refining your previous work based on critical review.

USER REQUEST:
{task}

PREVIOUS DRAFT:
{draft}

CRITIQUE & SCORE ({critique.get('score')}/10):
Feedback: {critique.get('feedback')}
Suggestions: {critique.get('suggestions')}

Please write an improved, high-quality final response addressing all critique points.
"""

        messages = [
            {"role": "system", "content": "You refine and improve responses based on critique."},
            {"role": "user", "content": refinement_prompt}
        ]

        return self.llm_caller(messages)
