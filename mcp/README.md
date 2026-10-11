# MCP servers

Custom **[Model Context Protocol](https://modelcontextprotocol.io)** servers for the Contoso Commerce
microhack. MCP is how the Order Support agent (and the GitHub Copilot coding agent) discover and call
**typed, governed tools** instead of hard-coding integrations.

| Server | Path | Transport(s) | Purpose |
| --- | --- | --- | --- |
| `contoso-orders` | [`contoso-orders-mcp/`](contoso-orders-mcp/) | stdio · streamable-http | Safe, read-only order/inventory tools. |

## Egress + secret model (applies to every server here)

These servers are designed to be **safe to point at production data**:

- **No keys.** Live backends authenticate with a **managed identity** (`DefaultAzureCredential`) and send a
  short-lived bearer token. No API keys or connection strings are stored in images, env vars, or source.
- **Key Vault for any secret.** If a secret is ever required it is referenced by a Key Vault URI
  (`kv-ccmh-<rand>`) and fetched at runtime via the same managed identity — never committed.
- **Documented, minimal egress.** Each server declares exactly one outbound target (its downstream API base
  URL). Everything else is denied at the network layer. With the default fixtures there is **no egress at all**.
- **Read-only by design.** The tools never mutate state, so a compromised client cannot place, cancel, or
  alter orders.
- **Least privilege.** The identity (`id-ccmh-lab`) is granted only the role/scope needed to read orders and
  inventory.

See each server's own `README.md` for its specific configuration surface.

## Discovery for VS Code + the Copilot coding agent

VS Code (and the Copilot coding agent) read a workspace **`.vscode/mcp.json`**. A ready-to-use definition is
provided at [`.vscode/mcp.json`](.vscode/mcp.json) in this folder:

```jsonc
{
  "servers": {
    "contoso-orders": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--project", "${workspaceFolder}/mcp/contoso-orders-mcp", "contoso-orders-mcp"]
    }
  }
}
```

To enable discovery, **copy this file (or merge its `servers` entry) into the repository-root
`.vscode/mcp.json`** — VS Code resolves `${workspaceFolder}` to the repo root. Reload the window and the
`contoso-orders` server (and its tools) appear in the MCP view. The agent reaches the same tools at runtime
via the modular tool layer; MCP is the discovery + transport contract that keeps them interchangeable.

> Hosted option: run a server with `--transport streamable-http` (see its README) and register the URL
> instead of a `stdio` command for remote discovery from Container Apps.

This server is the live data plane for **Challenge 04** — see
[`docs/challenges/challenge-04-copilot-mcp/`](../docs/challenges/challenge-04-copilot-mcp/).
