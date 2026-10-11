# Azure Key Vault — runtime secret storage (no secrets in git)

Key Vault is where the lab keeps the few real runtime secrets it needs (for example an inference API key when
running against a keyed provider). Code reads them at runtime with **`DefaultAzureCredential`** over **Entra ID
RBAC** — there are no connection strings, account keys, or `.env` files with live values anywhere in the repo.

> This is the runtime complement to [Secret Protection](secret-protection.md): the reason the repo rarely trips
> secret scanning is that there is nothing to commit — identity is OIDC, secrets live here.

## Principles

- **RBAC, not access policies.** Use the Key Vault **RBAC** permission model and assign least-privilege roles to
  identities, not vault-wide access policies.
- **Managed identity at runtime.** The Container App uses a **user-assigned managed identity** (`id-ccmh-lab`);
  locally, the developer's `az login` identity is used — the *same code* via `DefaultAzureCredential`.
- **Reference, do not copy.** Container Apps pulls secrets via a **Key Vault reference**, so the secret value is
  never baked into image, manifest, or env file.

## 1. Provision a vault (RBAC enabled, soft-delete + purge protection)

```bash
RG=rg-ccmh-lab
LOC=swedencentral
RAND=$(openssl rand -hex 3)          # keep the <rand> suffix in the lab naming convention
KV=kv-ccmh-${RAND}

az keyvault create \
  --name "$KV" --resource-group "$RG" --location "$LOC" \
  --enable-rbac-authorization true \
  --retention-days 7
echo "Vault: $KV"
```

`--enable-rbac-authorization true` is the important flag — it switches the vault to the Entra RBAC model.

## 2. Grant yourself the data-plane role, then store a secret

Ownership of the vault (control plane) does **not** grant secret access (data plane); you assign a data role.

```bash
KV_ID=$(az keyvault show --name "$KV" --query id -o tsv)
ME=$(az ad signed-in-user show --query id -o tsv)

# "Key Vault Secrets Officer" can set/read secrets; use "Secrets User" for read-only consumers
az role assignment create \
  --assignee-object-id "$ME" --assignee-principal-type User \
  --role "Key Vault Secrets Officer" --scope "$KV_ID"

# Store a sample runtime secret (value stays in Azure, never in git)
az keyvault secret set --vault-name "$KV" --name "inference-api-key" --value "<paste-at-runtime>"
```

## 3. Give the runtime identity read-only access

The Container App's managed identity needs only **Key Vault Secrets User** (read):

```bash
MI_PRINCIPAL=$(az identity show --name id-ccmh-lab --resource-group "$RG" --query principalId -o tsv)

az role assignment create \
  --assignee-object-id "$MI_PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" --scope "$KV_ID"
```

## 4. Read it from code — one credential, everywhere

`DefaultAzureCredential` resolves to the managed identity in Azure and to your `az login` locally, so the same
code runs in both places with **no secret in sight**.

```python
# Python (azure-identity, azure-keyvault-secrets — both MIT-licensed)
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = os.environ["AZURE_KEY_VAULT_URL"]  # e.g. https://kv-ccmh-ab12cd.vault.azure.net
client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
api_key = client.get_secret("inference-api-key").value
```

```csharp
// .NET (Azure.Identity, Azure.Security.KeyVault.Secrets — both MIT-licensed)
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;

var vaultUri = new Uri(Environment.GetEnvironmentVariable("AZURE_KEY_VAULT_URL")!);
var client = new SecretClient(vaultUri, new DefaultAzureCredential());
string apiKey = client.GetSecret("inference-api-key").Value.Value;
```

> The MicroHack defaults to **GitHub Models** / keyless **Azure OpenAI via Entra**, which need *no* API key at
> all. Key Vault is for the cases where a keyed provider is genuinely required — and even then the key lives
> here, not in code.

## 5. Container Apps secret reference (no value in the manifest)

Bind the app's env var to the vault secret via the managed identity — the value is resolved at runtime:

```bash
az containerapp secret set \
  --name ca-order-support --resource-group "$RG" \
  --secrets "inference-api-key=keyvaultref:https://${KV}.vault.azure.net/secrets/inference-api-key,identityref:/subscriptions/<sub>/resourcegroups/${RG}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-ccmh-lab"
```

## 6. Teardown notes

`az group delete` removes the vault, but **soft-delete** retains it (and its name) for the retention window. To
free the name immediately at end of day:

```bash
az keyvault purge --name "$KV" --location "$LOC"
```

The teardown script's `--purge` flag does this for you (see
[`docs/trainer/teardown.md`](../docs/trainer/teardown.md)).

## What good looks like

A secret exists **only** in Key Vault; the same `DefaultAzureCredential` code reads it locally and in Container
Apps; the runtime identity has **read-only** access scoped to the vault; and `git grep` for the secret value
returns nothing, because it was never committed.
