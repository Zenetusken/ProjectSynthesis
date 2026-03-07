"""Stage 1: Analyze

Classifies the prompt and identifies optimization opportunities.
Uses claude-haiku for fast, cheap structured JSON extraction.
"""

import asyncio
import logging
from typing import Optional

from app.config import settings
from app.prompts.analyzer_prompt import get_analyzer_prompt
from app.providers.base import MODEL_ROUTING, LLMProvider
from app.services.context_builders import build_codebase_summary

logger = logging.getLogger(__name__)


async def run_analyze(
    provider: LLMProvider,
    raw_prompt: str,
    codebase_context: Optional[dict] = None,
    file_contexts: list[dict] | None = None,        # N24: attached file content
    url_fetched_contexts: list[dict] | None = None, # N26: pre-fetched URL content
    instructions: list[str] | None = None,          # N37: user output constraints
) -> dict:
    """Run Stage 1 analysis on the raw prompt.

    Returns:
        dict with keys: task_type, weaknesses, strengths, complexity,
                        recommended_frameworks, codebase_informed
    """
    system_prompt = get_analyzer_prompt()

    user_message = f"Analyze this prompt:\n\n---\n{raw_prompt}\n---"

    # N21: use build_codebase_summary (not raw json.dumps)
    if codebase_context:
        codebase_summary = build_codebase_summary(codebase_context)
        if codebase_summary:
            user_message += f"\n\nCodebase context:\n{codebase_summary}"

    # N24: inject attached file content
    if file_contexts:
        blocks = []
        for fc in file_contexts[:5]:
            name = fc.get("name", "file")
            content = str(fc.get("content", ""))[:1500]
            blocks.append(f"[{name}]\n{content}")
        user_message += "\n\nAttached files:\n" + "\n\n".join(blocks)

    # N26: inject pre-fetched URL content
    if url_fetched_contexts:
        blocks = []
        for uc in url_fetched_contexts[:3]:
            url = uc.get("url", "url")
            content = str(uc.get("content", ""))  # N41: capped at source (url_fetcher.py)
            blocks.append(f"[{url}]\n{content}")
        user_message += "\n\nReferenced URLs:\n" + "\n\n".join(blocks)

    # N37: inject output constraints so analyzer can flag incompatibilities
    if instructions:
        constraint_block = "\n".join(f"  - {i}" for i in instructions[:10])
        user_message += (
            f"\n\nUser-specified output constraints:\n{constraint_block}"
        )

    model = MODEL_ROUTING["analyze"]

    try:
        result = await asyncio.wait_for(
            provider.complete_json(system_prompt, user_message, model),
            timeout=settings.ANALYZE_TIMEOUT_SECONDS,
        )
        result["analysis_quality"] = "full"
    except asyncio.TimeoutError:
        logger.warning(
            "Analyze stage timed out after %ds", settings.ANALYZE_TIMEOUT_SECONDS
        )
        raise  # Propagate to pipeline.py as a stage failure
    except Exception as e:
        logger.error(f"Stage 1 (Analyze) failed: {e}")
        # Return sensible defaults so downstream stages can still run
        result = {
            "task_type": "general",
            "weaknesses": ["Analysis failed - using defaults"],
            "strengths": [],
            "complexity": "moderate",
            "recommended_frameworks": ["CO-STAR"],
            "codebase_informed": codebase_context is not None,
            "analysis_quality": "fallback",
        }

    # Ensure required fields
    result.setdefault("task_type", "general")
    result.setdefault("weaknesses", [])
    result.setdefault("strengths", [])
    result.setdefault("complexity", "moderate")
    result.setdefault("recommended_frameworks", [])
    result.setdefault("codebase_informed", codebase_context is not None)

    return result
