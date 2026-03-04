from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Awaitable, Callable


MODEL_ROUTING = {
    "explore": "claude-sonnet-4-6",
    "analyze": "claude-haiku-4-5-20251001",
    "strategy": "claude-opus-4-6",
    "optimize": "claude-opus-4-6",
    "validate": "claude-sonnet-4-6",
}


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    handler: Callable[[dict], Awaitable[str]]


@dataclass
class AgenticResult:
    text: str
    tool_calls: list[dict] = field(default_factory=list)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @abstractmethod
    async def complete(self, system: str, user: str, model: str) -> str:
        """Single-shot completion. Returns full response text."""
        ...

    @abstractmethod
    async def stream(self, system: str, user: str, model: str) -> AsyncGenerator[str, None]:
        """Streaming completion. Yields text chunks as they arrive."""
        ...

    @abstractmethod
    async def complete_json(self, system: str, user: str, model: str, schema: type | None = None) -> dict:
        """Structured JSON output with 3-strategy fallback:
        1. Parse raw response as JSON
        2. Extract first ```json ... ``` code block, parse it
        3. Extract first { ... } substring with regex, parse it
        """
        ...

    @abstractmethod
    async def complete_agentic(
        self,
        system: str,
        user: str,
        model: str,
        tools: list[ToolDefinition],
        max_turns: int = 20,
        on_tool_call: Callable[[str, dict], None] | None = None,
    ) -> AgenticResult:
        """Agentic tool-calling loop."""
        ...
