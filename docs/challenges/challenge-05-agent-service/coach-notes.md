# Challenge 05 · Coach notes

Trainer companion for [Build & deploy the Order Support agent](README.md).

## Timing (75 min)

| Min | Segment | Focus |
| --- | --- | --- |
| 0–10 | Architecture | One agent, one tool layer, three providers. Draw the factory on the board. |
| 10–25 | Run on GitHub Models | Everyone gets a green triage with just `GITHUB_TOKEN` — zero Azure cost. |
| 25–40 | Provider swap | Switch to Azure OpenAI / Foundry **keyless**. Prove "no code change". |
| 40–50 | Serve + contract | `/healthz` vs `/readyz` vs `/triage`; why readiness gates traffic. |
| 50–60 | Telemetry | Wire App Insights; find the triage span; discuss sensitive-data flag. |
| 60–75 | Deploy | OIDC + keyless ACR + Container Apps; review the workflow; discuss rollout. |

## Key teaching points

- **The factory is the whole point.** `INFERENCE_PROVIDER` selects the backend; feature code only ever sees
  the `InferenceClient` interface. GitHub Models and Foundry ride `azure-ai-inference`; Azure OpenAI rides the
  `openai` SDK — **all keyless** except the GitHub token. Switching is config.
- **Start cheap.** The default (`github_models`) needs only a `GITHUB_TOKEN`, so the room is productive before
  anyone touches Azure. Move to Azure providers only for the deploy.
- **Structured output.** The agent returns a Pydantic `TriageRecommendation`, not prose — that is what makes
  it composable into a pipeline (Challenge 06).
- **Readiness ≠ liveness.** `/readyz` stays 503 until the inference client is built; that is how Container
  Apps avoids routing to a cold instance. Show the difference live.
- **Keyless everywhere.** OIDC to Entra, `az acr login` for the registry, managed identity inside the app.
  There is no secret in the workflow — only **Variables**.
- **No image generation.** Inference is chat/text only, by contract.

## Common pitfalls + fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `budget limit` / 4xx on GitHub Models | Account Models budget exhausted | Use a different token, or demo with `--console` + the fake-provider tests. |
| Azure provider 401/403 | Not logged in / identity lacks role | `az login`; grant the identity **Cognitive Services OpenAI User** (AOAI) or the Foundry data-plane role. |
| `/triage` 503 | Hitting it before readiness | Wait for `/readyz` to return 200, then call `/triage`. |
| No traces in App Insights | Connection string unset, or `ENABLE_AZURE_MONITOR=false` | Set `APPLICATIONINSIGHTS_CONNECTION_STRING`; both must be on (`azure_monitor_enabled`). |
| Deploy fails at login | Federated credential subject mismatch | Federate `repo:NikoMix/microhack-agentic-devops:environment:lab`; set the `AZURE_*` Variables. |
| Deploy fails at `containerapp update` | App/RG/ACR names don't match infra | Align `AGENT_CONTAINERAPP`/`MCP_CONTAINERAPP`/`AZURE_RESOURCE_GROUP`/`ACR_NAME` with Workstream-B outputs. |

## Discussion questions

- Where would you **add a fourth provider** (e.g. a local model), and what is the smallest change set?
- The agent calls tools over MCP. What are the **trust boundaries** between agent, MCP server, and Azure?
- When is **min-replicas=0** the right call, and what does it cost you on the first request?
- What belongs in a **trace** vs. a **metric** for this agent, and what must never be logged
  (`ENABLE_SENSITIVE_TELEMETRY=false`)?

## What good looks like

- The same issue is triaged on two different providers with only an env change, and the learner can explain
  exactly which line selects the backend.
- The learner articulates the readiness/liveness split and why deploys depend on it.
- A triage trace is found in App Insights and read end-to-end (tool calls → model call → structured result).
- The deploy is **keyless** and the learner can point to where each identifier comes from (Variables, OIDC).

## Cross-dependencies

- **Challenge 04** provides the MCP tool backend (`ORDERS_MCP_URL`).
- **Workstream B (issue #5)** owns the landing zone the deploy targets — this challenge references its outputs
  by the shared naming contract and never edits `/infra`.
- **Workstream D** owns SDLC security scanning; the agent CI runs `pip-audit` locally as a fast guardrail.
