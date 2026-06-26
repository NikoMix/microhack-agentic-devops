"""A deterministic in-memory inference client for tests and offline demos.

The fake records every call and returns scripted results, letting the full
agent + tool-calling loop be exercised with **no network and no credentials**.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .base import (
    ChatMessage,
    CompletionResult,
    InferenceClient,
    ResponseFormat,
    ToolChoice,
    ToolSpec,
)

Responder = Callable[[Sequence[ChatMessage], Sequence[ToolSpec]], CompletionResult]


@dataclass
class RecordedCall:
    """A single captured invocation of :meth:`FakeInferenceClient.complete`."""

    messages: tuple[ChatMessage, ...]
    tools: tuple[ToolSpec, ...]
    tool_choice: ToolChoice
    temperature: float | None
    max_tokens: int | None
    response_format: ResponseFormat | None


class FakeInferenceClient(InferenceClient):
    """An :class:`InferenceClient` that replays scripted completions.

    Provide either ``scripted`` (a queue of results consumed in order) or
    ``responder`` (a function computing the next result from the conversation).
    When ``scripted`` is exhausted the ``default`` result is returned.
    """

    provider = "fake"

    def __init__(
        self,
        *,
        scripted: Sequence[CompletionResult] | None = None,
        responder: Responder | None = None,
        default: CompletionResult | None = None,
        model: str = "fake/gpt-4o-mini",
    ) -> None:
        self._scripted: list[CompletionResult] = list(scripted or ())
        self._responder = responder
        self._default = default or CompletionResult(
            text="(no scripted response)", finish_reason="stop"
        )
        self._model = model
        self.calls: list[RecordedCall] = []
        self.closed = False

    @property
    def model(self) -> str:
        """The fake model identifier."""
        return self._model

    @property
    def endpoint(self) -> str | None:
        """A sentinel endpoint (no network is used)."""
        return "fake://inference"

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[ToolSpec] = (),
        tool_choice: ToolChoice = "auto",
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: ResponseFormat | None = None,
    ) -> CompletionResult:
        """Record the call and return the next scripted or responder result."""
        self.calls.append(
            RecordedCall(
                messages=tuple(messages),
                tools=tuple(tools),
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
        )
        if self._responder is not None:
            return self._responder(messages, tools)
        if self._scripted:
            return self._scripted.pop(0)
        return self._default

    async def aclose(self) -> None:
        """Mark the client closed (no resources to release)."""
        self.closed = True

    @property
    def call_count(self) -> int:
        """Number of times :meth:`complete` was invoked."""
        return len(self.calls)
