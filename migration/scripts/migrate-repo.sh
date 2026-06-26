#!/usr/bin/env bash
# =============================================================================
# Migrate one Azure DevOps Git repository to GitHub with GitHub Enterprise
# Importer (the `gh gei` extension).
#
# With --dry-run the script validates prerequisites and prints the exact command
# instead of executing it, so it is safe to run during the lab with no source
# Azure DevOps organization and no network access.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
. "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'EOF'
Usage:
  migrate-repo.sh --ado-org ORG --ado-team-project PROJECT --ado-repo REPO \
                  --github-org ORG --github-repo REPO \
                  [--target-visibility private|internal|public] [--dry-run]

Environment (required for a real migration; optional for --dry-run):
  ADO_PAT  Azure DevOps PAT. Scopes: Code (Read), Project and Team (Read),
           Work Items (Read), Graph (Read).
  GH_PAT   GitHub PAT. Scopes: repo, admin:org, workflow.

Flags:
  --ado-org            Source Azure DevOps organization
  --ado-team-project   Source team project
  --ado-repo           Source repository name
  --github-org         Destination GitHub organization
  --github-repo        Destination repository name
  --target-visibility  Visibility of the new repo (default: private)
  --dry-run            Validate prerequisites and print the command only
  -h, --help           Show this help
EOF
}

ado_org=""
ado_team_project=""
ado_repo=""
github_org=""
github_repo=""
target_visibility="private"
dry_run="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --ado-org) ado_org="$2"; shift 2 ;;
    --ado-team-project) ado_team_project="$2"; shift 2 ;;
    --ado-repo) ado_repo="$2"; shift 2 ;;
    --github-org) github_org="$2"; shift 2 ;;
    --github-repo) github_repo="$2"; shift 2 ;;
    --target-visibility) target_visibility="$2"; shift 2 ;;
    --dry-run) dry_run="true"; shift ;;
    -h | --help) usage; exit 0 ;;
    *) mig::err "Unknown argument: $1"; usage; exit 2 ;;
  esac
done

missing="false"
for pair in \
  "ado-org:${ado_org}" \
  "ado-team-project:${ado_team_project}" \
  "ado-repo:${ado_repo}" \
  "github-org:${github_org}" \
  "github-repo:${github_repo}"; do
  if [ -z "${pair#*:}" ]; then
    mig::err "Missing required flag: --${pair%%:*}"
    missing="true"
  fi
done
if [ "${missing}" = "true" ]; then
  usage
  exit 2
fi

mig::require_cmd gh

if ! gh extension list 2>/dev/null | grep -q "gh-gei"; then
  mig::warn "The gh-gei extension is not installed. Install it with:"
  mig::warn "  gh extension install github/gh-gei"
fi

cmd=(gh gei migrate-repo
  --ado-org "${ado_org}"
  --ado-team-project "${ado_team_project}"
  --ado-repo "${ado_repo}"
  --github-org "${github_org}"
  --github-repo "${github_repo}"
  --target-repo-visibility "${target_visibility}")

if [ "${dry_run}" = "true" ]; then
  mig::log "DRY RUN — no migration will be performed."
  mig::log "Would run (PATs are read from \$ADO_PAT and \$GH_PAT):"
  printf '  %s\n' "${cmd[*]}"
  if [ -n "${ADO_PAT:-}" ]; then mig::log "ADO_PAT is set."; else mig::warn "ADO_PAT is not set."; fi
  if [ -n "${GH_PAT:-}" ]; then mig::log "GH_PAT is set."; else mig::warn "GH_PAT is not set."; fi
  exit 0
fi

mig::require_env ADO_PAT
mig::require_env GH_PAT
mig::log "Migrating ${ado_org}/${ado_team_project}/${ado_repo} -> ${github_org}/${github_repo}"
"${cmd[@]}"
mig::log "Migration submitted. Review the migration log in the destination organization."
