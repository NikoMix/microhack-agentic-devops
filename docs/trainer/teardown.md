# Teardown & cost hygiene

Leaving cloud resources running is the #1 post-event complaint. Treat teardown as part of the craft and run it
**with the room** at 17:00. This page is the trainer reference; attendees follow the scripted steps.

## The one-command path

From the repo root, inside the dev container / Codespace:

```bash
# Bash (Linux/macOS/Codespaces)
./scripts/teardown/teardown.sh --resource-group rg-ccmh-lab --yes
```

```powershell
# PowerShell (Windows)
./scripts/teardown/teardown.ps1 -ResourceGroup rg-ccmh-lab -Yes
```

The script:

1. Confirms the **subscription + resource group** you're about to delete (prints them, asks to confirm unless `--yes`).
2. Deletes the **resource group** (`az group delete`) — this removes Container Apps, ACR, Key Vault, Log
   Analytics, App Insights, managed identity, and any runners' infra in that RG.
3. Optionally **purges** soft-deleted Key Vaults and Cognitive Services / Foundry accounts (`--purge`) so names
   are reusable immediately and you stop incurring soft-delete retention.
4. Optionally removes the **GitHub OIDC federated credentials** + app registration created in Challenge 00
   (`--remove-oidc`), so nothing dangling remains in Entra ID.

## What to verify after teardown

```bash
az group exists -n rg-ccmh-lab          # -> false
az keyvault list-deleted -o table       # ensure no lingering soft-deleted vaults you care about
az ad app list --display-name ccmh -o table   # if you used --remove-oidc, expect empty
```

On GitHub, also confirm any **self-hosted runners** registered in Challenge 02 are removed:
`Settings → Actions → Runners` (or `gh api`); the VMSS/ARC infra is gone with the RG, but the registration
entries should be deregistered by the script or removed manually.

## Per-resource cost notes (why these SKUs)

| Resource | SKU chosen | Why | Idle cost |
|---|---|---|---|
| Azure Container Apps | Consumption | Scales to zero | ~£0 when idle |
| Azure Container Registry | Basic | Cheapest registry that supports tasks | small/day |
| Key Vault | Standard | No HSM needed for the lab | negligible |
| Log Analytics | PAYG + daily cap | Bounds ingestion cost | low |
| Application Insights | Workspace-based | Reuses Log Analytics cap | low |
| Runners (VMSS) | B-series / Spot | Cheapest burstable; spot for extra savings | **only while running** |
| Azure AI Foundry / OpenAI | Pay-per-token | No always-on cost | **only on use** |

> The dominant *avoidable* cost is **runners left running** and **soft-delete retention** on Key Vault /
> Cognitive Services. The teardown script handles both.

## If an attendee can't run teardown

- Have them share their subscription + RG name with a coach; run the script on their behalf.
- Or, in the Portal: **Resource groups → `rg-ccmh-lab` → Delete resource group**.
- Set a **budget alert** at the start of the day as a backstop (the bootstrap script offers to create one).

## Trainer end-of-day checklist

- [ ] Every attendee's `rg-ccmh-lab` reports `false` from `az group exists`.
- [ ] No unexpected soft-deleted Key Vaults / Cognitive Services left accruing retention.
- [ ] Self-hosted runners deregistered from the GitHub repo/org.
- [ ] OIDC app registrations removed (if you don't plan to reuse them).
- [ ] Budget alert reviewed — confirm spend is within the expected per-attendee envelope.
