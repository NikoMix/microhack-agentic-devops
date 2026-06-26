"""Tests for the Agent Framework <-> modular inference bridge."""

from __future__ import annotations

from agent_framework import Content, Message

from order_support_agent.agent.modular_chat_client import (
    ModularChatClient,
    _completion_contents,
    _finish_reason,
    _normalize_role,
    _to_neutral_messages,
    _to_response_format,
    _to_tool_choice,
    _usage_details,
)
from order_support_agent.inference.base import CompletionResult, Usage
from order_support_agent.inference.fake import FakeInferenceClient
from order_support_agent.models import TriageRecommendation


def test_normalize_role_falls_back_to_user() -> None:
    assert _normalize_role("assistant") == "assistant"
    assert _normalize_role("banana") == "user"


def test_to_neutral_messages_extracts_text() -> None:
    message = Message(role="user", contents=[Content.from_text("hello there")])
    neutral = _to_neutral_messages([message])
    assert neutral[0].role == "user"
    assert neutral[0].content == "hello there"


def test_to_neutral_messages_maps_function_result_to_tool() -> None:
    message = Message(
        role="tool",
        contents=[Content.from_function_result("call-1", result={"found": True})],
    )
    neutral = _to_neutral_messages([message])
    assert neutral[0].role == "tool"
    assert neutral[0].tool_call_id == "call-1"
    assert "found" in (neutral[0].content or "")


def test_to_tool_choice_normalizes() -> None:
    assert _to_tool_choice("required") == "required"
    assert _to_tool_choice({"mode": "none"}) == "none"
    assert _to_tool_choice(123) == "auto"


def test_to_response_format_from_pydantic_model() -> None:
    response_format = _to_response_format(TriageRecommendation)
    assert response_format is not None
    assert response_format.kind == "json_schema"
    assert response_format.strict is False


def test_finish_reason_prefers_tool_calls() -> None:
    from order_support_agent.inference.base import ToolCall

    with_tools = CompletionResult(
        tool_calls=(ToolCall(id="c", name="n", arguments="{}"),), finish_reason="stop"
    )
    assert _finish_reason(with_tools) == "tool_calls"
    assert _finish_reason(CompletionResult(text="x", finish_reason="weird")) == "stop"


def test_usage_details_maps_token_counts() -> None:
    result = CompletionResult(
        text="x", usage=Usage(input_tokens=3, output_tokens=2, total_tokens=5)
    )
    details = _usage_details(result)
    assert details is not None
    assert details["total_token_count"] == 5


def test_completion_contents_never_empty() -> None:
    contents = _completion_contents(CompletionResult(finish_reason="stop"))
    assert len(contents) == 1


async def test_get_response_returns_text_and_usage() -> None:
    client = ModularChatClient(
        FakeInferenceClient(
            scripted=[
                CompletionResult(
                    text="hi there",
                    finish_reason="stop",
                    usage=Usage(input_tokens=1, output_tokens=2, total_tokens=3),
                )
            ]
        )
    )
    response = await client.get_response(
        [Message(role="user", contents=[Content.from_text("Hello")])]
    )
    assert response.text == "hi there"
    assert response.usage_details is not None
    await client.aclose()


async def test_get_response_streams_updates() -> None:
    client = ModularChatClient(
        FakeInferenceClient(scripted=[CompletionResult(text="streamed", finish_reason="stop")])
    )
    stream = client.get_response(
        [Message(role="user", contents=[Content.from_text("Hello")])],
        stream=True,
    )
    updates = [update async for update in stream]
    assert any(update.text for update in updates)
    await client.aclose()
