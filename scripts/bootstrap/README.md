# Bootstrap scripts

One-time setup for the MicroHack lab. Run from a logged-in shell (`az login`, and `gh auth login` if you want the
script to set GitHub secrets for you). Both the Bash and PowerShell versions are equivalent and **idempotent** —
re-running them is safe.

## `setup-oidc.sh` / `setup-oidc.ps1`

Wires **GitHub ↔ Entra ID ↔ Azure** with **OIDC federated credentials** so Actions and Codespaces can obtain
Azure tokens **without any stored client secret**. This backs Challenge 00.

What it does (idempotently):

1. Creates an **Entra ID app registration** + **service principal** (default name `id-ccmh-lab`).
2. Adds **federated credentials** for your repo's default branch, pull requests, and (optionally) an environment.
3. Optionally creates the **resource group**, registers required **resource providers**, and creates a **budget alert**.
4. Assigns a **least-privilege role** (`Contributor` by default) **scoped to the resource group** only.
5. Prints — and optionally sets via `gh` — the three values your workflows need:
   `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.

### Usage

```bash
# Bash
./setup-oidc.sh \
  --repo <your-org>/microhack-agentic-devops \
  --create-rg --register-providers \
  --budget 20 \
  --set-gh-secrets
```

```powershell
# PowerShell
./setup-oidc.ps1 `
  -Repo '<your-org>/microhack-agentic-devops' `
  -CreateRg -RegisterProviders `
  -Budget 20 `
  -SetGhSecrets
```

### Key options

| Bash | PowerShell | Default | Purpose |
| --- | --- | --- | --- |
| `--repo` | `-Repo` | *(required)* | `owner/repo` the federated credentials trust |
| `--app-name` | `-AppName` | `id-ccmh-lab` | Entra app registration name |
| `--resource-group` | `-ResourceGroup` | `rg-ccmh-lab` | Scope for the role assignment |
| `--location` | `-Location` | `swedencentral` | Region for `--create-rg` |
| `--role` | `-Role` | `Contributor` | Role assigned at RG scope |
| `--branch` | `-Branch` | `main` | Branch subject for the federated credential |
| `--environment` | `-Environment` | *(none)* | Adds an environment-scoped credential |
| `--create-rg` | `-CreateRg` | off | Create the resource group |
| `--register-providers` | `-RegisterProviders` | off | Register required RPs |
| `--budget <gbp>` | `-Budget <gbp>` | *(none)* | Create a monthly budget alert |
| `--set-gh-secrets` | `-SetGhSecrets` | off | Set the 3 secrets via `gh` |

> **Security note:** no client secret is ever created. The trust is entirely OIDC + federated identity. If you
> tighten the role to less than `Contributor`, make sure it still allows the resources each challenge deploys
> (Container Apps, ACR, Key Vault, Log Analytics, Cognitive Services).

When you're done with the event, clean everything up with [`../teardown/`](../teardown/).
