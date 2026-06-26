# Challenge 00 — Coach notes

Foundation challenge. Everything downstream depends on a working OIDC trust and a deployed landing zone,
so **do not let attendees leave this challenge half-finished**. Budget a checkpoint at the 30-minute mark.

## Timing (45 min)

| Min | Segment | Notes |
| --- | --- | --- |
| 0–5 | Dev container + context | Get everyone into the container; explain "control plane" RA. |
| 5–15 | OIDC bootstrap | Run `setup-oidc.*`; whiteboard the token exchange while it runs. |
| 15–20 | Publish IDs | `gh secret set`; clarify IDs vs. secrets. |
| 20–25 | Read the Bicep | Walk `main.bicep` top-to-bottom; highlight AVM + RBAC, zero secrets. |
| 25–35 | what-if + deploy | Preview, discuss the change list, deploy. |
| 35–45 | Verify keyless + Q&A | Role assignments, empty Key Vault, outputs. |

## Key teaching points

- **OIDC = short-lived, audience-bound tokens.** GitHub mints a JWT describing the workflow
  (`repo:OWNER/REPO:ref:refs/heads/...`); Entra trusts it via a *federated credential* and returns an
  Azure access token. Nothing long-lived is stored — contrast with the old "create an SP, paste its client
  secret into a repo secret, rotate forever" pattern.
- **The federated subject is the security boundary.** Whoever can run a workflow on the matching ref/env
  can assume the identity. Scope the subject as tightly as the lab allows.
- **AVM modules are the unit of reuse.** `br/public:avm/res/...` modules encode Microsoft's
  Well-Architected defaults (diagnostics, RBAC, private-networking hooks). We pin exact versions for
  reproducibility and run `az bicep lint` clean.
- **Two distinct identities, by design.** The Entra **app registration `id-ccmh-deploy`** (deploy identity,
  control plane) vs. the **user-assigned managed identity `id-ccmh-lab`** (runtime workload identity, data
  plane). They are deliberately named differently so the control-plane vs. data-plane split is obvious —
  drill this, it confuses people for the rest of the day otherwise.
- **Keyless by construction.** App Insights and Foundry set `disableLocalAuth: true`; Key Vault is RBAC
  mode; access is granted to the managed identity, not to a connection string.

## Common pitfalls + fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `AADSTS700016` / `AADSTS70021` on `azure/login` | Federated credential subject doesn't match the workflow ref/env | `az ad app federated-credential list`; ensure subject = `repo:OWNER/REPO:ref:refs/heads/<branch>` (or `:environment:lab`). |
| Bootstrap fails creating the role assignment | Caller lacks `Owner`/`User Access Administrator` | Have a subscription owner run the role-assignment step, or pre-create the assignment. |
| `what-if` errors `ResourceGroupNotFound` | Skipped `--create-rg` | Re-run bootstrap with `--create-rg` or `az group create -n rg-ccmh-lab -l swedencentral`. |
| Foundry account name conflict (`already exists`) | `customSubDomainName` must be globally unique | The template appends a deterministic `rand` suffix from the RG id — ensure the RG name/region matches the lab. |
| Quota error on the Foundry deployment | Subscription lacks `gpt-4o-mini` capacity in the region | Switch region (`westeurope`/`eastus2`) in `main.bicepparam` or lower the deployment capacity. |
| `az bicep` not found in CI | Old `az` | The dev container ships a current `az`; on hosted runners `az bicep` is bundled. |

## Discussion questions

1. What exactly is in the OIDC token GitHub sends, and which claims does Entra validate?
2. When would you scope the federated credential to an **environment** vs. a **branch**? What protection
   does each give?
3. Why grant roles to a **managed identity** rather than storing a Key Vault connection string in the app?
4. The landing zone is RG-scoped. What changes if you needed subscription-scoped resources (e.g. a
   policy assignment or a second RG)?
5. How does pinning AVM module versions help reproducibility — and what's the upgrade story?

## What good looks like

- `az ad app federated-credential list` shows a credential whose subject matches the repo/branch (or
  environment), and the three IDs are set as repo secrets.
- `what-if` shows a clean **Create** plan with no warnings; `az bicep lint` is silent.
- The deployment succeeds and `properties.outputs` exposes the managed identity, Key Vault, ACR, Container
  Apps environment, and Foundry endpoints used by Challenges 02–06.
- `az role assignment list --assignee <MI principal>` shows exactly the five least-privilege roles — no
  `Owner`, no `Contributor` on the managed identity.
- Attendees can articulate the difference between the deploy identity and the workload identity.

## Links

- Student lab: [`README.md`](README.md)
- Landing zone + module table: [`../../../infra/README.md`](../../../infra/README.md)
- OIDC bootstrap (read-only reference): `scripts/bootstrap/setup-oidc.sh` / `.ps1`
- Deploy workflow: [`../../../.github/workflows/infra-deploy.yml`](../../../.github/workflows/infra-deploy.yml)
