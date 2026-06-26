"""Build and drive the Order Support / Triage agent.

This module wires the modular inference layer to the Microsoft Agent Framework:
a :class:`ModularChatClient` (which swaps providers purely from configuration)
is turned into an :class:`~agent_framework.Agent` with the triage tools and a
structured-output contract (:class:`TriageRecommendation`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from order_support_agent.agent.modular_chat_client import ModularChatClient
from order_support_agent.agent.prompts import SYSTEM_PROMPT
from order_support_agent.agent.tools import build_order_toolset
from order_support_agent.config import Settings, get_settings
from order_support_agent.inference.factory import create_inference_client
from order_support_agent.models import TriageRecommendation
from order_support_agent.tools.domain import OrderRepository, default_repository

if TYPE_CHECKING:
    from agent_framework import Agent, FunctionTool

    from order_support_agent.inference.base import InferenceClient

DEFAULT_AGENT_NAME = "contoso-order-triage"


class TriageError(RuntimeError):
    """Raised when the agent does not return a valid structured recommendation."""


def build_triage_agent(
    *,
    inference: InferenceClient | None = None,
    repo: OrderRepository | None = None,
    settings: Settings | None = None,
    tools: list[FunctionTool] | None = None,
    name: str = DEFAULT_AGENT_NAME,
) -> Agent:
    """Construct the triage :class:`~agent_framework.Agent`.

    Args:
        inference: An inference client. When omitted, one is created from
            ``settings`` via the provider factory.
        repo: The order repository the tools read from. Defaults to the
            in-process fixture repository.
        settings: Configuration. Defaults to :func:`get_settings`.
        tools: Pre-built tools. Defaults to :func:`build_order_toolset`.
        name: The agent name surfaced in traces.

    Returns:
        A ready-to-run agent whose provider is governed by ``INFERENCE_PROVIDER``.
    """
    resolved_settings = settings or get_settings()
    resolved_repo = repo or default_repository()
    client = ModularChatClient(inference or create_inference_client(resolved_settings))
    toolset = tools if tools is not None else build_order_toolset(resolved_repo)
    return client.as_agent(
        name=name,
        instructions=SYSTEM_PROMPT,
        tools=toolset,
        default_options={
            "temperature": resolved_settings.agent_temperature,
            "max_tokens": resolved_settings.agent_max_tokens,
        },
    )


def _format_issue(
    issue: str,
    *,
    customer_id: str | None = None,
    order_id: str | None = None,
) -> str:
    """Render the customer issue with any known identifiers as a single prompt."""
    lines = [f"Customer issue: {issue.strip()}"]
    if order_id:
        lines.append(f"Known order id: {order_id}")
    if customer_id:
        lines.append(f"Known customer id: {customer_id}")
    return "\n".join(lines)


async def run_triage(
    agent: Agent,
    issue: str,
    *,
    customer_id: str | None = None,
    order_id: str | None = None,
) -> TriageRecommendation:
    """Triage ``issue`` with an existing ``agent`` and return the recommendation.

    The caller owns the ``agent`` lifecycle (and therefore the inference
    client). Use :func:`triage_once` for a self-contained, one-shot call.

    Args:
        agent: A triage agent from :func:`build_triage_agent`.
        issue: The free-text customer complaint.
        customer_id: Optional known customer id to seed the lookup.
        order_id: Optional known order id to seed the lookup.

    Returns:
        The structured triage recommendation.

    Raises:
        TriageError: If the model does not return a valid structured value.
    """
    response = await agent.run(
        _format_issue(issue, customer_id=customer_id, order_id=order_id),
        options={"response_format": TriageRecommendation},
    )
    value = response.value
    if not isinstance(value, TriageRecommendation):
        msg = "The model did not return a valid structured triage recommendation."
        raise TriageError(msg)
    return value


async def triage_once(
    issue: str,
    *,
    settings: Settings | None = None,
    repo: OrderRepository | None = None,
    customer_id: str | None = None,
    order_id: str | None = None,
) -> TriageRecommendation:
    """Triage ``issue`` end to end, building and closing the agent internally.

    Args:
        issue: The free-text customer complaint.
        settings: Configuration. Defaults to :func:`get_settings`.
        repo: The order repository. Defaults to the fixture repository.
        customer_id: Optional known customer id.
        order_id: Optional known order id.

    Returns:
        The structured triage recommendation.
    """
    resolved_settings = settings or get_settings()
    inference = create_inference_client(resolved_settings)
    agent = build_triage_agent(inference=inference, repo=repo, settings=resolved_settings)
    try:
        return await run_triage(
            agent,
            issue,
            customer_id=customer_id,
            order_id=order_id,
        )
    finally:
        await inference.aclose()
