"""Bridge the Microsoft Agent Framework onto the modular inference layer.

``ModularChatClient`` is a thin :class:`~agent_framework.BaseChatClient` whose
``_inner_get_response`` delegates to an :class:`InferenceClient`. By composing the
framework's :class:`FunctionInvocationLayer` (the automatic tool-calling loop) and
:class:`ChatTelemetryLayer` (OpenTelemetry spans) on top of the base client, an
``Agent`` built with :meth:`as_agent` transparently runs against whichever
provider ``INFERENCE_PROVIDER`` selects — Foundry, Azure OpenAI, or GitHub
Models — with **no change** to the agent or its tools.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Mapping, Sequence
from typing import Any, ClassVar, cast

from agent_framework import (
    BaseChatClient,
    ChatResponse,
    ChatResponseUpdate,
    Content,
    FunctionInvocationLayer,
    Message,
    ResponseStream,
    UsageDetails,
)
from agent_framework.observability import ChatTelemetryLayer
from pydantic import BaseModel

from order_support_agent.inference.base import (
    ChatMessage,
    CompletionResult,
    InferenceClient,
    ResponseFormat,
    Role,
    ToolCall,
    ToolChoice,
    ToolSpec,
)

_VALID_ROLES: frozenset[str] = frozenset({"system", "user", "assistant", "tool"})
_VALID_FINISH: frozenset[str] = frozenset({"stop", "length", "tool_calls", "content_filter"})
_VALID_TOOL_CHOICE: frozenset[str] = frozenset({"auto", "required", "none"})


def _normalize_role(role: str) -> Role:
    if role in _VALID_ROLES:
        return cast(Role, role)
    return "user"


def _to_neutral_messages(messages: Sequence[Message]) -> list[ChatMessage]:
    """Translate Agent Framework messages into provider-neutral messages."""
    neutral: list[ChatMessage] = []
    for message in messages:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        tool_result: str | None = None
        tool_call_id: str | None = None
        for content in message.contents:
            match content.type:
                case "text" if content.text:
                    text_parts.append(content.text)
                case "function_call":
                    raw_args = content.arguments
                    arguments = (
                        raw_args if isinstance(raw_args, str) else json.dumps(raw_args or {})
                    )
                    tool_calls.append(
                        ToolCall(
                            id=content.call_id or "",
                            name=content.name or "",
                            arguments=arguments,
                        )
                    )
                case "function_result":
                    tool_call_id = content.call_id
                    result = content.result
                    tool_result = (
                        result if isinstance(result, str) else json.dumps(result, default=str)
                    )
        if str(message.role) == "tool" or tool_result is not None:
            neutral.append(
                ChatMessage(role="tool", content=tool_result or "", tool_call_id=tool_call_id)
            )
            continue
        neutral.append(
            ChatMessage(
                role=_normalize_role(str(message.role)),
                content="\n".join(text_parts) if text_parts else None,
                tool_calls=tuple(tool_calls),
            )
        )
    return neutral


def _to_tool_specs(tools: Sequence[Any]) -> list[ToolSpec]:
    """Translate normalized framework tools into neutral OpenAI-style specs."""
    specs: list[ToolSpec] = []
    for tool in tools:
        to_spec = getattr(tool, "to_json_schema_spec", None)
        if not callable(to_spec):
            continue
        function = to_spec().get("function", {})
        specs.append(
            ToolSpec(
                name=function["name"],
                description=function.get("description") or "",
                parameters=function.get("parameters") or {},
            )
        )
    return specs


def _to_tool_choice(value: Any) -> ToolChoice:
    if isinstance(value, str):
        mode = value
    elif isinstance(value, Mapping):
        mode = str(value.get("mode", "auto"))
    else:
        mode = "auto"
    if mode in _VALID_TOOL_CHOICE:
        return cast(ToolChoice, mode)
    return "auto"


def _to_response_format(value: Any) -> ResponseFormat | None:
    if value is None:
        return None
    if isinstance(value, type) and issubclass(value, BaseModel):
        return ResponseFormat.json_schema(
            name=value.__name__, schema=value.model_json_schema(), strict=False
        )
    if isinstance(value, Mapping):
        title = str(value.get("title", "response"))
        return ResponseFormat.json_schema(name=title, schema=dict(value), strict=False)
    return None


def _finish_reason(result: CompletionResult) -> str:
    if result.tool_calls:
        return "tool_calls"
    reason = result.finish_reason
    return reason if reason in _VALID_FINISH else "stop"


def _usage_details(result: CompletionResult) -> UsageDetails | None:
    if result.usage is None:
        return None
    details: UsageDetails = {}
    if result.usage.input_tokens is not None:
        details["input_token_count"] = result.usage.input_tokens
    if result.usage.output_tokens is not None:
        details["output_token_count"] = result.usage.output_tokens
    if result.usage.total_tokens is not None:
        details["total_token_count"] = result.usage.total_tokens
    return details or None


def _completion_contents(result: CompletionResult) -> list[Content]:
    contents: list[Content] = []
    if result.text:
        contents.append(Content.from_text(result.text))
    for call in result.tool_calls:
        contents.append(
            Content.from_function_call(call.id, call.name, arguments=call.parsed_arguments())
        )
    if not contents:
        contents.append(Content.from_text(""))
    return contents


class ModularChatClient(FunctionInvocationLayer[Any], ChatTelemetryLayer[Any], BaseChatClient[Any]):
    """An Agent Framework chat client backed by the modular inference layer."""

    OTEL_PROVIDER_NAME: ClassVar[str] = "modular-inference"

    def __init__(self, inference: InferenceClient) -> None:
        """Wrap an :class:`InferenceClient` as an Agent Framework chat client.

        Args:
            inference: The provider-neutral inference client to delegate to.
        """
        self._inference = inference
        super().__init__(otel_provider_name=f"modular-inference:{inference.provider}")

    @property
    def inference(self) -> InferenceClient:
        """The underlying provider-neutral inference client."""
        return self._inference

    def service_url(self) -> str:
        """Return the backend endpoint for telemetry attribution."""
        return self._inference.endpoint or "modular-inference://local"

    def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> Awaitable[ChatResponse[Any]] | ResponseStream[ChatResponseUpdate, ChatResponse[Any]]:
        """Delegate a single model round-trip to the modular inference client."""
        response_format = options.get("response_format")
        if stream:
            return self._build_response_stream(
                self._stream(messages, options), response_format=response_format
            )
        return self._respond(messages, options)

    async def _complete(
        self, messages: Sequence[Message], options: Mapping[str, Any]
    ) -> CompletionResult:
        validated = await self._validate_options(options)
        return await self._inference.complete(
            _to_neutral_messages(messages),
            tools=_to_tool_specs(validated.get("tools") or []),
            tool_choice=_to_tool_choice(validated.get("tool_choice")),
            temperature=validated.get("temperature"),
            max_tokens=validated.get("max_tokens"),
            response_format=_to_response_format(validated.get("response_format")),
        )

    async def _respond(
        self, messages: Sequence[Message], options: Mapping[str, Any]
    ) -> ChatResponse[Any]:
        result = await self._complete(messages, options)
        return ChatResponse(
            messages=[Message(role="assistant", contents=_completion_contents(result))],
            finish_reason=cast(Any, _finish_reason(result)),
            usage_details=_usage_details(result),
            model=result.model or self._inference.model,
            response_format=options.get("response_format"),
            raw_representation=result.raw,
        )

    async def _stream(
        self, messages: Sequence[Message], options: Mapping[str, Any]
    ) -> AsyncIterator[ChatResponseUpdate]:
        result = await self._complete(messages, options)
        yield ChatResponseUpdate(
            contents=_completion_contents(result),
            role="assistant",
            finish_reason=cast(Any, _finish_reason(result)),
            model=result.model or self._inference.model,
        )

    async def aclose(self) -> None:
        """Release the underlying inference client and its credentials."""
        await self._inference.aclose()
