"""Provider-neutral inference abstraction.

This is the **modular inference layer**. Feature code (and the Agent Framework
bridge) depend only on :class:`InferenceClient` and the small set of neutral
data types defined here — never on a concrete provider SDK. Concrete providers
live in sibling modules and are selected by
:func:`order_support_agent.inference.factory.create_inference_client`.
"""

from __future__ import annotations

import abc
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Literal, Self

Role = Literal["system", "user", "assistant", "tool"]
ToolChoice = Literal["auto", "required", "none"]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A callable tool advertised to the model (OpenAI-style function schema)."""

    name: str
    description: str
    parameters: Mapping[str, Any]

    def to_openai_tool(self) -> dict[str, Any]:
        """Render as an OpenAI/GitHub-Models ``tools`` entry."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": dict(self.parameters),
            },
        }


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A model-requested tool invocation."""

    id: str
    name: str
    arguments: str  # raw JSON string, as emitted by the model

    def parsed_arguments(self) -> dict[str, Any]:
        """Best-effort parse of ``arguments`` into a dict (``{}`` on failure)."""
        if not self.arguments:
            return {}
        try:
            parsed: Any = json.loads(self.arguments)
        except (json.JSONDecodeError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single conversation turn in provider-neutral form."""

    role: Role
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    name: str | None = None

    @classmethod
    def system(cls, content: str) -> ChatMessage:
        """Convenience constructor for a system message."""
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> ChatMessage:
        """Convenience constructor for a user message."""
        return cls(role="user", content=content)


@dataclass(frozen=True, slots=True)
class ResponseFormat:
    """How the model should shape its output.

    ``kind`` is ``"text"`` (default), ``"json_object"`` (free-form JSON), or
    ``"json_schema"`` (constrained to ``schema``). Image generation is never a
    valid response format in this codebase.
    """

    kind: Literal["text", "json_object", "json_schema"] = "text"
    name: str = "response"
    schema: Mapping[str, Any] | None = None
    strict: bool = True

    @classmethod
    def text(cls) -> ResponseFormat:
        """Free-form text output (the default)."""
        return cls(kind="text")

    @classmethod
    def json_object(cls) -> ResponseFormat:
        """Free-form JSON output."""
        return cls(kind="json_object")

    @classmethod
    def json_schema(
        cls, name: str, schema: Mapping[str, Any], *, strict: bool = True
    ) -> ResponseFormat:
        """Build a JSON-schema-constrained response format."""
        return cls(kind="json_schema", name=name, schema=schema, strict=strict)


@dataclass(frozen=True, slots=True)
class Usage:
    """Token accounting for a completion, when the provider reports it."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class CompletionResult:
    """The normalized result of a single model round-trip."""

    text: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    finish_reason: str | None = None
    model: str | None = None
    usage: Usage | None = None
    raw: Any = field(default=None, repr=False, compare=False)

    @property
    def has_tool_calls(self) -> bool:
        """True when the model requested one or more tool invocations."""
        return bool(self.tool_calls)


class InferenceClient(abc.ABC):
    """Provider-neutral async chat client.

    Subclasses implement :meth:`complete` against exactly one backend. The class
    is an async context manager so callers can deterministically release SDK
    clients and credentials.
    """

    #: Stable provider identifier, e.g. ``"github_models"``.
    provider: str = "unknown"

    @property
    @abc.abstractmethod
    def model(self) -> str:
        """The model/deployment this client targets."""

    @property
    def endpoint(self) -> str | None:
        """The service endpoint, when applicable (used for telemetry)."""
        return None

    @abc.abstractmethod
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
        """Perform one chat completion round-trip and return a normalized result."""

    async def aclose(self) -> None:  # noqa: B027 - intentional no-op default
        """Release any underlying SDK clients/credentials. Override as needed."""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()


__all__ = [
    "ChatMessage",
    "CompletionResult",
    "InferenceClient",
    "ResponseFormat",
    "Role",
    "ToolCall",
    "ToolChoice",
    "ToolSpec",
    "Usage",
]
