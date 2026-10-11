"""FastAPI surface for the Order Support / Triage agent.

The same modular-inference agent that powers the CLI is exposed over HTTP so it
can be deployed to **Azure Container Apps** with real ingress and health probes:

* ``GET  /healthz`` — liveness (process is up); never touches a provider.
* ``GET  /readyz``  — readiness (the agent built successfully for the configured
  provider). Returns ``503`` until the inference client is ready.
* ``POST /triage``  — triage a customer issue and return a structured
  :class:`~order_support_agent.models.TriageRecommendation`.

The inference client is built once at startup and reused across requests, then
closed on shutdown. HTTP requests are traced to Application Insights when Azure
Monitor is configured (``opentelemetry-instrumentation-fastapi`` is auto-wired
by ``azure-monitor-opentelemetry``).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from order_support_agent.agent.triage_agent import TriageError, build_triage_agent, run_triage
from order_support_agent.config import Settings, get_settings
from order_support_agent.inference.errors import InferenceConfigurationError
from order_support_agent.inference.factory import create_inference_client
from order_support_agent.models import TriageRecommendation, TriageRequest
from order_support_agent.telemetry import setup_telemetry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from agent_framework import Agent

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "0.0.0.0"  # noqa: S104 - container ingress binds all interfaces by design
_DEFAULT_PORT = 8000


def create_app(*, settings: Settings | None = None, agent: Agent | None = None) -> FastAPI:
    """Build the FastAPI application.

    Args:
        settings: Configuration. Defaults to :func:`get_settings`.
        agent: A pre-built agent (used by tests with a fake provider). When
            omitted, the agent is built at startup from ``settings`` and its
            inference client is closed on shutdown.

    Returns:
        A configured :class:`fastapi.FastAPI` app.
    """
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        setup_telemetry(resolved_settings)
        owned_inference = None
        app.state.settings = resolved_settings
        try:
            if agent is not None:
                app.state.agent = agent
            else:
                owned_inference = create_inference_client(resolved_settings)
                app.state.agent = build_triage_agent(
                    inference=owned_inference, settings=resolved_settings
                )
        except InferenceConfigurationError:
            logger.exception("Inference provider misconfigured; service starts unready.")
            app.state.agent = None
        try:
            yield
        finally:
            if owned_inference is not None:
                await owned_inference.aclose()

    app = FastAPI(
        title="Contoso Order Support Agent",
        version="0.1.0",
        summary="Triages a Contoso Commerce order issue and returns a recommendation.",
        lifespan=lifespan,
    )

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        """Liveness probe — the process is running."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["health"])
    async def readyz(request: Request) -> JSONResponse:
        """Readiness probe — the agent is built for the configured provider."""
        ready_agent = getattr(request.app.state, "agent", None)
        if ready_agent is None:
            return JSONResponse({"status": "unready"}, status_code=503)
        active: Settings = request.app.state.settings
        return JSONResponse({"status": "ready", "config": active.describe()})

    @app.post("/triage", tags=["triage"])
    async def triage(request: Request, body: TriageRequest) -> TriageRecommendation:
        """Triage a customer issue and return a structured recommendation."""
        ready_agent = getattr(request.app.state, "agent", None)
        if ready_agent is None:
            raise HTTPException(status_code=503, detail="Inference provider not configured.")
        try:
            return await run_triage(
                ready_agent,
                body.issue,
                customer_id=body.customer_id,
                order_id=body.order_id,
            )
        except TriageError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


app = create_app()


def run() -> None:
    """Entry point for ``order-support-agent-serve`` and the container CMD."""
    import uvicorn

    host = os.environ.get("HOST", _DEFAULT_HOST)
    port = int(os.environ.get("PORT", str(_DEFAULT_PORT)))
    uvicorn.run("order_support_agent.service:app", host=host, port=port, log_level="info")


if __name__ == "__main__":  # pragma: no cover - module CLI shim
    run()
