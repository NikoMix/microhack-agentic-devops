#!/usr/bin/env bash
# =============================================================================
# Shared helpers for the Contoso Commerce ADO -> GitHub migration scripts.
# Sourced by migrate-repo.sh and boards-to-issues.sh. No side effects on source.
# =============================================================================

# Emit a namespaced log line on stdout.
mig::log() {
  printf '[migration] %s\n' "$*"
}

# Emit a warning on stderr.
mig::warn() {
  printf '[migration][warn] %s\n' "$*" >&2
}

# Emit an error on stderr.
mig::err() {
  printf '[migration][error] %s\n' "$*" >&2
}

# Fail unless the named command is available on PATH.
mig::require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    mig::err "Required command not found on PATH: $1"
    return 1
  fi
}

# Fail unless the named environment variable is set and non-empty.
mig::require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    mig::err "Required environment variable is not set: ${name}"
    return 1
  fi
}

# Map an Azure Boards work item type to a GitHub issue label.
mig::label_for_type() {
  case "$1" in
    Epic) printf 'type:epic' ;;
    Feature) printf 'type:feature' ;;
    "User Story") printf 'type:user-story' ;;
    Bug) printf 'bug' ;;
    Task) printf 'type:task' ;;
    *) printf 'type:work-item' ;;
  esac
}

# Return 0 when an Azure Boards state should map to a closed GitHub issue.
mig::state_is_closed() {
  case "$1" in
    Closed | Done | Removed | Resolved) return 0 ;;
    *) return 1 ;;
  esac
}
