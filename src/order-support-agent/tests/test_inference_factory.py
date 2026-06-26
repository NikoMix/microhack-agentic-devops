"""Tests for the fake inference client and the provider factory."""

from __future__ import annotations

import pytest

from order_support_agent.config import InferenceProvider, Settings
from order_support_agent.inference import create_inference_client
from order_support_agent.inference.base import ChatMessage, CompletionResult, ToolSpec
from order_support_agent.inference.errors import InferenceConfigurationError
from order_support_agent.inference.fake import FakeInferenceClient


async def test_fake_returns_scripted_in_order() -> None:
    client = FakeInferenceClient(
        scripted=[
            CompletionResult(text="first", finish_reason="stop"),
            CompletionResult(text="second", finish_reason="stop"),
        ]
    )
    first = await client.complete([ChatMessage.user("a")])
    second = await client.complete([ChatMessage.user("b")])
    assert (first.text, second.text) == ("first", "second")
    assert client.call_count == 2


async def test_fake_falls_back_to_default_when_exhausted() -> None:
    client = FakeInferenceClient(default=CompletionResult(text="fallback", finish_reason="stop"))
    result = await client.complete([ChatMessage.user("a")])
    assert result.text == "fallback"


async def test_fake_responder_sees_messages_and_tools() -> None:
    seen: dict[str, int] = {}

    def responder(messages: object, tools: object) -> CompletionResult:
        seen["messages"] = len(messages)  # type: ignore[arg-type]
        seen["tools"] = len(tools)  # type: ignore[arg-type]
        return CompletionResult(text="ok", finish_reason="stop")

    client = FakeInferenceClient(responder=responder)
    await client.complete(
        [ChatMessage.system("s"), ChatMessage.user("u")],
        tools=[ToolSpec(name="t", description="d", parameters={})],
    )
    assert seen == {"messages": 2, "tools": 1}


async def test_fake_records_call_details() -> None:
    client = FakeInferenceClient()
    await client.complete([ChatMessage.user("a")], temperature=0.3, max_tokens=128)
    recorded = client.calls[0]
    assert recorded.temperature == 0.3
    assert recorded.max_tokens == 128


async def test_fake_closes() -> None:
    client = FakeInferenceClient()
    async with client as opened:
        assert opened.closed is False
    assert client.closed is True


def test_factory_selects_github_models() -> None:
    settings = Settings(
        inference_provider=InferenceProvider.GITHUB_MODELS,
        github_token="ghp_test",
    )
    client = create_inference_client(settings)
    assert client.provider == "github_models"
    assert client.model == "openai/gpt-4o-mini"


def test_factory_github_models_requires_token() -> None:
    settings = Settings(inference_provider=InferenceProvider.GITHUB_MODELS)
    with pytest.raises(InferenceConfigurationError):
        create_inference_client(settings)


async def test_factory_selects_azure_openai() -> None:
    settings = Settings(
        inference_provider=InferenceProvider.AZURE_OPENAI,
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_chat_deployment="gpt-4o-mini",
    )
    client = create_inference_client(settings)
    try:
        assert client.provider == "azure_openai"
        assert client.endpoint == "https://example.openai.azure.com"
    finally:
        await client.aclose()


def test_factory_azure_openai_requires_endpoint() -> None:
    settings = Settings(inference_provider=InferenceProvider.AZURE_OPENAI)
    with pytest.raises(InferenceConfigurationError):
        create_inference_client(settings)


async def test_factory_selects_foundry() -> None:
    settings = Settings(
        inference_provider=InferenceProvider.FOUNDRY,
        azure_ai_foundry_project_endpoint="https://proj.services.ai.azure.com",
    )
    client = create_inference_client(settings)
    try:
        assert client.provider == "foundry"
    finally:
        await client.aclose()


def test_factory_foundry_requires_endpoint() -> None:
    settings = Settings(inference_provider=InferenceProvider.FOUNDRY)
    with pytest.raises(InferenceConfigurationError):
        create_inference_client(settings)
