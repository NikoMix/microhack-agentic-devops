"""Tests for the command-line entry point."""

from __future__ import annotations

import json

import pytest

from order_support_agent.__main__ import main
from order_support_agent.config import InferenceProvider, Settings
from order_support_agent.models import TriageRecommendation


def test_main_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def test_main_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    sample_recommendation: TriageRecommendation,
) -> None:
    async def fake_triage_once(issue: str, **_kwargs: object) -> TriageRecommendation:
        return sample_recommendation

    monkeypatch.setattr("order_support_agent.__main__.setup_telemetry", lambda *a, **k: "none")
    monkeypatch.setattr("order_support_agent.__main__.triage_once", fake_triage_once)

    exit_code = main(["My order 1001 issue", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["category"] == "shipping_delay"
    assert payload["order_id"] == "1001"


def test_main_provider_override_changes_settings(
    monkeypatch: pytest.MonkeyPatch,
    sample_recommendation: TriageRecommendation,
) -> None:
    captured: dict[str, object] = {}

    async def fake_triage_once(
        issue: str, *, settings: Settings, **_kwargs: object
    ) -> TriageRecommendation:
        captured["provider"] = settings.inference_provider
        return sample_recommendation

    monkeypatch.setattr("order_support_agent.__main__.setup_telemetry", lambda *a, **k: "none")
    monkeypatch.setattr("order_support_agent.__main__.triage_once", fake_triage_once)

    exit_code = main(["An issue", "--provider", "azure_openai", "--json"])

    assert exit_code == 0
    assert captured["provider"] is InferenceProvider.AZURE_OPENAI
