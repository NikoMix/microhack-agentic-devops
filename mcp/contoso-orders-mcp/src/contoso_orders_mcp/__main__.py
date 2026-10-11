"""Command-line entry point for the Contoso Orders MCP server.

Examples:
    # Local stdio (default) — how the agent / Copilot launches it
    contoso-orders-mcp

    # Hosted streamable-HTTP (for Container Apps / remote discovery)
    contoso-orders-mcp --transport streamable-http --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import argparse
import logging

from contoso_orders_mcp.config import ServerSettings, Transport, get_settings
from contoso_orders_mcp.server import create_server

logger = logging.getLogger("contoso_orders_mcp")


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the server CLI."""
    parser = argparse.ArgumentParser(
        prog="contoso-orders-mcp",
        description="Run the Contoso Commerce Orders MCP server.",
    )
    parser.add_argument(
        "--transport",
        choices=[transport.value for transport in Transport],
        help="Override ORDERS_MCP_TRANSPORT for this run.",
    )
    parser.add_argument("--host", help="Bind host for HTTP transports.")
    parser.add_argument("--port", type=int, help="Bind port for HTTP transports.")
    return parser


def _resolve_settings(args: argparse.Namespace) -> ServerSettings:
    """Apply CLI overrides on top of environment settings."""
    settings = get_settings()
    updates: dict[str, object] = {}
    if args.transport:
        updates["transport"] = Transport(args.transport)
    if args.host:
        updates["host"] = args.host
    if args.port:
        updates["port"] = args.port
    return settings.model_copy(update=updates) if updates else settings


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, configure logging and run the server.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv``).

    Returns:
        A process exit code (0 on success).
    """
    args = _build_parser().parse_args(argv)
    settings = _resolve_settings(args)
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    logger.info("Starting Contoso Orders MCP (%s)", settings.describe())
    server = create_server(settings=settings)

    match settings.transport:
        case Transport.STDIO:
            server.run(transport="stdio")
        case Transport.SSE:
            server.run(transport="sse")
        case Transport.STREAMABLE_HTTP:
            server.run(transport="streamable-http")
    return 0


if __name__ == "__main__":  # pragma: no cover - module CLI shim
    raise SystemExit(main())
