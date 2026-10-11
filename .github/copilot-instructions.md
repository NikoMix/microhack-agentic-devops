# Copilot instructions — Contoso Commerce: Agentic DevOps MicroHack

This repository is a **1-day, classroom-led, Train-the-Trainer microhack** that teaches consultants how to
*deliver* an Agentic DevOps platform on **Azure + GitHub**. It maps to **Module B / control B.1.1** of the
Agentic DevOps Advanced Specialization. Keep everything **technical, hands-on, and reproducible**.

## Scenario

**Contoso Commerce** runs a legacy **.NET Orders API** on **Azure DevOps** (Repos/Pipelines/Boards). Across the
day, attendees **migrate it to GitHub**, **modernize it on Azure**, **secure the SDLC**, and add a new
**Python "Order Support / Triage" agent** built with **modular inference**.

## Golden rules

- **Security first:** never hardcode secrets/keys. Use **Entra ID + `DefaultAzureCredential`**, **Key Vault**,
  and **GitHub OIDC** (federated credentials) — no long-lived cloud secrets in Actions.
- **Latest stable, zero known vulns:** keep NuGet/PyPI/npm/Actions current. CI runs
  `dotnet list package --vulnerable`, `pip-audit`, `npm audit`, and dependency review.
- **License-safe:** only MIT/Apache/BSD/PSF dependencies. If none exists, build it ourselves.
- **No image generation** anywhere (inference is text/chat only).
- **Modular inference:** all AI calls go through the provider factory and honor `INFERENCE_PROVIDER`
  (`foundry` | `azure_openai` | `github_models`). Never call a single provider SDK directly from feature code.

## Tech & quality standards

| Area | Standard |
| --- | --- |
| .NET | `net10.0`, file-scoped namespaces, nullable enabled, warnings-as-errors, `dotnet format`, xUnit, Central Package Management |
| Python | 3.12, `uv`, `ruff` (lint+format), `mypy --strict`, `pytest`, `pyproject.toml` |
| IaC | **Bicep AVM modules** (`br/public:avm/res/...`), `az bicep lint` clean, `what-if` before deploy |
| Actions | OIDC login, least-privilege `permissions:`, **pin actions by commit SHA**, `actionlint`/`zizmor` clean, distinct filename prefix per workstream |
| Docs | Each `docs/challenges/challenge-XX-*/` has `README.md` (student) + `coach-notes.md` (trainer) |

## Modular inference env contract

```ini
INFERENCE_PROVIDER=github_models            # foundry | azure_openai | github_models
GITHUB_MODELS_ENDPOINT=https://models.github.ai/inference
GITHUB_MODELS_MODEL=openai/gpt-4o-mini
AZURE_OPENAI_ENDPOINT=...                    # keyless via Entra
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=...
AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT=gpt-4o-mini
```

> **Actions variable mapping & zero secrets:** GitHub Actions forbids `GITHUB_`-prefixed repository
> variables, so at the **workflow** layer the app's `GITHUB_MODELS_MODEL` is supplied via the repo variable
> **`GH_MODELS_MODEL`** (see `agentic-inference.yml`); the app/runtime layer still reads `GITHUB_MODELS_MODEL`.
> All Azure OIDC IDs (`AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID`) and lab settings are
> stored as repository **Variables**, never secrets — they are identifiers and the trust is OIDC federation,
> so the repo holds **zero secrets**.

## Azure naming (lab)

RG `rg-ccmh-lab` · prefix `ccmh` · region `swedencentral` (alts `westeurope`, `eastus2`) · ACR `crccmhlab<rand>` ·
ACA env `cae-ccmh-lab` · Key Vault `kv-ccmh-<rand>` · Log Analytics `log-ccmh-lab` · App Insights `appi-ccmh-lab` ·
Foundry `aif-ccmh-lab`/`proj-ccmh-lab` · workload **managed identity `id-ccmh-lab`** (data plane).

> The OIDC **deploy** app registration (control plane, created by `scripts/bootstrap/setup-oidc.*`) is a
> separate object named **`id-ccmh-deploy`** — keep it distinct from the `id-ccmh-lab` workload identity.

## Where things live

- `src/legacy-orders-api/` — .NET Orders API (migration subject)
- `src/order-support-agent/` — Python agent (Microsoft Agent Framework + modular inference)
- `mcp/` — custom MCP server(s)
- `infra/` — Bicep AVM landing zone + runners
- `.github/agents/`, `.github/prompts/` — Copilot custom agents + skills
- `docs/trainer/`, `docs/challenges/` — facilitator + student content

Always make labs work end-to-end and verify before claiming done. Clean up Azure resources with the teardown script.
