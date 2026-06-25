# Teardown scripts

Run these at the **end of the day** (or any time you want to stop the meter). Both versions are equivalent. They
delete the ephemeral lab resource group and can also purge soft-deleted resources and remove the OIDC app.

See the trainer reference in [`../../docs/trainer/teardown.md`](../../docs/trainer/teardown.md) for the full
cost-hygiene checklist.

## `teardown.sh` / `teardown.ps1`

What they do:

1. **Confirm** the subscription + resource group (require you to type the RG name unless `--yes`/`-Yes`).
2. **Delete the resource group** — removes Container Apps, ACR, Key Vault, Log Analytics, App Insights, managed
   identity, and any runner infra in that RG.
3. *(optional)* **Purge** soft-deleted **Key Vaults** and **Cognitive Services / Foundry** accounts so names are
   reusable and retention stops.
4. *(optional)* **Remove the OIDC** Entra ID app registration (federated credentials go with it).
5. **Verify** the RG is gone.

### Usage

```bash
# Bash — interactive confirm
./teardown.sh --resource-group rg-ccmh-lab

# Bash — full clean, no prompts
./teardown.sh --resource-group rg-ccmh-lab --purge --remove-oidc --yes
```

```powershell
# PowerShell — full clean, no prompts
./teardown.ps1 -ResourceGroup rg-ccmh-lab -Purge -RemoveOidc -Yes
```

### Options

| Bash | PowerShell | Purpose |
| --- | --- | --- |
| `--resource-group` | `-ResourceGroup` | RG to delete (default `rg-ccmh-lab`) |
| `--subscription` | `-Subscription` | Target a specific subscription |
| `--purge` | `-Purge` | Purge soft-deleted Key Vaults / Cognitive Services |
| `--remove-oidc` | `-RemoveOidc` | Delete the Entra ID app registration (`id-ccmh-lab`) |
| `--app-name` | `-AppName` | Override the app-registration name to remove |
| `--no-wait` | `-NoWait` | Start RG deletion in the background (skips purge) |
| `--yes` / `-y` | `-Yes` | Skip the confirmation prompt |

> **Don't forget the runners.** The VMSS/ARC infra is deleted with the RG, but you should also **deregister**
> any self-hosted runners in **GitHub → Settings → Actions → Runners**. The script reminds you at the end.
>
> **Soft delete matters.** Key Vault and Cognitive Services keep paying retention after a plain RG delete. Use
> `--purge` to stop that and free the names immediately.
