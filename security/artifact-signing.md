# Artifact signing — keyless cosign, SBOM & SLSA provenance

This runbook explains what [`.github/workflows/security-sign.yml`](../.github/workflows/security-sign.yml)
produces and, crucially, how to **verify** it. A signature nobody checks is theatre — the deploy step in
Challenge 05 verifies before it promotes an image.

We sign **keyless**: cosign uses a short-lived certificate bound to the **GitHub Actions OIDC identity**
(Sigstore Fulcio) and logs the signature to a public transparency log (Rekor). There is **no signing key** to
store, leak, or rotate — the identity *is* the workflow.

## What the workflow emits

For a pushed image `ghcr.io/<owner>/<repo>/<image>@sha256:<digest>` the signing job produces:

| Artifact | How | Verified with |
| --- | --- | --- |
| **Signature** | `cosign sign` (keyless OIDC) | `cosign verify` |
| **SBOM (SPDX JSON)** | `anchore/sbom-action` (syft) | `cosign verify-attestation --type spdxjson` |
| **SBOM attestation** | `cosign attest --type spdxjson` | `cosign verify-attestation` |
| **SLSA build provenance** | `actions/attest-build-provenance` | `gh attestation verify` / `cosign verify-attestation` |

All four are pushed to the registry as OCI **referrers** of the image digest, so they travel with the image.

## Call it from another workflow

`security-sign.yml` is a **reusable** workflow. A workstream that builds the Orders API calls it like this (the
caller owns the build context and Dockerfile; signing stays centralised here):

```yaml
jobs:
  ship:
    uses: ./.github/workflows/security-sign.yml
    permissions:
      contents: read
      packages: write
      id-token: write
      attestations: write
    with:
      image-name: orders-api
      context: src/legacy-orders-api
      dockerfile: src/legacy-orders-api/Dockerfile
```

Or run it standalone from the Actions tab via **Run workflow** (it defaults to the Orders API context).

## Verify a signed image

Set the identity expectations to the workflow that is allowed to sign. **Pin both** the signing workflow
identity and the OIDC issuer — a signature from the wrong workflow must fail.

```bash
IMAGE=ghcr.io/nikomix/microhack-agentic-devops/orders-api
DIGEST=sha256:<digest-from-the-build>

cosign verify "${IMAGE}@${DIGEST}" \
  --certificate-identity-regexp "https://github.com/NikoMix/microhack-agentic-devops/.github/workflows/security-sign.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  -o text
```

A pass prints the certificate subject (the workflow), the issuer, and the Rekor log entry. Tampering with the
image, or a signature from any other identity, fails the check.

## Read the SBOM and verify its attestation

```bash
# Pull the SBOM attestation and confirm it was signed by our workflow identity
cosign verify-attestation "${IMAGE}@${DIGEST}" \
  --type spdxjson \
  --certificate-identity-regexp "https://github.com/NikoMix/microhack-agentic-devops/.github/workflows/security-sign.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  | jq -r '.payload | @base64d | fromjson | .predicate' > sbom.spdx.json

# What is actually inside the image?
jq -r '.packages[]?.name' sbom.spdx.json | sort -u | head
```

The SBOM is also uploaded as a workflow **artifact** (`sbom-<image>.spdx.json`) for quick download without a
registry round-trip.

## Verify SLSA build provenance

Provenance answers "which workflow, from which commit, on which runner, built this exact digest?" The simplest
check uses the GitHub CLI:

```bash
gh attestation verify "oci://${IMAGE}@${DIGEST}" \
  --repo NikoMix/microhack-agentic-devops
```

It confirms the image was built by this repository's Actions and prints the builder identity and source commit.

## Local dry run (no registry)

You can rehearse the verification flow entirely locally to understand the moving parts:

```bash
# Build locally (Docker / Buildx) and reference by digest after a push to a throwaway registry,
# or use cosign against an existing public image to see a successful verify, e.g.:
cosign verify ghcr.io/sigstore/cosign/cosign \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" -o text | head
```

> cosign keyless **signing** needs an ambient OIDC token, so the *sign* step only works inside GitHub Actions (or
> another OIDC-capable environment). **Verification** works anywhere with network access to Rekor.

## Why these choices

- **Keyless over keys** — no long-lived signing key anywhere; rotation is automatic per run. Aligns with the
  repo's "no secrets" contract.
- **SHA-pinned actions** — `cosign-installer`, `sbom-action`, `attest-build-provenance`, and the docker actions
  are all pinned by commit (see the workflow), so the signing toolchain itself is supply-chain hardened.
- **SPDX SBOM** — an open, tool-neutral format (ISO/IEC 5962); consumable by Defender for Cloud and other
  scanners.
- **Verify at deploy** — the signature/provenance only delivers value if the deploy gate enforces it; Challenge
  05 wires `cosign verify` into the promotion step.

## What good looks like

An attendee can take a bare image digest and, from a clean shell, prove (1) it was signed by *our* workflow,
(2) what is in it via its SBOM, and (3) the commit and runner that built it — all without any pre-shared key.
