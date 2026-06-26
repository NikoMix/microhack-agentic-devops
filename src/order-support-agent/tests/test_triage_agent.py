"""End-to-end tests for the triage agent against the fake inference client.

These exercise the *real* Microsoft Agent Framework tool-calling loop and
structured-output parsing — only the model backend is faked, so the wiring under
test is the production wiring.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from order_support_agent.agent.triage_agent import (
    TriageError,
    build_triage_agent,
    run_triage,
    triage_once,
)
from order_support_agent.inference.base import ChatMessage, CompletionResult
from order_support_agent.inference.fake import FakeInferenceClient
from order_support_agent.models import TriageRecommendation
from order_support_agent.tools.domain import InMemoryOrderRepository

Responder = Callable[..., Callable[..., CompletionResult]]


async def test_run_triage_returns_structured_recommendation(
    fake_triage_agent: tuple[object, FakeInferenceClient],
    sample_recommendation: TriageRecommendation,
) -> None:
    agent, fake = fake_triage_agent
    recommendation = await run_triage(agent, "Order 1001 has not arrived.", order_id="1001")  # type: ignore[arg-type]

    assert isinstance(recommendation, TriageRecommendation)
    assert recommendation.category == sample_recommendation.category
    assert recommendation.order_id == "1001"
    await fake.aclose()


async def test_run_triage_actually_invokes_a_tool(
    fake_triage_agent: tuple[object, FakeInferenceClient],
) -> None:
    agent, fake = fake_triage_agent
    await run_triage(agent, "Where is order 1001?", order_id="1001")  # type: ignore[arg-type]

    # Two rounds: (1) request the tool, (2) final structured answer.
    assert fake.call_count == 2
    final_round: list[ChatMessage] = list(fake.calls[1].messages)
    assert any(message.role == "tool" for message in final_round)
    await fake.aclose()


async def test_triage_once_builds_and_closes_inference(
    repo: InMemoryOrderRepository,
    sample_recommendation: TriageRecommendation,
    triage_responder_factory: Responder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeInferenceClient(responder=triage_responder_factory(sample_recommendation))
    monkeypatch.setattr(
        "order_support_agent.agent.triage_agent.create_inference_client",
        lambda _settings: fake,
    )

    recommendation = await triage_once("Order 1001 issue", repo=repo, order_id="1001")

    assert isinstance(recommendation, TriageRecommendation)
    assert fake.closed is True


async def test_run_triage_raises_on_unstructured_output(
    repo: InMemoryOrderRepository,
) -> None:
    fake = FakeInferenceClient(scripted=[CompletionResult(text=None, finish_reason="stop")])
    agent = build_triage_agent(inference=fake, repo=repo)

    with pytest.raises(TriageError):
        await run_triage(agent, "An issue with no resolvable answer.")
    await fake.aclose()
