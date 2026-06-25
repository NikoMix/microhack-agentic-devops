#!/usr/bin/env bash
#
# setup-oidc.sh — Bootstrap GitHub ↔ Entra ID ↔ Azure OIDC for the
# Contoso Commerce Agentic DevOps MicroHack (Challenge 00).
#
# Creates (idempotently):
#   * an Entra ID app registration + service principal
#   * federated credentials so GitHub Actions / Codespaces can get Azure tokens
#     WITHOUT any client secret
#   * a least-privilege role assignment scoped to the lab resource group
#   * (optional) the lab resource group, required resource providers, and a budget alert
#
# It then writes the three values you set as GitHub repo secrets/variables:
#   AZURE_CLIENT_ID · AZURE_TENANT_ID · AZURE_SUBSCRIPTION_ID
#
# No secrets are ever created or stored. Re-running is safe.
#
# Usage:
#   ./setup-oidc.sh \
#     --repo <owner>/<repo> \
#     [--app-name id-ccmh-lab] \
#     [--resource-group rg-ccmh-lab] \
#     [--location swedencentral] \
#     [--subscription <sub-id>] \
#     [--role Contributor] \
#     [--branch main] \
#     [--environment ""] \
#     [--create-rg] [--register-providers] [--budget <amount-gbp>] \
#     [--set-gh-secrets]
#
set -euo pipefail

# ---- defaults ---------------------------------------------------------------
APP_NAME="id-ccmh-lab"
RESOURCE_GROUP="rg-ccmh-lab"
LOCATION="swedencentral"
SUBSCRIPTION=""
ROLE="Contributor"
BRANCH="main"
ENVIRONMENT=""
REPO=""
CREATE_RG=false
REGISTER_PROVIDERS=false
BUDGET=""
SET_GH_SECRETS=false

PROVIDERS=(
  Microsoft.App
  Microsoft.ContainerRegistry
  Microsoft.KeyVault
  Microsoft.OperationalInsights
  Microsoft.Insights
  Microsoft.CognitiveServices
  Microsoft.ManagedIdentity
  Microsoft.Compute
  Microsoft.Network
)

# ---- helpers ----------------------------------------------------------------
log()  { printf '\033[0;36m▶ %s\033[0m\n' "$*"; }
ok()   { printf '\033[0;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[0;33m! %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[0;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

usage() { sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

# ---- parse args -------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)               REPO="$2"; shift 2;;
    --app-name)           APP_NAME="$2"; shift 2;;
    --resource-group)     RESOURCE_GROUP="$2"; shift 2;;
    --location)           LOCATION="$2"; shift 2;;
    --subscription)       SUBSCRIPTION="$2"; shift 2;;
    --role)               ROLE="$2"; shift 2;;
    --branch)             BRANCH="$2"; shift 2;;
    --environment)        ENVIRONMENT="$2"; shift 2;;
    --create-rg)          CREATE_RG=true; shift;;
    --register-providers) REGISTER_PROVIDERS=true; shift;;
    --budget)             BUDGET="$2"; shift 2;;
    --set-gh-secrets)     SET_GH_SECRETS=true; shift;;
    -h|--help)            usage;;
    *) die "Unknown argument: $1 (use --help)";;
  esac
done

command -v az >/dev/null || die "Azure CLI (az) is required."
[[ -n "$REPO" ]] || die "--repo <owner>/<repo> is required."
if $SET_GH_SECRETS; then command -v gh >/dev/null || die "GitHub CLI (gh) is required for --set-gh-secrets."; fi

# ---- context ----------------------------------------------------------------
log "Resolving Azure context…"
az account show >/dev/null 2>&1 || die "Not logged in. Run 'az login' first."
[[ -n "$SUBSCRIPTION" ]] && az account set --subscription "$SUBSCRIPTION"
SUB_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"
SUB_NAME="$(az account show --query name -o tsv)"
ok "Subscription: $SUB_NAME ($SUB_ID)"
ok "Tenant:       $TENANT_ID"

# ---- app registration + service principal -----------------------------------
log "Ensuring app registration '$APP_NAME'…"
APP_ID="$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)"
if [[ -z "$APP_ID" ]]; then
  APP_ID="$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)"
  ok "Created app registration ($APP_ID)"
else
  ok "App registration already exists ($APP_ID)"
fi

if ! az ad sp show --id "$APP_ID" >/dev/null 2>&1; then
  az ad sp create --id "$APP_ID" >/dev/null
  ok "Created service principal"
else
  ok "Service principal already exists"
fi

