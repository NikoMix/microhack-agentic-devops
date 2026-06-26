"""Contoso Commerce Orders MCP server.

A small, Azure-facing Model Context Protocol server exposing read-only order and
inventory tools. It is the live tool surface for the Order Support / Triage agent
and the subject of Challenge 04. Egress and secrets follow a managed-identity +
Key Vault model — see ``README.md``.
"""

from __future__ import annotations

__version__ = "0.1.0"
