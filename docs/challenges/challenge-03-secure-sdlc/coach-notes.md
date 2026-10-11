# Challenge 03 — Secure SDLC · coach notes

Trainer companion to [`README.md`](README.md). The arc of this hour is **"make the SDLC trustworthy"**: students
should leave able to point at a control for every row of the STRIDE table in
[`/security/threat-model.md`](../../../security/threat-model.md). Keep it hands-on — every control is one they
turn on themselves.

## Timing (60 min)

| Min | Segment | Notes |
| --- | --- | --- |
| 0–5 | Framing | Why secure SDLC; the post-2025 GHAS split (Code Security vs Secret Protection). Show the ref-arch diagram. |
| 5–15 | Task 1–2: enable + CodeQL | Enable controls live; kick off `security-codeql.yml`. While it runs, narrate **build-mode none**. |
| 15–25 | Task 2 cont.: **Copilot Autofix** | The crowd-pleaser. Generate a fix on a real alert, read the explanation, apply it. |
| 25–35 | Task 3: Dependency Review + Dependabot | Open the "bad PR", watch the gate fail; tour `dependabot.yml`. |
| 35–45 | Task 4: Secret Protection demo | The signature moment — block, **bypass with reason**, remove + revoke. |
| 45–57 | Task 5: sign + verify | Run `security-sign.yml`; verify signature + provenance from a clean shell. |
| 57–60 | Task 6 + wrap | Defender/Key Vault are mostly narration if time is tight; assign as stretch. |

> If you are behind, Task 6 (Defender + Key Vault) is the compressible one — demo it from the front and point to
> the runbooks. Never cut Task 4 (Secret Protection) or the **verify** half of Task 5; they are the lessons.

## Key teaching points

- **Two names, one product.** "GitHub Advanced Security" split into **GitHub Code Security** (CodeQL, Autofix,
  Dependency Review, Dependabot) and **GitHub Secret Protection** (secret scanning + push protection). Use the
  new names — customers see them in the UI now.
- **Copilot Autofix is the headline.** CodeQL *finds*; **Autofix** proposes a reviewed code change with an
  explanation, turning a backlog of alerts into PRs. Emphasise it is a **suggestion a human reviews**, not an
  auto-merge. This is the moment that lands "agentic DevOps secures itself". Show the diff *and* the natural
  language rationale.
- **build-mode `none` for C#.** Modern CodeQL builds the C# database from source with **no .NET SDK or compile**
  (it is the default for C#, C/C++, Java, Rust). That is why the lab is robust even before the Orders API
  compiles cleanly. Stretch: switch `csharp` to `autobuild` and compare — autobuild sees generated code, none is
  faster and never breaks on a red build.
- **Two dependency gates, not one.** Dependency **Review** blocks the *incoming PR diff*; **Dependabot** fixes
  what is *already on `main`*. Neither covers the other's window — you need both. The review gate also enforces
  **licences** (permissive-only), which most teams forget is a supply-chain risk.
- **Keyless signing removes the worst secret.** A signing **key** is the one secret you cannot put in Key Vault
  and rotate cheaply. cosign keyless makes the **GitHub workflow identity** the signer — nothing to store or
  leak. Tie this back to the "no secrets" contract.
- **A signature nobody verifies is theatre.** Spend the time on `cosign verify` and `gh attestation verify`,
  pinned to the *correct* workflow identity. Demonstrate that a wrong identity or a tampered digest **fails**.
- **Pin everything.** Actions are SHA-pinned; Dependabot (`github-actions` ecosystem) keeps those pins current.
  Show one pinned `uses:` line and the `# v4` comment beside the SHA.

## Facilitating the Secret Protection demo (Task 4) safely

This is the demo most likely to go sideways. Run it on the rails:

- **Use a throwaway fine-grained PAT** as the trigger, not a provider example key. Documented example keys are
  deliberately *allow-listed* by scanners, so they will **not** fire the block — the demo falls flat. A PAT
  always fires.
- **Never have anyone commit a real, live, valuable secret** — even to demonstrate. The throwaway PAT is created
  for the demo and **revoked immediately** after.
- **Make the bypass the lesson, not the loophole.** The point is that the override is *attributable*: pull up the
  audit-log entry (`action:secret_scanning_push_protection.bypass`) and show "who bypassed what, and why". In a
  real org, restrict who can bypass.
- **Reinforce remediation = rotation.** If a secret ever reached the remote, bypassing or deleting the file does
  **not** make it safe; it must be **revoked/rotated**. This is the single most important sentence of the hour.

## Common pitfalls and fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `security-codeql` fails: "no source code found" for a language | The `src/` path for that language does not exist yet (cross-workstream dependency) | Ensure Challenge 01/05 code is merged; until then expect the matrix leg to no-op or be skipped. |
| Push-protection demo "doesn't block" | A documented example key was used (allow-listed) | Use a throwaway fine-grained PAT instead. |
| `cosign verify` fails with identity mismatch | `--certificate-identity-regexp` does not match the signing workflow path/ref | Copy the exact workflow path; keep the `@.*` ref suffix. |
| cosign **sign** fails locally | Keyless signing needs an **ambient OIDC token** (Actions); local shells have none | Sign only in CI; **verify** locally. |
| Dependency Review check is skipped | Dependency graph disabled, or it ran on a non-PR event | Enable the Dependency graph; the action only runs on `pull_request`. |
| `azure/login`/Defender step "unauthorized" | OIDC federated credential subject does not match the branch/PR | Re-run Challenge 00 `setup-oidc.sh`; check the federated-credential subject. |
| Dependabot opens no PRs | No manifests on the default branch yet, or everything is already current | Expected pre-integration; confirm via **Insights → Dependency graph → Dependabot**. |
| GHCR push denied | `packages: write` missing, or the package is private to a fork | Confirm job `permissions:`; for forks the workflow runs build-only (`push: false`). |

## CI note for trainers (account billing)

In the authoring environment, **GitHub Actions billing is disabled**, so these workflows will not run live until
billing is restored. They are authored to pass once enabled and were validated locally with **actionlint** and
**zizmor** (zero findings), plus YAML and markdown lint. If a student's runs are queued/blocked, check
**Settings → Billing** before debugging the YAML.

## Discussion questions

1. Where is the **highest-value trust boundary** in this platform, and which single control would you turn on
   first if you could only pick one? (Steer toward Developer → Repo + push protection, or Actions → Azure +
   OIDC.)
2. Dependency Review and Dependabot overlap — *why keep both*? What window does each cover that the other does
   not?
3. Copilot Autofix proposes a change. **Who is accountable** for the fix, and what review gate keeps a bad
   suggestion out of `main`?
4. You sign every image. **What breaks if the deploy step never verifies the signature**? Is signing-without-
   verifying worse than not signing (false confidence)?
5. A teammate bypasses push protection daily "to move fast". What controls and conversations change that
   behaviour without grinding delivery to a halt?
6. Keyless cosign has **no key to rotate** — is that strictly better, or what new dependency (Sigstore/Rekor
   availability, OIDC issuer trust) have you taken on?

## What good looks like

- Every box on the ref-arch diagram corresponds to a control the attendees **enabled themselves**.
- A student can take a bare image **digest** and, from a clean shell, prove it was signed by *our* workflow, list
  its SBOM contents, and name the commit + runner that built it.
- The room understands that the **bypass** is friction-by-design and **attributable**, and that **rotation** —
  not deletion — is how you remediate a leaked secret.
- Nobody committed a live secret to demonstrate secret protection. The irony is the lesson.
