#!/usr/bin/env bash
# Post-create provisioning for the Contoso Commerce MicroHack dev container.
# Installs lab CLIs not provided as dev container features: uv (Python), cosign
# (artifact signing), actionlint + zizmor (Actions hygiene); verifies the toolchain.
set -euo pipefail

echo "==> Verifying core toolchain"
dotnet --version
python --version
az version --output table || true
gh --version | head -n1

echo "==> Installing uv (fast Python package manager)"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

echo "==> Installing ruff + mypy + pip-audit as global lab tools"
uv tool install ruff >/dev/null 2>&1 || true
uv tool install mypy >/dev/null 2>&1 || true
uv tool install pip-audit >/dev/null 2>&1 || true

echo "==> Installing cosign (Sigstore artifact signing)"
if ! command -v cosign >/dev/null 2>&1; then
  COSIGN_VERSION="v2.4.1"
  curl -fsSL -o /tmp/cosign "https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}/cosign-linux-amd64"
  sudo install -m 0755 /tmp/cosign /usr/local/bin/cosign && rm -f /tmp/cosign
fi
cosign version || true

echo "==> Installing actionlint + zizmor (GitHub Actions linters)"
if ! command -v actionlint >/dev/null 2>&1; then
  bash <(curl -fsSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash) >/dev/null 2>&1 || true
  sudo install -m 0755 ./actionlint /usr/local/bin/actionlint 2>/dev/null || true
  rm -f ./actionlint
fi
uv tool install zizmor >/dev/null 2>&1 || true

echo "==> Ensuring Bicep is current"
az bicep install >/dev/null 2>&1 || true
az bicep version || true

echo "==> Dev container ready. See docs/trainer/prerequisites.md to authenticate to Azure + GitHub."
