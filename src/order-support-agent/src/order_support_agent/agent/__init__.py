"""The Order Support / Triage agent built on the Microsoft Agent Framework."""

from __future__ import annotations

from order_support_agent.agent.modular_chat_client import ModularChatClient
from order_support_agent.agent.prompts import SYSTEM_PROMPT
from order_support_agent.agent.tools import build_order_toolset
from order_support_agent.agent.triage_agent import (
    DEFAULT_AGENT_NAME,
    TriageError,
    build_triage_agent,
    run_triage,
    triage_once,
)

__all__ = [
    "DEFAULT_AGENT_NAME",
    "SYSTEM_PROMPT",
    "ModularChatClient",
    "TriageError",
    "build_order_toolset",
    "build_triage_agent",
    "run_triage",
    "triage_once",
]
