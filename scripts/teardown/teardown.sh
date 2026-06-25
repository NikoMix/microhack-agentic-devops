#!/usr/bin/env bash
#
# teardown.sh — Tear down the Contoso Commerce Agentic DevOps MicroHack lab.
#
# Deletes the ephemeral resource group and (optionally) purges soft-deleted
# Key Vaults / Cognitive Services and removes the GitHub OIDC app registration,
# so nothing keeps accruing cost or retention.
#
# Usage:
#   ./teardown.sh --resource-group rg-ccmh-lab [--subscription <sub-id>] \
#                 [--purge] [--remove-oidc] [--app-name id-ccmh-lab] \
#                 [--no-wait] [--yes]
#
set -euo pipefail

RESOURCE_GROUP="rg-ccmh-lab"
SUBSCRIPTION=""
APP_NAME="id-ccmh-lab"
PURGE=false
REMOVE_OIDC=false
NO_WAIT=false
ASSUME_YES=false

log()  { printf '\033[0;36m▶ %s\033[0m\n' "$*"; }
ok()   { printf '\033[0;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[0;33m! %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[0;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --resource-group) RESOURCE_GROUP="$2"; shift 2;;
    --subscription)   SUBSCRIPTION="$2"; shift 2;;
    --app-name)       APP_NAME="$2"; shift 2;;
    --purge)          PURGE=true; shift;;
    --remove-oidc)    REMOVE_OIDC=true; shift;;
    --no-wait)        NO_WAIT=true; shift;;
    --yes|-y)         ASSUME_YES=true; shift;;
    -h|--help)        sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) die "Unknown argument: $1 (use --help)";;
  esac
done

command -v az >/dev/null || die "Azure CLI (az) is required."
az account show >/dev/null 2>&1 || die "Not logged in. Run 'az login' first."
[[ -n "$SUBSCRIPTION" ]] && az account set --subscription "$SUBSCRIPTION"

SUB_NAME="$(az account show --query name -o tsv)"
SUB_ID="$(az account show --query id -o tsv)"

# ---- confirm ----------------------------------------------------------------
log "About to tear down:"
echo "    Subscription : $SUB_NAME ($SUB_ID)"
echo "    Resource grp : $RESOURCE_GROUP"
echo "    Purge vaults : $PURGE"
echo "    Remove OIDC  : $REMOVE_OIDC (app '$APP_NAME')"
if ! $ASSUME_YES; then
  read -r -p "Type the resource group name to confirm deletion: " confirm
  [[ "$confirm" == "$RESOURCE_GROUP" ]] || die "Confirmation did not match. Aborting."
fi

# ---- capture names to purge BEFORE deleting the RG --------------------------
KV_NAMES=(); CS_NAMES=()
if $PURGE && [[ "$(az group exists -n "$RESOURCE_GROUP")" == "true" ]]; then
  mapfile -t KV_NAMES < <(az keyvault list -g "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || true)
  mapfile -t CS_NAMES < <(az cognitiveservices account list -g "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || true)
fi

# ---- delete the resource group ----------------------------------------------
if [[ "$(az group exists -n "$RESOURCE_GROUP")" == "true" ]]; then
  log "Deleting resource group '$RESOURCE_GROUP'…"
  if $NO_WAIT; then
    az group delete -n "$RESOURCE_GROUP" --yes --no-wait
    ok "Deletion started (running in background)."
  else
    az group delete -n "$RESOURCE_GROUP" --yes
    ok "Resource group deleted."
  fi
else
  warn "Resource group '$RESOURCE_GROUP' does not exist — nothing to delete."
fi

# ---- purge soft-deleted resources ------------------------------------------
if $PURGE && ! $NO_WAIT; then
  for kv in "${KV_NAMES[@]:-}"; do
    [[ -z "$kv" ]] && continue
    log "Purging soft-deleted Key Vault '$kv'…"
    az keyvault purge --name "$kv" >/dev/null 2>&1 && ok "Purged vault '$kv'" || warn "Could not purge vault '$kv' (may be protected)."
  done
  for cs in "${CS_NAMES[@]:-}"; do
    [[ -z "$cs" ]] && continue
    LOC="$(az cognitiveservices account list-deleted --query "[?name=='$cs'].location | [0]" -o tsv 2>/dev/null || true)"
    if [[ -n "$LOC" ]]; then
      log "Purging soft-deleted Cognitive Services '$cs'…"
      az cognitiveservices account purge -n "$cs" -g "$RESOURCE_GROUP" -l "$LOC" >/dev/null 2>&1 \
        && ok "Purged '$cs'" || warn "Could not purge '$cs'."
    fi
  done
elif $PURGE && $NO_WAIT; then
  warn "--purge skipped because --no-wait was set (RG must finish deleting first). Re-run with --purge only."
fi

# ---- remove OIDC app registration ------------------------------------------
if $REMOVE_OIDC; then
  APP_ID="$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)"
  if [[ -n "$APP_ID" ]]; then
    log "Deleting Entra ID app registration '$APP_NAME' ($APP_ID)…"
    az ad app delete --id "$APP_ID" && ok "App registration removed (federated credentials go with it)."
  else
    warn "No app registration named '$APP_NAME' found."
  fi
fi

# ---- verify -----------------------------------------------------------------
echo
log "Verification:"
echo "    az group exists -n $RESOURCE_GROUP  → $(az group exists -n "$RESOURCE_GROUP")"
ok "Teardown complete. Remember to deregister any self-hosted runners in GitHub (Settings → Actions → Runners)."