# ---- federated credentials (the OIDC magic — no secrets) --------------------
add_fic() {
  local name="$1" subject="$2"
  local existing
  existing="$(az ad app federated-credential list --id "$APP_ID" \
              --query "[?name=='$name'].name" -o tsv 2>/dev/null || true)"
  if [[ -n "$existing" ]]; then ok "Federated credential '$name' exists"; return; fi
  az ad app federated-credential create --id "$APP_ID" --parameters "$(cat <<JSON
{
  "name": "$name",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "$subject",
  "audiences": ["api://AzureADTokenExchange"],
  "description": "GitHub OIDC for $REPO ($name)"
}
JSON
)" >/dev/null
  ok "Added federated credential '$name' → $subject"
}

log "Configuring GitHub OIDC federated credentials for '$REPO'…"
add_fic "gh-branch-${BRANCH}" "repo:${REPO}:ref:refs/heads/${BRANCH}"
add_fic "gh-pull-request"     "repo:${REPO}:pull_request"
[[ -n "$ENVIRONMENT" ]] && add_fic "gh-env-${ENVIRONMENT}" "repo:${REPO}:environment:${ENVIRONMENT}"

# ---- optional: resource providers ------------------------------------------
if $REGISTER_PROVIDERS; then
  log "Registering resource providers…"
  for p in "${PROVIDERS[@]}"; do
    state="$(az provider show -n "$p" --query registrationState -o tsv 2>/dev/null || echo NotRegistered)"
    if [[ "$state" != "Registered" ]]; then az provider register -n "$p" >/dev/null && ok "Registering $p"; else ok "$p already registered"; fi
  done
fi

# ---- optional: resource group ----------------------------------------------
if $CREATE_RG; then
  if [[ "$(az group exists -n "$RESOURCE_GROUP")" == "true" ]]; then
    ok "Resource group '$RESOURCE_GROUP' exists"
  else
    az group create -n "$RESOURCE_GROUP" -l "$LOCATION" \
      --tags purpose=microhack lifecycle=ephemeral project=ccmh >/dev/null
    ok "Created resource group '$RESOURCE_GROUP' in $LOCATION"
  fi
fi

# ---- role assignment (scoped, least privilege) ------------------------------
SP_OBJECT_ID="$(az ad sp show --id "$APP_ID" --query id -o tsv)"
if [[ "$(az group exists -n "$RESOURCE_GROUP")" == "true" ]]; then
  SCOPE="/subscriptions/${SUB_ID}/resourceGroups/${RESOURCE_GROUP}"
  log "Assigning role '$ROLE' to the SP at RG scope…"
  if az role assignment list --assignee "$APP_ID" --scope "$SCOPE" \
        --query "[?roleDefinitionName=='$ROLE']" -o tsv | grep -q .; then
    ok "Role '$ROLE' already assigned at $SCOPE"
  else
    az role assignment create --assignee-object-id "$SP_OBJECT_ID" \
      --assignee-principal-type ServicePrincipal \
      --role "$ROLE" --scope "$SCOPE" >/dev/null
    ok "Assigned '$ROLE' at $SCOPE"
  fi
else
  warn "Resource group '$RESOURCE_GROUP' does not exist yet — skipping role assignment."
  warn "Re-run with --create-rg, or create the RG, then re-run to assign the role."
fi

# ---- optional: budget alert -------------------------------------------------
if [[ -n "$BUDGET" ]]; then
  log "Creating monthly budget alert (£$BUDGET) on the resource group…"
  start="$(date -u +%Y-%m-01)"
  az consumption budget create \
    --budget-name "budget-ccmh-lab" \
    --amount "$BUDGET" \
    --category Cost --time-grain Monthly \
    --start-date "$start" --end-date "2099-12-31" \
    --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1 \
    && ok "Budget alert created" \
    || warn "Could not create budget (needs Cost Management permissions) — set one in the Portal instead."
fi

# ---- emit / set the three values -------------------------------------------
echo
ok "OIDC bootstrap complete. Use these in GitHub (Settings → Secrets and variables → Actions):"
echo "  AZURE_CLIENT_ID=$APP_ID"
echo "  AZURE_TENANT_ID=$TENANT_ID"
echo "  AZURE_SUBSCRIPTION_ID=$SUB_ID"

if $SET_GH_SECRETS; then
  log "Setting GitHub Actions secrets via gh…"
  gh secret set AZURE_CLIENT_ID       --repo "$REPO" --body "$APP_ID"   && ok "Set AZURE_CLIENT_ID"
  gh secret set AZURE_TENANT_ID       --repo "$REPO" --body "$TENANT_ID" && ok "Set AZURE_TENANT_ID"
  gh secret set AZURE_SUBSCRIPTION_ID --repo "$REPO" --body "$SUB_ID"    && ok "Set AZURE_SUBSCRIPTION_ID"
fi

echo
ok "Done. Your workflows can now use azure/login with federated OIDC — no client secret required."
