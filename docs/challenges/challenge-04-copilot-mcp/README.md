# Challenge 04 · Copilot coding agent + a custom MCP server

You will use the **GitHub Copilot coding agent** and build a custom, **Azure-facing
[Model Context Protocol](https://modelcontextprotocol.io) (MCP) server** that exposes safe, governed tools
to that agent. This is the data plane the Order Support agent (Challenge 05) calls at runtime.

## Duration

60 minutes.

## Reference architecture

Architecture **3 — Agentic dev**. The Copilot coding agent (and, later, your own agent) discover tools over
MCP instead of hard-coding integrations. The server owns the egress + secret model so a tool call is always
governed.

```mermaid
flowchart LR
  subgraph Client["Client (VS Code)"]
    CG[Copilot coding agent]
  end
  subgraph Server["contoso-orders MCP server"]
    T1[get_order]
    T2[lookup_inventory]
    T3[get_order_history]
  end
  CG -- "MCP (stdio / streamable-http)" --> Server
  Server -->|fixtures (default)| FX[(Packaged JSON)]
  Server -.->|live: managed identity, no keys| API[(Orders API)]
  API -.-> KV[(Key Vault)]
```

## Learning objectives

By the end of this challenge you can:

- Explain what MCP is and **why** an agent should reach tools through it (typed, discoverable, governed).
- Run a custom MCP server locally over **stdio** and inspect its tools.
- Make the server discoverable to the **Copilot coding agent** via `.vscode/mcp.json`.
- Read and defend a concrete **egress + secret model**: managed identity, Key Vault, single egress,
  read-only, least privilege — **no keys**.
- Switch the server from packaged fixtures to a **live** backend with **zero code change**.

## Prerequisites

- Challenge 00 (OIDC + dev container) and Challenge 01 (repo in GitHub) complete.
- VS Code with the **GitHub Copilot** extension, signed in with coding-agent access.
- [`uv`](https://docs.astral.sh/uv/) installed (the dev container ships it). Python 3.12.
- Repository cloned; this challenge lives under [`mcp/`](../../../mcp/).

## Tasks

1. **Tour the server.** Read [`mcp/README.md`](../../../mcp/README.md) and
   [`mcp/contoso-orders-mcp/README.md`](../../../mcp/contoso-orders-mcp/README.md). Identify the three tools,
   their arguments, and the two backends (`InMemoryOrderRepository`, `AzureOrdersRepository`).
2. **Install + verify.** From `mcp/contoso-orders-mcp/`:

   ```bash
   uv sync
   uv run ruff check . && uv run mypy . && uv run pytest
   ```

   All gates should pass (20 tests).
3. **Run it (stdio).** Launch the server the way an agent does:

   ```bash
   uv run contoso-orders-mcp
   ```

   It starts on `stdio` and logs `transport=stdio backend=fixtures`. Stop it with `Ctrl+C`.
4. **Inspect the tools.** In another terminal, list and call tools with the MCP Inspector:

   ```bash
   uv run mcp dev src/contoso_orders_mcp/__main__.py
   ```

   Confirm `get_order`, `lookup_inventory`, `get_order_history` appear, then call `get_order` with
   `order_id = "1001"` and read the structured result.
5. **Make it discoverable.** Copy [`mcp/.vscode/mcp.json`](../../../mcp/.vscode/mcp.json) (or merge its
   `servers` entry) into the **repository-root** `.vscode/mcp.json`, reload VS Code, and confirm the
   `contoso-orders` server and its tools appear in the MCP view.
6. **Use it from Copilot.** Ask the Copilot coding agent to triage a stuck order — for example:
   *"Order 1001 hasn't moved in six days. Use the contoso-orders tools to check its status and the stock for
   its SKU, then recommend an action."* Watch it call `get_order` then `lookup_inventory` and ground its
   answer in the tool output.
7. **Read the security model.** In [`config.py`](../../../mcp/contoso-orders-mcp/src/contoso_orders_mcp/config.py)
   and [`repository.py`](../../../mcp/contoso-orders-mcp/src/contoso_orders_mcp/repository.py), find where the
   live path authenticates. Confirm there are **no API keys** — only `DefaultAzureCredential` + a scoped
   bearer token, with Key Vault for any secret. Set `ORDERS_MCP_API_BASE_URL` (a fake URL is fine) and observe
   `describe()` flip to `live:` — proof the swap is a **deployment** change, not a code change.

## Success criteria

- `uv run pytest` is green and `uv run ruff check .` / `uv run mypy .` are clean.
- The server runs over stdio and exposes exactly **three read-only tools**.
- The Copilot coding agent discovers the server via `.vscode/mcp.json` and calls at least two tools to
  answer a triage question.
- You can point to the exact lines that prove the live path uses a **managed identity and no keys**, and
  name the **single egress target**.

## Stretch goals

- Add a fourth read-only tool (e.g. `list_delayed_orders`) as a pure function in
  [`tools.py`](../../../mcp/contoso-orders-mcp/src/contoso_orders_mcp/tools.py) plus a thin `@server.tool`
  wrapper, with a unit test. Keep ruff/mypy green.
- Run the server over **streamable-HTTP** (`--transport streamable-http --host 0.0.0.0 --port 8080`) and
  register the URL for remote discovery.
- Write a one-paragraph network policy that allows only the server's single egress target and denies the rest.

## Cleanup

- Stop any running server (`Ctrl+C`).
- If you created a repository-root `.vscode/mcp.json` and don't want it committed, remove it or add it to your
  local ignore — it references only local commands and holds no secrets.
- No Azure resources are created in this challenge.
