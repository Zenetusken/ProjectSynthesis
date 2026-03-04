"""Stage 4: Validate

Scores and verifies the optimized prompt is genuinely better.
Uses claude-sonnet for quality assessment.
Server-side weighted average computation (never trust LLM arithmetic).
"""

import json
import logging

from app.providers.base import LLMProvider, MODEL_ROUTING
from app.prompts.validator_prompt import get_validator_prompt

logger = logging.getLogger(__name__)

# Score weights for overall_score computation
SCORE_WEIGHTS = {
    "clarity_score": 0.20,
    "specificity_score": 0.20,
    "structure_score": 0.15,
    "faithfulness_score": 0.25,
    "conciseness_score": 0.20,
}


def compute_overall_score(scores: dict) -> int:
    """Compute weighted average overall score.

    Weights: clarity 20%, specificity 20%, structure 15%,
             faithfulness 25%, conciseness 20%

    Returns: integer 1-10
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for field, weight in SCORE_WEIGHTS.items():
        value = scores.get(field)
        if value is not None and isinstance(value, (int, float)):
            weighted_sum += value * weight
            total_weight += weight

    if total_weight == 0:
        return 5  # default mid-score

    raw = weighted_sum / total_weight
    return max(1, min(10, round(raw)))


async def run_validate(
    provider: LLMProvider,
    original_prompt: str,
    optimized_prompt: str,
    changes_made: list[str],
) -> dict:
    """Run Stage 4 validation.

    Returns:
        dict with keys: is_improvement, clarity_score, specificity_score,
                        structure_score, faithfulness_score, conciseness_score,
                        overall_score, verdict, issues, scores
    """
    system_prompt = get_validator_prompt()

    user_message = (
        f"Original prompt:\n---\n{original_prompt}\n---\n\n"
        f"Optimized prompt:\n---\n{optimized_prompt}\n---\n\n"
        f"Changes made:\n{json.dumps(changes_made, indent=2)}"
    )

    model = MODEL_ROUTING["validate"]

    try:
        result = await provider.complete_json(system_prompt, user_message, model)
    except Exception as e:
        logger.error(f"Stage 4 (Validate) failed: {e}")
        result = {
            "is_improvement": True,
            "clarity_score": 5,
            "specificity_score": 5,
            "structure_score": 5,
            "faithfulness_score": 5,
            "conciseness_score": 5,
            "verdict": "Validation failed - default scores applied.",
            "issues": ["Validation stage encountered an error"],
        }

    # Ensure all score fields exist
    for field in SCORE_WEIGHTS:
        if field not in result or not isinstance(result.get(field), (int, float)):
            result[field] = 5

    # ALWAYS compute overall_score server-side (never trust LLM arithmetic)
    result["overall_score"] = compute_overall_score(result)

    # Ensure other required fields
    result.setdefault("is_improvement", True)
    result.setdefault("verdict", "")
    result.setdefault("issues", [])

    # Build scores sub-object for SSE event
    result["scores"] = {
        "clarity_score": result["clarity_score"],
        "specificity_score": result["specificity_score"],
        "structure_score": result["structure_score"],
        "faithfulness_score": result["faithfulness_score"],
        "conciseness_score": result["conciseness_score"],
        "overall_score": result["overall_score"],
    }

    return result
