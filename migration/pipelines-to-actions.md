# Pipelines → Actions translation

How [`azure-pipelines.yml`](../src/legacy-orders-api/azure-pipelines.yml) (the "before") becomes
[`orders-api-ci.yml`](../.github/workflows/orders-api-ci.yml) (the "after"). GitHub Enterprise Importer
moves repositories, **not** pipelines — this translation is a deliberate step you own.

## Concept mapping

| Azure Pipelines | GitHub Actions | Notes |
| --- | --- | --- |
| `trigger:` / `pr:` | `on: push:` / `on: pull_request:` | Both scope to `paths:` so the workflow only runs for Orders changes |
| `stages:` → `jobs:` → `steps:` | `jobs:` → `steps:` | Actions has no `stages` layer; ordering is expressed with `needs:` |
| `dependsOn:` | `needs:` | `deploy` `needs: build-test` |
| `condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')` | `if: github.ref == 'refs/heads/main'` | Gate the deploy on `main` |
| `pool: { vmImage: ubuntu-latest }` | `runs-on: ubuntu-latest` | Same hosted image family |
| `variables:` | `env:` (+ repo/org `vars.*`) | Non-secret config moves to repository **Variables**, not secrets |
| Variable group / pipeline secrets | `secrets.*` / OIDC | Most "secrets" disappear entirely — replaced by OIDC federation |
| Service connection (ACR) | OIDC + `AcrPush` role | No stored registry credential |
| Service connection (ARM) | `azure/login` with OIDC | No stored service principal secret |
| `environment: ccmh-lab` (deployment job) | `environment: ccmh-lab` (job key) | GitHub Environments add reviewers + scoped variables |

## Task-by-task mapping

| # | Azure DevOps task | GitHub Actions equivalent |
| --- | --- | --- |
| 1 | `UseDotNet@2` | `actions/setup-dotnet@…` with `global-json-file:` |
| 2 | `DotNetCoreCLI@2` (`restore`) | `run: dotnet restore <solution>.slnx` |
| 3 | `DotNetCoreCLI@2` (`build`, `-warnaserror`) | `run: dotnet build … --no-restore -warnaserror` |
| 4 | `DotNetCoreCLI@2` (`test`, `publishTestResults: true`) | `run: dotnet test … --logger trx` + `actions/upload-artifact@…` |
| 5 | *(none — formatting was manual)* | `run: dotnet format --verify-no-changes` *(added: fails on drift)* |
| 6 | *(none — vuln scan was manual)* | `run: dotnet list package --vulnerable …` + `grep`/`exit 1` *(added)* |
| 7 | `Docker@2` (`buildAndPush`, registry service connection) | `run: az acr build …` over OIDC — no registry credential |
| 8 | `PublishBuildArtifacts@1` | `actions/upload-artifact@…` |
| 9 | `AzureCLI@2` (`azureSubscription` service connection) | `azure/login@…` (OIDC) + `run: az containerapp update …` |

> Steps 5 and 6 did not exist in the source pipeline. The migration is the moment to **add** the
> quality and security gates the contract requires (format check, vulnerable-package scan).

## The security upgrade (the real reason to migrate)

| Before (Azure DevOps) | After (GitHub Actions) |
| --- | --- |
| ACR **service connection** stores a registry credential | `az acr build` uses the federated identity's `AcrPush` role — **no credential** |
| ARM **service connection** stores a service principal secret | `azure/login` uses **OIDC** (`client-id`/`tenant-id`/`subscription-id`) — **no secret** |
| Pipeline token is broadly scoped | `permissions: contents: read` by default; `id-token: write` only on `deploy` |
| Tasks referenced by mutable major version (`@2`) | Every action **pinned to a full commit SHA** |
| Secrets live in variable groups | Non-secret config lives in repository **Variables** (`vars.*`) |

### Variables the "after" workflow expects

Set these as repository or **Environment** (`ccmh-lab`) **Variables** — all non-secret. They are
provisioned by Workstream B's landing zone (`/infra`); names follow the shared lab contract.

| Variable | Example | Purpose |
| --- | --- | --- |
| `AZURE_CLIENT_ID` | GUID of `id-ccmh-lab` | OIDC federated identity (also the deploy gate) |
| `AZURE_TENANT_ID` | GUID | Entra tenant |
| `AZURE_SUBSCRIPTION_ID` | GUID | Target subscription |
| `ACR_NAME` | `crccmhlab<rand>` | Azure Container Registry |
| `ACA_NAME` | `ca-ccmh-orders-api` | Container App to update |
| `AZURE_RESOURCE_GROUP` | `rg-ccmh-lab` | Resource group |

The `deploy` job is gated on `vars.AZURE_CLIENT_ID != ''`, so **build + test + scan run in any fork**
while the Azure deploy only runs once these variables exist.

## Validate the translation locally

```bash
# Lint the workflow the way CI does
actionlint .github/workflows/orders-api-ci.yml

# Prove the build/test/scan steps pass
dotnet build  src/legacy-orders-api/Contoso.Orders.slnx -c Release -warnaserror
dotnet test   src/legacy-orders-api/Contoso.Orders.slnx -c Release
dotnet list   src/legacy-orders-api/src/Contoso.Orders.Api/Contoso.Orders.Api.csproj package --vulnerable --include-transitive
```
