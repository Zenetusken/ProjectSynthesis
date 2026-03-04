"""Stage 3: Optimize (streaming)

Rewrites the prompt using the selected strategy.
Uses claude-opus for creative rewriting at maximum capability.
Streams token by token via SSE step_progress events.
"""

import json
import logging
from typing import AsyncGenerator, Optional

from app.providers.base import LLMProvider, MODEL_ROUTING
from app.prompts.optimizer_prompts import get_optimizer_prompt

logger = logging.getLogger(__name__)


async def run_optimize(
    provider: LLMProvider,
    raw_prompt: str,
    analysis: dict,
    strategy: dict,
    codebase_context: Optional[dict] = None,
) -> AsyncGenerator[tuple[str, dict], None]:
    """Run Stage 3 optimization with streaming.

    Yields:
        ("step_progress", {"step": "optimize", "content": "chunk"}) for each token
        ("optimization", {optimized_prompt, changes_made, framework_applied, optimization_notes})
    """
    task_type = analysis.get("task_type", "general")
    system_prompt = get_optimizer_prompt(task_type)

    user_message = (
        f"Raw prompt to optimize:\n---\n{raw_prompt}\n---\n\n"
        f"Analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"Strategy:\n{json.dumps(strategy, indent=2)}"
    )
    if codebase_context:
        user_message += f"\n\nCodebase context:\n{json.dumps(codebase_context, indent=2)}"

    model = MODEL_ROUTING["optimize"]

    # Stream the optimization
    full_text = ""
    try:
        async for chunk in provider.stream(system_prompt, user_message, model):
            full_text += chunk
            yield ("step_progress", {"step": "optimize", "content": chunk})
    except Exception as e:
        logger.error(f"Stage 3 (Optimize) streaming failed: {e}")
        # Fall back to non-streaming
        try:
            full_text = await provider.complete(system_prompt, user_message, model)
        except Exception as e2:
            logger.error(f"Stage 3 (Optimize) complete also failed: {e2}")
            full_text = raw_prompt  # Return original as fallback

    # Try to extract structured data from the response
    optimized_prompt = full_text
    changes_made = []
    framework_applied = strategy.get("primary_framework", "")
    optimization_notes = ""

    # Try to parse if the response is JSON
    try:
        parsed = json.loads(full_text)
        if isinstance(parsed, dict):
            optimized_prompt = parsed.get("optimized_prompt", full_text)
            changes_made = parsed.get("changes_made", [])
            framework_applied = parsed.get("framework_applied", framework_applied)
            optimization_notes = parsed.get("optimization_notes", "")
    except (json.JSONDecodeError, TypeError):
        # Response is plain text (the optimized prompt itself)
        # Try to extract JSON block from mixed content
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", full_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                optimized_prompt = parsed.get("optimized_prompt", full_text)
                changes_made = parsed.get("changes_made", [])
                framework_applied = parsed.get("framework_applied", framework_applied)
                optimization_notes = parsed.get("optimization_notes", "")
            except (json.JSONDecodeError, TypeError):
                pass

    yield ("optimization", {
        "optimized_prompt": optimized_prompt,
        "changes_made": changes_made,
        "framework_applied": framework_applied,
        "optimization_notes": optimization_notes,
    })
