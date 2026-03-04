from __future__ import annotations

import json
import re
import logging
import asyncio
from typing import AsyncGenerator, Callable

from app.providers.base import LLMProvider, ToolDefinition, AgenticResult, MODEL_ROUTING
from app.config import settings

logger = logging.getLogger(__name__)


class MockProvider(LLMProvider):
    """Mock LLM provider for development. Returns realistic-looking responses."""

    @property
    def name(self) -> str:
        return "mock"

    async def complete(self, system: str, user: str, model: str) -> str:
        await asyncio.sleep(0.1)
        return f"[Mock response from {model}] Processed prompt with system context."

    async def stream(self, system: str, user: str, model: str) -> AsyncGenerator[str, None]:
        chunks = [
            "This ", "is ", "an ", "optimized ", "version ", "of ", "the ", "prompt.\n\n",
            "## Role\n",
            "You are an expert assistant specialized in the task at hand.\n\n",
            "## Context\n",
            "The user needs a well-structured, ", "clear, ", "and specific prompt ",
            "that achieves their intended goal.\n\n",
            "## Instructions\n",
            "1. Carefully analyze the input\n",
            "2. Apply structured reasoning\n",
            "3. Provide a comprehensive response\n",
            "4. Include relevant examples where appropriate\n\n",
            "## Output Format\n",
            "Respond in a structured format with clear sections and actionable content.",
        ]
        for chunk in chunks:
            await asyncio.sleep(0.03)
            yield chunk

    async def complete_json(self, system: str, user: str, model: str, schema: type | None = None) -> dict:
        await asyncio.sleep(0.1)

        # Detect what stage is being called based on system prompt content
        system_lower = system.lower()

        if "analyze" in system_lower or "classify" in system_lower or "evaluate" in system_lower:
            return {
                "task_type": "coding",
                "weaknesses": [
                    "Lacks specific constraints and boundaries",
                    "No output format specified",
                    "Missing context about the target environment",
                ],
                "strengths": [
                    "Clear high-level intent",
                    "Identifies the core task",
                ],
                "complexity": "moderate",
                "recommended_frameworks": ["CO-STAR", "structured-output"],
                "codebase_informed": False,
            }
        elif "strategy" in system_lower or "framework" in system_lower:
            return {
                "primary_framework": "CO-STAR",
                "secondary_frameworks": ["structured-output"],
                "rationale": "CO-STAR provides the ideal structure for this coding task, "
                             "combining context, objective, style, tone, audience, and response "
                             "format into a cohesive prompt framework.",
                "approach_notes": "Apply CO-STAR sections sequentially. Inject structured-output "
                                  "constraints in the Response section to ensure consistent formatting.",
            }
        elif "validate" in system_lower or "score" in system_lower:
            return {
                "is_improvement": True,
                "clarity_score": 8,
                "specificity_score": 7,
                "structure_score": 9,
                "faithfulness_score": 8,
                "conciseness_score": 7,
                "overall_score": 8,
                "verdict": "The optimized prompt is a significant improvement. It provides "
                           "clear structure, explicit constraints, and a well-defined output format.",
                "issues": [],
            }
        else:
            return {
                "optimized_prompt": "An optimized version of the prompt.",
                "changes_made": ["Added structure", "Clarified intent", "Added constraints"],
                "framework_applied": "CO-STAR",
                "optimization_notes": "Applied CO-STAR framework for structured prompting.",
            }

    async def complete_agentic(
        self,
        system: str,
        user: str,
        model: str,
        tools: list[ToolDefinition],
        max_turns: int = 20,
        on_tool_call: Callable[[str, dict], None] | None = None,
    ) -> AgenticResult:
        await asyncio.sleep(0.2)
        tool_calls_log = []

        # Simulate calling get_repo_summary if available
        for tool in tools:
            if tool.name == "get_repo_summary":
                if on_tool_call:
                    on_tool_call(tool.name, {})
                result = await tool.handler({})
                tool_calls_log.append({
                    "name": tool.name,
                    "input": {},
                    "output": result[:200] if result else "",
                })
                break

        return AgenticResult(
            text=json.dumps({
                "repo": "mock/repo",
                "tech_stack": ["Python", "FastAPI"],
                "key_files_read": [],
                "relevant_code_snippets": [],
                "codebase_observations": ["Mock observation: project uses standard patterns"],
                "prompt_grounding_notes": ["Mock: prompt aligns with codebase structure"],
            }),
            tool_calls=tool_calls_log,
        )


def _parse_json_response(text: str) -> dict:
    """3-strategy JSON parsing fallback."""
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: Extract ```json ... ``` code block
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 3: Extract first { ... } substring
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, TypeError):
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:200]}...")


async def detect_provider() -> LLMProvider:
    """Detect the best available LLM provider.

    Detection order:
    1. Check if `claude` CLI is available on PATH with valid credentials -> ClaudeCLIProvider
    2. Check if ANTHROPIC_API_KEY is set -> AnthropicAPIProvider
    3. Fall back to MockProvider for development
    """
    import shutil

    # Check for Claude CLI
    try:
        claude_path = shutil.which("claude")
        if claude_path:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    "claude", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=5.0,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                logger.info(f"Claude CLI detected at {claude_path}: {stdout.decode().strip()}")
                try:
                    from app.providers.claude_cli import ClaudeCLIProvider
                    return ClaudeCLIProvider()
                except ImportError:
                    logger.warning("Claude CLI found but claude_agent_sdk not installed")
    except (asyncio.TimeoutError, FileNotFoundError, OSError) as e:
        logger.warning(f"Claude CLI detection failed: {e}")

    # Check for Anthropic API key
    if settings.ANTHROPIC_API_KEY:
        try:
            from app.providers.anthropic_api import AnthropicAPIProvider
            provider = AnthropicAPIProvider(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("Using AnthropicAPIProvider")
            return provider
        except ImportError:
            logger.warning("ANTHROPIC_API_KEY set but anthropic package not installed")

    # Fall back to mock
    logger.warning("No LLM provider detected. Using MockProvider for development.")
    return MockProvider()
