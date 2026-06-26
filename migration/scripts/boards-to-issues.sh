#!/usr/bin/env bash
# =============================================================================
# Recreate Azure Boards work items as GitHub Issues.
#
# Reads a work-items.json export (default: the bundled sample export) and creates
# one GitHub issue per work item, mapping the work item type to a label and
# closing issues whose source state was terminal.
#
# With --dry-run it prints what it would create without calling the GitHub API,
# so it runs fully offline against migration/sample-export/boards/work-items.json.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
. "${SCRIPT_DIR}/common.sh"

DEFAULT_INPUT="${SCRIPT_DIR}/../sample-export/boards/work-items.json"

usage() {
  cat <<'EOF'
Usage:
  boards-to-issues.sh [--repo OWNER/NAME] [--input PATH] [--dry-run]

Flags:
  --repo OWNER/NAME  Destination GitHub repository (required unless --dry-run)
  --input PATH       work-items.json to read (default: bundled sample export)
  --dry-run          Print planned issues without calling the GitHub API
  -h, --help         Show this help

Requires: jq. A real run also requires gh (authenticated).
EOF
}

repo=""
input="${DEFAULT_INPUT}"
dry_run="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --input) input="$2"; shift 2 ;;
    --dry-run) dry_run="true"; shift ;;
    -h | --help) usage; exit 0 ;;
    *) mig::err "Unknown argument: $1"; usage; exit 2 ;;
  esac
done

mig::require_cmd jq
if [ ! -f "${input}" ]; then
  mig::err "Input file not found: ${input}"
  exit 1
fi
if [ "${dry_run}" != "true" ]; then
  mig::require_cmd gh
  if [ -z "${repo}" ]; then
    mig::err "--repo OWNER/NAME is required unless --dry-run is set."
    exit 2
  fi
fi

# Pre-create the labels we map to, so `gh issue create --label` never fails.
ensure_label() {
  gh label create "$1" --repo "${repo}" --color "$2" --description "$3" --force >/dev/null 2>&1 || true
}
if [ "${dry_run}" != "true" ]; then
  ensure_label "type:epic" "6f42c1" "Migrated Azure Boards Epic"
  ensure_label "type:feature" "1d76db" "Migrated Azure Boards Feature"
  ensure_label "type:user-story" "0e8a16" "Migrated Azure Boards User Story"
  ensure_label "type:task" "fbca04" "Migrated Azure Boards Task"
  ensure_label "bug" "d73a4a" "Migrated Azure Boards Bug"
fi

total="$(jq 'length' "${input}")"
mig::log "Found ${total} work item(s) in ${input}"

i=0
created=0
while [ "${i}" -lt "${total}" ]; do
  id="$(jq -r ".[${i}].id" "${input}")"
  type="$(jq -r ".[${i}].workItemType" "${input}")"
  title="$(jq -r ".[${i}].title" "${input}")"
  state="$(jq -r ".[${i}].state" "${input}")"
  assigned="$(jq -r ".[${i}].assignedTo // \"unassigned\"" "${input}")"
  area="$(jq -r ".[${i}].areaPath // \"\"" "${input}")"
  iteration="$(jq -r ".[${i}].iterationPath // \"\"" "${input}")"
  parent="$(jq -r ".[${i}].parent // \"none\"" "${input}")"
  description="$(jq -r ".[${i}].description // \"\"" "${input}")"
  tags="$(jq -r "(.[${i}].tags // []) | join(\", \")" "${input}")"
  i=$((i + 1))

  label="$(mig::label_for_type "${type}")"
  if mig::state_is_closed "${state}"; then close_note="yes"; else close_note="no"; fi

  body="$(printf 'Migrated from Azure Boards work item **#%s** (%s).\n\n%s\n\n---\n- **Original state:** %s\n- **Originally assigned to:** %s\n- **Area path:** %s\n- **Iteration:** %s\n- **Parent work item:** %s\n- **Tags:** %s\n' \
    "${id}" "${type}" "${description}" "${state}" "${assigned}" "${area}" "${iteration}" "${parent}" "${tags}")"

  if [ "${dry_run}" = "true" ]; then
    mig::log "[#${id}] ${type} -> label '${label}', close after create: ${close_note}"
    printf '        title: %s\n' "${title}"
    continue
  fi

  issue_url="$(gh issue create --repo "${repo}" --title "${title}" --body "${body}" --label "${label}" 2>/dev/null || true)"
  if [ -z "${issue_url}" ]; then
    mig::warn "[#${id}] failed to create issue for: ${title}"
    continue
  fi
  created=$((created + 1))
  mig::log "[#${id}] created ${issue_url}"
  if mig::state_is_closed "${state}"; then
    gh issue close "${issue_url}" --reason completed >/dev/null 2>&1 || true
    mig::log "[#${id}] closed (original state: ${state})"
  fi
done

if [ "${dry_run}" = "true" ]; then
  mig::log "DRY RUN complete — ${total} issue(s) would be created."
else
  mig::log "Done — created ${created} of ${total} issue(s) in ${repo}."
fi
