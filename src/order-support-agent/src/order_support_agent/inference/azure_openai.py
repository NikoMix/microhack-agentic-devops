"""Azure OpenAI provider — keyless via Entra ID using the official ``openai`` SDK.

Uses :class:`AsyncAzureOpenAI` with an Entra bearer-token provider (no API keys).
The managed identity (or developer identity) needs the
``Cognitive Services OpenAI User`` role on the Azure OpenAI resource.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from order_support_agent.config import Settings

from ._azure_ai_inference import COGNITIVE_SERVICES_SCOPE
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
from .errors import InferenceConfigurationError


def _to_openai_messages(messages: Sequence[ChatMessage]) -> list[dict[str, Any]]:
    """Translate neutral messages into OpenAI chat message dicts."""
    payload: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "assistant" and message.tool_calls:
            payload.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {"name": call.name, "arguments": call.arguments},
                        }
                        for call in message.tool_calls
                    ],
                }
            )
        elif message.role == "tool":
            payload.append(
                {
                    "role": "tool",
                    "content": message.content or "",
                    "tool_call_id": message.tool_call_id or "",
                }
            )
        else:
            payload.append({"role": message.role, "content": message.content or ""})
    return payload


def _to_openai_response_format(response_format: ResponseFormat | None) -> dict[str, Any] | None:
    """Map a neutral response format onto the OpenAI ``response_format`` field."""
    if response_format is None or response_format.kind == "text":
        return None
    if response_format.kind == "json_object":
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": response_format.name,
            "schema": dict(response_format.schema or {}),
            "strict": response_format.strict,
        },
    }


class AzureOpenAIClient(InferenceClient):
    """Chat client backed by Azure OpenAI, authenticated keyless with Entra ID."""

    provider = "azure_openai"

    def __init__(self, settings: Settings) -> None:
        endpoint = settings.azure_openai_endpoint
        if not endpoint:
            raise InferenceConfigurationError(
                "Azure OpenAI provider requires AZURE_OPENAI_ENDPOINT to be set."
            )
        self._endpoint = endpoint
        self._deployment = settings.azure_openai_chat_deployment
        self._credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(self._credential, COGNITIVE_SERVICES_SCOPE)
        self._client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_version=settings.azure_openai_api_version,
            azure_ad_token_provider=token_provider,
            timeout=settings.request_timeout_seconds,
        )

    @property
    def model(self) -> str:
        """The Azure OpenAI deployment name acting as the model id."""
        return self._deployment

    @property
    def endpoint(self) -> str | None:
        """The Azure OpenAI resource endpoint."""
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
        """Call Azure OpenAI chat completions and normalize the result."""
        request: dict[str, Any] = {
            "model": self._deployment,
            "messages": _to_openai_messages(messages),
        }
        if temperature is not None:
            request["temperature"] = temperature
        if max_tokens is not None:
            request["max_tokens"] = max_tokens
        if tools:
            request["tools"] = [spec.to_openai_tool() for spec in tools]
            request["tool_choice"] = tool_choice
        formatted = _to_openai_response_format(response_format)
        if formatted is not None:
            request["response_format"] = formatted

        result = await self._client.chat.completions.create(**cast("Any", request))

        choice = result.choices[0]
        raw_tool_calls = choice.message.tool_calls or []
        tool_calls = tuple(
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=call.function.arguments or "{}",
            )
            for call in raw_tool_calls
            if call.type == "function"
        )
        usage = (
            Usage(
                input_tokens=result.usage.prompt_tokens,
                output_tokens=result.usage.completion_tokens,
                total_tokens=result.usage.total_tokens,
            )
            if result.usage is not None
            else None
        )
        return CompletionResult(
            text=choice.message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            model=result.model,
            usage=usage,
            raw=result,
        )

    async def aclose(self) -> None:
        """Close the underlying client and Entra credential."""
        await self._client.close()
        await self._credential.close()
