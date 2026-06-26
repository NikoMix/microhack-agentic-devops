"""Configuration for the Orders MCP server.

All settings come from environment variables (prefix ``ORDERS_MCP_``) so the same
image runs unchanged across local stdio and hosted streamable-HTTP modes. The
egress + secret model is intentionally explicit:

* **No keys.** When a live ``api_base_url`` is configured, the server calls the
  downstream Orders API with a **bearer token from a managed identity**
  (``DefaultAzureCredential``), scoped by ``api_scope``.
* **Key Vault.** Any configuration secret (e.g. a downstream connection string)
  is referenced by ``key_vault_uri`` and fetched at runtime via the same managed
  identity — never baked into the image or committed.
* **Egress allow-list.** The server only ever calls ``api_base_url``; document
  this single egress target in your network policy.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Transport(StrEnum):
    """Supported MCP transports."""

    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"


class ServerSettings(BaseSettings):
    """Typed settings for the Orders MCP server (env prefix ``ORDERS_MCP_``)."""

    model_config = SettingsConfigDict(
        env_prefix="ORDERS_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- transport / hosting -----------------------------------------------
    transport: Transport = Transport.STDIO
    host: str = "127.0.0.1"
    port: Annotated[int, Field(gt=0, le=65_535)] = 8080

    # ----- live Orders API egress (managed identity, no keys) ----------------
    api_base_url: str | None = None
    api_scope: str = "api://contoso-orders/.default"
    request_timeout_seconds: Annotated[float, Field(gt=0)] = 15.0

    # ----- secrets via Key Vault (resolved at runtime, never committed) ------
    key_vault_uri: str | None = None

    # ----- diagnostics --------------------------------------------------------
    log_level: str = "INFO"

    @property
    def live_mode(self) -> bool:
        """True when a downstream Orders API is configured (else fixtures)."""
        return bool(self.api_base_url)

    def describe(self) -> str:
        """A redaction-safe one-line description of the active configuration."""
        backend = f"live:{self.api_base_url}" if self.live_mode else "fixtures"
        return f"transport={self.transport.value} backend={backend}"


@lru_cache(maxsize=1)
def get_settings() -> ServerSettings:
    """Return process-wide settings (cached). Tests construct ``ServerSettings`` directly."""
    return ServerSettings()
