from __future__ import annotations

import json
import re
import logging
from typing import AsyncGenerator, Callable

from app.providers.base import LLMProvider, ToolDefinition, AgenticResult

logger = logging.getLogger(__name__)


class AnthropicAPIProvider(LLMProvider):
    """LLM provider using the Anthropic Python SDK with direct API calls."""

    def __init__(self, api_key: str):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def name(self) -> str:
        return "anthropic_api"

    async def complete(self, system: str, user: str, model: str) -> str:
        response = await self._client.messages.create(
            model=model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text if response.content else ""

    async def stream(self, system: str, user: str, model: str) -> AsyncGenerator[str, None]:
        async with self._client.messages.stream(
            model=model,
            max_tokens=8192,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            async for chunk in stream.text_stream:
                yield chunk

    async def complete_json(self, system: str, user: str, model: str, schema: type | None = None) -> dict:
        raw = await self.complete(system, user, model)
        return _parse_json(raw)

    async def complete_agentic(
        self,
        system: str,
        user: str,
        model: str,
        tools: list[ToolDefinition],
        max_turns: int = 20,
        on_tool_call: Callable[[str, dict], None] | None = None,
    ) -> AgenticResult:
        api_tools = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ]
        tool_map = {t.name: t.handler for t in tools}

        messages = [{"role": "user", "content": user}]
        all_tool_calls = []
        turns = 0

        while turns < max_turns:
            turns += 1
            response = await self._client.messages.create(
                model=model,
                max_tokens=8192,
                system=system,
                tools=api_tools,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                text = next(
                    (b.text for b in response.content if hasattr(b, "text")),
                    "",
                )
                return AgenticResult(text=text, tool_calls=all_tool_calls)

            if response.stop_reason == "tool_use":
                results = []
                for block in response.content:
                    if block.type == "tool_use":
                        if on_tool_call:
                            on_tool_call(block.name, block.input)
                        result_str = await tool_map[block.name](block.input)
                        all_tool_calls.append({
                            "name": block.name,
                            "input": block.input,
                            "output": result_str[:500] if result_str else "",
                        })
                        results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })
                messages.append({"role": "user", "content": results})

        logger.warning(f"Agentic loop hit max_turns ({max_turns})")
        return AgenticResult(text="", tool_calls=all_tool_calls)


def _parse_json(text: str) -> dict:
    """3-strategy JSON parsing fallback."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, TypeError):
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:200]}...")
