"""Shared Azure AI Inference backend for the GitHub Models and Foundry providers.

Both providers speak the same wire protocol via the ``azure-ai-inference`` SDK;
they differ only in endpoint and credential. GitHub Models authenticates with a
``GITHUB_TOKEN`` (an :class:`AzureKeyCredential`); Foundry authenticates keyless
with Entra ID via :class:`DefaultAzureCredential`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    ChatCompletionsToolCall,
    ChatCompletionsToolDefinition,
    ChatRequestMessage,
    FunctionCall,
    FunctionDefinition,
    JsonSchemaFormat,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential

from .base import (
    ChatMessage,
    CompletionResult,
    InferenceClient,
    ResponseFormat,
    ToolCall,
    ToolChoice,
    ToolSpec,
    Usage,
)

#: Entra scope used when authenticating to an Azure AI Foundry/Services endpoint.
COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


def _to_request_messages(messages: Sequence[ChatMessage]) -> list[ChatRequestMessage]:
    """Translate neutral messages into ``azure-ai-inference`` request messages."""
    out: list[ChatRequestMessage] = []
    for message in messages:
        match message.role:
            case "system":
                out.append(SystemMessage(content=message.content or ""))
            case "user":
                out.append(UserMessage(content=message.content or ""))
            case "assistant":
                if message.tool_calls:
                    out.append(
                        AssistantMessage(
                            content=message.content or None,
                            tool_calls=[
                                ChatCompletionsToolCall(
                                    id=call.id,
                                    function=FunctionCall(name=call.name, arguments=call.arguments),
                                )
                                for call in message.tool_calls
                            ],
                        )
                    )
                else:
                    out.append(AssistantMessage(content=message.content or ""))
            case "tool":
                out.append(
                    ToolMessage(
                        content=message.content or "", tool_call_id=message.tool_call_id or ""
                    )
                )
    return out


def _to_tool_definitions(tools: Sequence[ToolSpec]) -> list[ChatCompletionsToolDefinition]:
    """Translate neutral tool specs into ``azure-ai-inference`` tool definitions."""
    return [
        ChatCompletionsToolDefinition(
            function=FunctionDefinition(
                name=spec.name,
                description=spec.description,
                parameters=dict(spec.parameters),
            )
        )
        for spec in tools
    ]


def _to_response_format(
    response_format: ResponseFormat | None,
) -> str | JsonSchemaFormat | None:
    """Map a neutral response format onto the SDK's representation."""
    if response_format is None or response_format.kind == "text":
        return None
    if response_format.kind == "json_object":
        return "json_object"
    schema = dict(response_format.schema or {})
    return JsonSchemaFormat(name=response_format.name, schema=schema, strict=response_format.strict)


def _parse_completion(result: Any, fallback_model: str) -> CompletionResult:
    """Normalize a ``ChatCompletions`` result into a :class:`CompletionResult`."""
    choice = result.choices[0]
    raw_tool_calls = getattr(choice.message, "tool_calls", None) or []
    tool_calls = tuple(
        ToolCall(id=call.id, name=call.function.name, arguments=call.function.arguments or "{}")
        for call in raw_tool_calls
    )
    usage_obj = getattr(result, "usage", None)
    usage = (
        Usage(
            input_tokens=getattr(usage_obj, "prompt_tokens", None),
            output_tokens=getattr(usage_obj, "completion_tokens", None),
            total_tokens=getattr(usage_obj, "total_tokens", None),
        )
        if usage_obj is not None
        else None
    )
    finish_reason = choice.finish_reason
    return CompletionResult(
        text=choice.message.content,
        tool_calls=tool_calls,
        finish_reason=str(finish_reason) if finish_reason is not None else None,
        model=getattr(result, "model", None) or fallback_model,
        usage=usage,
        raw=result,
    )


class _AzureAIInferenceClient(InferenceClient):
    """Base client wrapping ``azure-ai-inference`` for a single endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        credential: AzureKeyCredential | AsyncTokenCredential,
        model: str,
        timeout: float,
        credential_scopes: Sequence[str] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._model = model
        client_kwargs: dict[str, Any] = {"endpoint": endpoint, "credential": credential}
        if credential_scopes is not None:
            client_kwargs["credential_scopes"] = list(credential_scopes)
        self._client = ChatCompletionsClient(**client_kwargs)
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    @property
    def endpoint(self) -> str | None:
        return self._endpoint

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
        request: dict[str, Any] = {
            "messages": _to_request_messages(messages),
            "model": self._model,
        }
        if temperature is not None:
            request["temperature"] = temperature
        if max_tokens is not None:
            request["max_tokens"] = max_tokens
        if tools:
            request["tools"] = _to_tool_definitions(tools)
            request["tool_choice"] = tool_choice
        formatted = _to_response_format(response_format)
        if formatted is not None:
            request["response_format"] = formatted
        result = await self._client.complete(**request)
        return _parse_completion(result, self._model)

    async def aclose(self) -> None:
        await self._client.close()
