"""Tests for the FastAPI service surface (offline, fake provider)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from order_support_agent.config import InferenceProvider, Settings
from order_support_agent.models import TriageRecommendation
from order_support_agent.service import create_app

if TYPE_CHECKING:
    from agent_framework import Agent

    from order_support_agent.inference.fake import FakeInferenceClient


def _settings() -> Settings:
    return Settings(enable_azure_monitor=False)


def test_healthz(fake_triage_agent: tuple[Agent, FakeInferenceClient]) -> None:
    agent, _ = fake_triage_agent
    app = create_app(settings=_settings(), agent=agent)
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_ready(fake_triage_agent: tuple[Agent, FakeInferenceClient]) -> None:
    agent, _ = fake_triage_agent
    app = create_app(settings=_settings(), agent=agent)
    with TestClient(app) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_triage_returns_structured_recommendation(
    fake_triage_agent: tuple[Agent, FakeInferenceClient],
    sample_recommendation: TriageRecommendation,
) -> None:
    agent, _ = fake_triage_agent
    app = create_app(settings=_settings(), agent=agent)
    with TestClient(app) as client:
        response = client.post("/triage", json={"issue": "Order 1001 is late", "order_id": "1001"})
    assert response.status_code == 200
    body = TriageRecommendation.model_validate(response.json())
    assert body.category == sample_recommendation.category
    assert body.order_id == "1001"


def test_triage_rejects_empty_issue(
    fake_triage_agent: tuple[Agent, FakeInferenceClient],
) -> None:
    agent, _ = fake_triage_agent
    app = create_app(settings=_settings(), agent=agent)
    with TestClient(app) as client:
        response = client.post("/triage", json={"issue": ""})
    assert response.status_code == 422


def test_unready_when_provider_unconfigured() -> None:
    settings = Settings(
        inference_provider=InferenceProvider.GITHUB_MODELS,
        enable_azure_monitor=False,
    )
    app = create_app(settings=settings)
    with TestClient(app) as client:
        ready = client.get("/readyz")
        triage = client.post("/triage", json={"issue": "Where is my order?"})
    assert ready.status_code == 503
    assert triage.status_code == 503
