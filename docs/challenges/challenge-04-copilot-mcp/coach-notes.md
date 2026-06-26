# Challenge 04 · Coach notes

Trainer companion for [Copilot coding agent + a custom MCP server](README.md).

## Timing (60 min)

| Min | Segment | Focus |
| --- | --- | --- |
| 0–10 | Why MCP | Frame the problem: agents need **discoverable, typed, governed** tools, not bespoke glue. |
| 10–20 | Tour + verify | Walk the repo; run the quality gates so everyone has a green baseline. |
| 20–30 | Run + inspect | Start stdio; use the Inspector to call `get_order`. Make the protocol tangible. |
| 30–45 | Discovery + Copilot | Wire `.vscode/mcp.json`; have Copilot triage order 1001 live. This is the "wow". |
| 45–55 | Security model | Read the live path together; prove "no keys"; flip to `live:`. |
| 55–60 | Debrief | Discussion questions; preview Challenge 05 (the agent that owns this loop). |

## Key teaching points

- **MCP is a contract, not a library.** Tools are described once (name, schema, docstring) and any compliant
  client — Copilot today, our Python agent tomorrow — can discover and call them. Show `list_tools` output.
- **Pure core, thin edges.** Tool logic lives in `tools.py` as plain async functions returning dicts; the
  server is a thin registration layer. That is why behaviour is unit-tested without a network or a server.
- **Two backends, one protocol.** `build_repository(settings)` returns fixtures or the live Azure path. The
  agent never knows which — swapping is configuration. This mirrors the modular-inference idea in Challenge 05.
- **Governed by construction.** Read-only tools, a single documented egress, managed-identity auth, and Key
  Vault for secrets mean "point it at prod" is a defensible statement, not a risk.
- **Structured output matters.** Tools return typed JSON (`found` + fields, or `error`). Agents reason far
  better over structure than prose.

## Common pitfalls + fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `uv run` rebuilds / errors on first run | No `uv.lock` resolved yet | Run `uv sync` once; the lock is committed, so this is fast. |
| Inspector shows no tools | Pointed at the wrong module | Use `uv run mcp dev src/contoso_orders_mcp/__main__.py`. |
| Copilot ignores the server | `.vscode/mcp.json` not at the **repo root**, or window not reloaded | Copy the sample to the root and reload VS Code. |
| `ImportError: aiohttp` when touching the live path | `azure-identity` aio transport is lazy | It is already a declared dependency; re-run `uv sync`. |
| "Where are the keys?" confusion | Expectation of a connection string | There are none — show `DefaultAzureCredential` + `get_token(scope)`. |

## Discussion questions

- What stops a malicious or confused agent from **mutating** an order through this server? (Read-only surface.)
- The live path trusts a managed identity. **What exactly is that identity allowed to do**, and who grants it?
- Fixtures vs live is a config flip. What are the **risks** of that pattern, and how do you guard them
  (env validation, separate identities per environment, network policy)?
- When should a capability be an **MCP tool** vs. an in-process function in the agent? (Reuse, isolation,
  language independence, blast-radius.)

## What good looks like

- A learner can start the server, list its tools, and explain each argument and return shape without notes.
- Copilot completes a triage by calling **two** tools and **citing** their output — no hallucinated order ids.
- The learner points to the precise lines proving keyless auth and names the single egress target.
- Quality gates stay green after the stretch tool is added.

## Cross-dependencies

- Consumes the OIDC + dev-container foundation from **Challenge 00**.
- The server is the live tool backend for the agent in **Challenge 05**.
- Custom Copilot agents/skills under `.github/agents/` and `.github/prompts/` (other workstreams) can target
  this same server; the discovery contract is identical.
