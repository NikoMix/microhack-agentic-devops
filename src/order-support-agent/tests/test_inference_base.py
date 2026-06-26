"""Tests for the provider-neutral inference data types."""

from __future__ import annotations

from order_support_agent.inference.base import (
    ChatMessage,
    CompletionResult,
    ResponseFormat,
    ToolCall,
    ToolSpec,
    Usage,
)


def test_tool_spec_renders_openai_schema() -> None:
    spec = ToolSpec(
        name="get_order",
        description="Look up an order.",
        parameters={"type": "object", "properties": {"order_id": {"type": "string"}}},
    )
    rendered = spec.to_openai_tool()
    assert rendered["type"] == "function"
    assert rendered["function"]["name"] == "get_order"
    assert rendered["function"]["parameters"]["properties"]["order_id"]["type"] == "string"


def test_tool_call_parses_arguments() -> None:
    call = ToolCall(id="c1", name="get_order", arguments='{"order_id": "1001"}')
    assert call.parsed_arguments() == {"order_id": "1001"}


def test_tool_call_parse_failures_return_empty() -> None:
    assert ToolCall(id="c", name="n", arguments="").parsed_arguments() == {}
    assert ToolCall(id="c", name="n", arguments="not json").parsed_arguments() == {}
    assert ToolCall(id="c", name="n", arguments="[1, 2]").parsed_arguments() == {}


def test_chat_message_convenience_constructors() -> None:
    assert ChatMessage.system("hi").role == "system"
    assert ChatMessage.user("yo").content == "yo"


def test_response_format_constructors() -> None:
    assert ResponseFormat.text().kind == "text"
    assert ResponseFormat.json_object().kind == "json_object"
    schema = ResponseFormat.json_schema("rec", {"type": "object"}, strict=False)
    assert schema.kind == "json_schema"
    assert schema.name == "rec"
    assert schema.strict is False


def test_completion_result_has_tool_calls() -> None:
    without = CompletionResult(text="done", finish_reason="stop")
    assert without.has_tool_calls is False
    with_calls = CompletionResult(
        tool_calls=(ToolCall(id="c", name="n", arguments="{}"),),
        finish_reason="tool_calls",
    )
    assert with_calls.has_tool_calls is True


def test_usage_defaults_to_none() -> None:
    usage = Usage()
    assert usage.input_tokens is None
    assert usage.total_tokens is None
