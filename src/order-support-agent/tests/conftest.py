"""Shared pytest fixtures for the Order Support agent tests."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import pytest

from order_support_agent.agent.triage_agent import build_triage_agent
from order_support_agent.inference.base import ChatMessage, CompletionResult, ToolCall, ToolSpec
from order_support_agent.inference.fake import FakeInferenceClient
from order_support_agent.models import (
    RecommendedAction,
    TriageCategory,
    TriageRecommendation,
    TriageSeverity,
)
from order_support_agent.tools.domain import InMemoryOrderRepository, default_repository

if TYPE_CHECKING:
    from agent_framework import Agent

Responder = Callable[[Sequence[ChatMessage], Sequence[ToolSpec]], CompletionResult]

_CONTRACT_ENV_VARS = (
    "INFERENCE_PROVIDER",
    "GITHUB_TOKEN",
    "GITHUB_MODELS_ENDPOINT",
    "GITHUB_MODELS_MODEL",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT",
    "AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT",
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    "ENABLE_AZURE_MONITOR",
    "ENABLE_FOUNDRY_TRACING",
    "ENABLE_SENSITIVE_TELEMETRY",
    "ORDERS_MCP_URL",
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove contract env vars so settings tests are deterministic."""
    for name in _CONTRACT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def repo() -> InMemoryOrderRepository:
    """A fresh, seeded in-memory repository."""
    return default_repository()


@pytest.fixture
def sample_recommendation() -> TriageRecommendation:
    """A representative structured recommendation."""
    return TriageRecommendation(
        category=TriageCategory.SHIPPING_DELAY,
        severity=TriageSeverity.HIGH,
        recommended_action=RecommendedAction.APOLOGIZE_AND_TRACK,
        summary="Order 1001 is stuck in transit with the carrier.",
        suggested_customer_reply="We're sorry — your order is delayed; we're chasing the carrier.",
        confidence=0.82,
        order_id="1001",
        references=("order:1001",),
    )


def make_triage_responder(
    recommendation: TriageRecommendation,
    *,
    tool_name: str = "get_order",
    tool_arguments: dict[str, str] | None = None,
) -> Responder:
    """Build a responder that requests one tool, then returns ``recommendation``.

    The first completion (no tool result yet) asks the agent to call ``tool_name``;
    once a tool result is in the transcript, the final structured JSON is returned.
    """
    arguments = json.dumps(tool_arguments or {"order_id": "1001"})

    def responder(messages: Sequence[ChatMessage], _tools: Sequence[ToolSpec]) -> CompletionResult:
        if any(message.role == "tool" for message in messages):
            return CompletionResult(
                text=recommendation.model_dump_json(),
                finish_reason="stop",
            )
        return CompletionResult(
            tool_calls=(ToolCall(id="call-1", name=tool_name, arguments=arguments),),
            finish_reason="tool_calls",
        )

    return responder


@pytest.fixture
def fake_triage_agent(
    repo: InMemoryOrderRepository,
    sample_recommendation: TriageRecommendation,
) -> tuple[Agent, FakeInferenceClient]:
    """A real Agent Framework agent backed by a scripted fake inference client."""
    fake = FakeInferenceClient(responder=make_triage_responder(sample_recommendation))
    agent = build_triage_agent(inference=fake, repo=repo)
    return agent, fake


@pytest.fixture
def triage_responder_factory() -> Callable[..., Responder]:
    """Expose the triage responder builder to tests."""
    return make_triage_responder
