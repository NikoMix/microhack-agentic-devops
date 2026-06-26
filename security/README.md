# Security — Contoso Commerce Agentic DevOps MicroHack

This folder is the **Secure SDLC** evidence and enablement pack for the MicroHack. It pairs the automated
controls under [`.github/`](../.github/) with the human-facing runbooks a delivery consultant needs to turn the
controls on, demonstrate them, and verify them.

Everything here follows the repo contract in
[`.github/copilot-instructions.md`](../.github/copilot-instructions.md): **no secrets committed**, identity via
**Entra ID + `DefaultAzureCredential` + GitHub OIDC**, secrets pulled from **Key Vault** at runtime, and only
**MIT/Apache/BSD/PSF**-licensed dependencies.

> Post-2025 GHAS naming is used throughout: **GitHub Code Security** (CodeQL, Autofix, Dependency Review,
> Dependabot) and **GitHub Secret Protection** (secret scanning + push protection).

## What the platform enforces

| Control | Surface | Where it lives |
| --- | --- | --- |
| Static analysis (CodeQL + Autofix) | C# + Python | [`.github/workflows/security-codeql.yml`](../.github/workflows/security-codeql.yml) · [`.github/codeql/codeql-config.yml`](../.github/codeql/codeql-config.yml) |
| Dependency review (PR gate) | All ecosystems | [`.github/workflows/security-dependency-review.yml`](../.github/workflows/security-dependency-review.yml) |
| Automated dependency updates | nuget · uv · npm · actions · docker | [`.github/dependabot.yml`](../.github/dependabot.yml) |
| Secret scanning + push protection | Whole repo | [`secret-protection.md`](secret-protection.md) |
| Artifact signing + SBOM + provenance | Container images | [`.github/workflows/security-sign.yml`](../.github/workflows/security-sign.yml) · [`artifact-signing.md`](artifact-signing.md) |
| Runtime posture + CSPM | Azure resources | [`defender-for-cloud.md`](defender-for-cloud.md) |
| Runtime secret storage | Azure | [`key-vault.md`](key-vault.md) |

## Runbooks in this folder

- **[`threat-model.md`](threat-model.md)** — a STRIDE-lite model of the lab platform: what we are defending,
  the trust boundaries, and which control answers each threat.
- **[`secret-protection.md`](secret-protection.md)** — enable secret scanning + push protection and run the
  "blocked secret → bypass with a reason" teaching moment safely.
- **[`artifact-signing.md`](artifact-signing.md)** — sign and **verify** a container image with keyless cosign,
  read its SBOM, and inspect SLSA build provenance.
- **[`defender-for-cloud.md`](defender-for-cloud.md)** — turn on Microsoft Defender for Cloud (CSPM + the
  relevant workload plans) and wire GitHub Advanced Security results into Defender.
- **[`key-vault.md`](key-vault.md)** — provision Key Vault with RBAC, store a runtime secret, and read it from
  code with `DefaultAzureCredential` (no connection strings, no keys).

## How this maps to the challenge

These runbooks are the reference material for
[`docs/challenges/challenge-03-secure-sdlc`](../docs/challenges/challenge-03-secure-sdlc/). The challenge
`README.md` is the student lab; the files here are the deeper "why" and the copy-paste commands.

## Golden rule

If a control would require committing a secret to work, it is the wrong control. Every credential in this lab is
either **short-lived (OIDC)** or **stored in Key Vault and fetched at runtime**. Nothing long-lived lands in git.
