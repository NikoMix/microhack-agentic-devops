# Migration runbook — Azure DevOps → GitHub

Everything Challenge 01 needs to move the **Contoso Orders** service off Azure DevOps and onto
GitHub + Azure: **Repos → GitHub repositories**, **Pipelines → GitHub Actions**, and
**Boards → GitHub Issues**, with **OIDC** replacing every stored credential afterwards.

> **No source organization? No problem.** Every step has an **offline `--dry-run` path** that runs
> against the bundled [`sample-export/`](sample-export/). You can complete the whole lab with nothing
> but `gh`, `jq`, and this folder.

## Contents

| Path | What it is |
| --- | --- |
| [`scripts/migrate-repo.sh`](scripts/migrate-repo.sh) · [`.ps1`](scripts/migrate-repo.ps1) | Wrap GitHub Enterprise Importer to migrate one repo (with `--dry-run`) |
| [`scripts/boards-to-issues.sh`](scripts/boards-to-issues.sh) · [`.ps1`](scripts/boards-to-issues.ps1) | Recreate Azure Boards work items as GitHub Issues (with `--dry-run`) |
| [`scripts/common.sh`](scripts/common.sh) · [`.ps1`](scripts/common.ps1) | Shared logging + mapping helpers |
| [`pipelines-to-actions.md`](pipelines-to-actions.md) | Task-by-task Pipelines → Actions mapping table |
| [`boards-to-issues.md`](boards-to-issues.md) | Boards → Issues field mapping + approach |
| [`sample-export/`](sample-export/) | A self-contained ADO export (boards, pipeline, repo README) |

The translated workflow (the "after") lives at
[`.github/workflows/orders-api-ci.yml`](../.github/workflows/orders-api-ci.yml). The "before" pipeline
it was translated from is [`src/legacy-orders-api/azure-pipelines.yml`](../src/legacy-orders-api/azure-pipelines.yml).

## What GitHub Enterprise Importer moves (and what it doesn't)

GitHub Enterprise Importer (GEI) is delivered as two GitHub CLI extensions:

- **`gh gei`** — the umbrella importer (GitHub-to-GitHub and Azure DevOps sources).
- **`gh ado2gh`** — the Azure DevOps specialization. Adds `generate-script` (bulk), `rewire-pipeline`,
  team creation, and Boards integration. The official ADO runbook uses this one.

GEI migrates **Git repositories** (history, branches, tags, PRs, and more). It does **not** translate
**Pipelines** or move **Boards** — those are deliberate, opinionated steps you own (and the reason this
runbook exists). See the upstream limits in the GitHub docs before a production run.

## Prerequisites

```bash
# GitHub CLI + the two importer extensions
gh --version
gh extension install github/gh-gei
gh extension install github/gh-ado2gh

# jq is used by the Boards → Issues Bash script (the dev container ships it)
jq --version
```

### Personal access tokens (the only credentials, and they're short-lived)

GEI needs two PATs, exported as environment variables. Create them with a **7-day expiry**, use them,
then delete them. They never get committed and they are not needed after the migration — the running
service authenticates to Azure with **OIDC**, not PATs.

| Token | Env var | Required scopes |
| --- | --- | --- |
| Azure DevOps PAT | `ADO_PAT` | **Code** (Read), **Project and Team** (Read), **Work Items** (Read), **Graph** (Read) |
| GitHub PAT (classic) | `GH_PAT` | **repo**, **admin:org**, **workflow** |

```bash
export ADO_PAT="<azure-devops-pat>"   # paste at the prompt; do not hardcode
export GH_PAT="<github-pat>"          # paste at the prompt; do not hardcode
```

> In Azure DevOps, also enable **Organization settings → Policies → Third-party application access via
> OAuth** so GEI can read the source.

## Phase 1 — Repositories

### Trial run first

GEI has no delta sync, so always do a **trial run** into a throwaway `*-sandbox` org, validate, then run
the production migration with work halted.

### Bulk (recommended for a real org)

```bash
# Generate one migrate-repo command per repo, plus pipeline rewiring and Boards links.
gh ado2gh generate-script --ado-org "$ADO_ORG" --github-org "$GH_ORG" --all --output migrate.ps1
# Review migrate.ps1, then run it with pwsh.
pwsh ./migrate.ps1
```

### Single repo (what the lab uses)

```bash
# Bash
./scripts/migrate-repo.sh \
  --ado-org "$ADO_ORG" --ado-team-project Orders --ado-repo orders-api \
  --github-org "$GH_ORG" --github-repo orders-api
```

```powershell
# PowerShell
./scripts/migrate-repo.ps1 `
  -AdoOrg $env:ADO_ORG -AdoTeamProject Orders -AdoRepo orders-api `
  -GithubOrg $env:GH_ORG -GithubRepo orders-api
```

### Offline dry-run (no source org needed)

```bash
./scripts/migrate-repo.sh \
  --ado-org contoso --ado-team-project Orders --ado-repo orders-api \
  --github-org "$GH_ORG" --github-repo orders-api --dry-run
```

The dry run validates your prerequisites and prints the exact `gh gei migrate-repo` command without
calling anything.

## Phase 2 — Pipelines → Actions

GEI does not convert pipelines. Translate [`azure-pipelines.yml`](../src/legacy-orders-api/azure-pipelines.yml)
by hand (Copilot is excellent at the first draft) and compare against the finished
[`orders-api-ci.yml`](../.github/workflows/orders-api-ci.yml). The line-by-line mapping — and the
security wins (OIDC instead of service connections, least-privilege `permissions:`, SHA-pinned
actions) — are in **[`pipelines-to-actions.md`](pipelines-to-actions.md)**.

If you migrated with `gh ado2gh ... --all`, the importer also `rewire-pipeline`s the old ADO pipeline to
build from GitHub during a transition window. Retire it once Actions is green.

## Phase 3 — Boards → Issues

There is no first-party Boards importer, so we recreate work items as Issues from an export. The field
mapping and rationale are in **[`boards-to-issues.md`](boards-to-issues.md)**.

```bash
# Offline: print the plan from the bundled export (no API calls)
./scripts/boards-to-issues.sh --dry-run

# Live: create issues in a real repo from the bundled (or your own) export
./scripts/boards-to-issues.sh --repo "$GH_ORG/orders-api"
```

```powershell
./scripts/boards-to-issues.ps1 -DryRun
./scripts/boards-to-issues.ps1 -Repo "$env:GH_ORG/orders-api"
```

The script pre-creates the labels it maps to, sets the issue body with the original ADO metadata, and
closes issues whose source state was terminal (`Closed`/`Done`/`Removed`/`Resolved`).

## After the migration: kill the stored credentials

The whole point of the move is to delete long-lived secrets:

- **No registry credentials** — the workflow builds server-side with `az acr build` over the federated
  identity's `AcrPush` role.
- **No cloud service principal secret** — `azure/login` uses **GitHub OIDC** (`client-id` / `tenant-id`
  / `subscription-id`, no client secret).
- **Least privilege** — the default `GITHUB_TOKEN` is read-only; `id-token: write` is granted only to
  the deploy job.
- **Delete the migration PATs** as soon as Phase 1–3 are done.

## Cleanup

- Delete the `ADO_PAT` / `GH_PAT` tokens in Azure DevOps and GitHub.
- Delete any `*-sandbox` trial organizations.
- Remove generated `migrate.ps1` scripts and downloaded migration logs.
