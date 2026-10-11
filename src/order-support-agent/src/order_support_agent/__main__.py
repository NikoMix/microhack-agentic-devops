"""Command-line entry point for the Order Support / Triage agent.

Examples:
    # Use the configured provider (default: github_models, needs only GITHUB_TOKEN)
    order-support-agent "My order 1001 never arrived"

    # Force a provider for a demo and emit console traces
    order-support-agent --provider azure_openai --console "Refund please" --order-id 1003
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from order_support_agent.agent import triage_once
from order_support_agent.config import InferenceProvider, Settings, get_settings
from order_support_agent.telemetry import setup_telemetry

_SAMPLE_ISSUE = "I ordered two espresso blends a week ago (order 1001) and nothing has arrived."
_SAMPLE_ORDER_ID = "1001"


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="order-support-agent",
        description="Triage a Contoso Commerce order issue and print a recommendation.",
    )
    parser.add_argument(
        "issue",
        nargs="?",
        help="The customer's free-text complaint. Omit to run the built-in sample.",
    )
    parser.add_argument("--order-id", help="A known order id to seed the lookup.")
    parser.add_argument("--customer-id", help="A known customer id to seed the lookup.")
    parser.add_argument(
        "--provider",
        choices=[p.value for p in InferenceProvider],
        help="Override INFERENCE_PROVIDER for this run (no code change required).",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Emit OpenTelemetry traces to the console when Azure Monitor is unset.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print only the recommendation as JSON (machine-readable).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def _resolve_settings(provider: str | None) -> Settings:
    """Return settings, optionally overriding the inference provider."""
    settings = get_settings()
    if provider:
        return settings.model_copy(update={"inference_provider": InferenceProvider(provider)})
    return settings


async def _run(args: argparse.Namespace) -> int:
    """Execute the triage flow and render the result."""
    settings = _resolve_settings(args.provider)
    setup_telemetry(settings, console=args.console)

    issue = args.issue or _SAMPLE_ISSUE
    order_id = args.order_id or (None if args.issue else _SAMPLE_ORDER_ID)

    if not args.json:
        sys.stderr.write(f"Triaging with {settings.describe()}\n")

    recommendation = await triage_once(
        issue,
        settings=settings,
        order_id=order_id,
        customer_id=args.customer_id,
    )

    if args.json:
        print(json.dumps(recommendation.model_dump(mode="json"), indent=2))
    else:
        print(recommendation.render())
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, configure logging and run the agent.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv``).

    Returns:
        A process exit code (0 on success, non-zero on failure).
    """
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        return 130


if __name__ == "__main__":  # pragma: no cover - module CLI shim
    raise SystemExit(main())
