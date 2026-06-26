# Contoso Orders MCP server

A small, **Azure-facing [Model Context Protocol](https://modelcontextprotocol.io) server** that exposes
safe, read-only order tools to the Order Support agent (and to the GitHub Copilot coding agent during
development). It is the live data plane behind Challenge&nbsp;04.

/ It ships with deterministic fixtures so it runs offline with zero configuration, and a managed-identity
"live" path for talking to a real downstream Orders API — **no API keys, ever**.

## Tools

| Tool | Arguments | Returns |
| --- | --- | --- |
| `get_order` | `order_id: str` | Order status, carrier, tracking, line items and `total`. |
| `lookup_inventory` | `sku: str` | Stock `available`/`reserved` and computed `sellable` units. |
| `get_order_history` | `customer_id: str`, `limit: int = 10` | A customer's recent orders, newest first. |

All tools are **read-only** and return structured JSON (a `found` flag plus typed fields, or an `error`
message). There is **no image generation** and no write/mutating tool surface.

## Architecture

```text
Agent / Copilot ──MCP──▶ FastMCP server ──▶ OrderRepository
                                              ├─ InMemoryOrderRepository  (packaged fixtures, default)
                                              └─ AzureOrdersRepository     (live: managed identity → Orders API)
```

`build_repository(settings)` selects the backend from configuration, so swapping fixtures for the live API
is a **deployment change, not a code change**. Tool logic lives in `tools.py` as pure async functions and is
unit-tested without any server or network.

## Egress + secret model

This server is deliberately explicit about what it can reach and how it authenticates:

- **No keys.** The live backend authenticates to the downstream Orders API with a **bearer token from a
  managed identity** (`DefaultAzureCredential`), scoped by `ORDERS_MCP_API_SCOPE`. No secrets are stored in
  the image, in environment variables, or in source.
- **Key Vault for any secret.** If a configuration secret is ever required, it is referenced by
  `ORDERS_MCP_KEY_VAULT_URI` and fetched at runtime via the same managed identity — never committed.
- **Single egress target.** The only outbound host is `ORDERS_MCP_API_BASE_URL`. Document that one target in
  your network policy / NSG and deny everything else. With fixtures (the default) there is **no egress at all**.
- **Least privilege.** The managed identity (`id-ccmh-lab`) needs only the app-role/scope required to read
  orders and inventory — nothing more.

## Configuration

All settings use the `ORDERS_MCP_` prefix (see `.env.example`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `ORDERS_MCP_TRANSPORT` | `stdio` | `stdio`, `sse`, or `streamable-http`. |
| `ORDERS_MCP_HOST` | `127.0.0.1` | Bind host for HTTP transports. |
| `ORDERS_MCP_PORT` | `8080` | Bind port for HTTP transports. |
| `ORDERS_MCP_API_BASE_URL` | _(unset)_ | Downstream Orders API base URL. Unset ⇒ fixtures. |
| `ORDERS_MCP_API_SCOPE` | `api://contoso-orders/.default` | Token scope for the managed identity. |
| `ORDERS_MCP_REQUEST_TIMEOUT_SECONDS` | `15` | Per-request timeout for the live path. |
| `ORDERS_MCP_KEY_VAULT_URI` | _(unset)_ | Key Vault used for any runtime secret. |
| `ORDERS_MCP_LOG_LEVEL` | `INFO` | Log level. |

## Run it

```bash
uv sync

# Local stdio (how the agent / Copilot launches it)
uv run contoso-orders-mcp

# Hosted streamable-HTTP (Container Apps / remote discovery)
uv run contoso-orders-mcp --transport streamable-http --host 0.0.0.0 --port 8080
```

## Discovery for the Copilot coding agent

VS Code reads a workspace `.vscode/mcp.json`. A ready-to-use definition lives at
[`mcp/.vscode/mcp.json`](../.vscode/mcp.json); copy it to the **repository root** `.vscode/mcp.json` (or merge
its `servers` entry) so Copilot discovers the `contoso-orders` server and its tools. See
[`mcp/README.md`](../README.md) for the egress + secret model across all servers.

## Quality gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
uv run pip-audit
```

## Container

A multi-stage `Dockerfile` builds a non-root image that runs the server over streamable-HTTP. The image
carries **no secrets**; at runtime it relies on the Container Apps managed identity for any Azure access.

```bash
docker build -t contoso-orders-mcp .
docker run --rm -p 8080:8080 -e ORDERS_MCP_TRANSPORT=streamable-http -e ORDERS_MCP_HOST=0.0.0.0 contoso-orders-mcp
```
