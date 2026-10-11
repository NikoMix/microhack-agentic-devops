# GitHub Secret Protection — scanning, push protection & the bypass teaching moment

**GitHub Secret Protection** is the post-2025 name for the secret-scanning half of GitHub Advanced Security:
**secret scanning** (detects committed credentials) plus **push protection** (blocks them *before* they land).
This runbook turns it on and runs the signature classroom demo — pushing a secret, watching it get blocked, then
performing a **documented bypass with a reason** — without ever committing a live credential to this repository.

> Defence in depth: this repo also runs **gitleaks** as a `pre-commit` hook
> (see [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)). Push protection is the server-side backstop for
> when a hook is skipped or not installed.

## 1. Enable the controls

GitHub Secret Protection is enabled in repository (or organization) settings.

UI path: **Settings → Advanced Security** (or **Code security**) →

- **Secret scanning** → **Enable**
- **Push protection** → **Enable**

Or with the CLI (requires admin on the repo):

```bash
gh api -X PATCH repos/NikoMix/microhack-agentic-devops \
  -f security_and_analysis='{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}'
```

Verify:

```bash
gh api repos/NikoMix/microhack-agentic-devops \
  --jq '.security_and_analysis | {scan: .secret_scanning.status, push: .secret_scanning_push_protection.status}'
```

Both should read `enabled`.

## 2. The teaching moment — block, then bypass with a reason

The point of the demo is to feel the **guardrail** and then experience the **audited override** that real teams
need for the occasional false positive. We never put a triggering secret in the repo's history or in these docs —
the attendee introduces a **throwaway** value at demo time and removes it immediately.

### 2a. Generate a throwaway trigger (recommended: a fine-grained PAT)

The most reliable, self-contained trigger is a GitHub **fine-grained personal access token** you create and then
revoke. It always matches a high-confidence pattern, and it is yours to destroy.

1. Create one: **Settings → Developer settings → Fine-grained tokens → Generate** (any scope, 7-day expiry).
2. Copy the token value (starts with `github_pat_`).
3. **Immediately** plan to revoke it after the demo — treat it as burned.

> Alternative that needs no token: many teams use a provider's *documented example* key for illustration, but
> those are deliberately allow-listed by scanners (so they will **not** trigger a block). For the block to fire
> you need a value that matches a live pattern, which is exactly why a throwaway PAT works best.

### 2b. Try to push it — watch push protection block

```bash
git checkout -b demo/secret-protection
printf 'token = "%s"\n' "$YOUR_THROWAWAY_PAT" > leak-demo.txt
git add leak-demo.txt
git commit -m "demo: intentionally stage a throwaway secret"
git push -u origin demo/secret-protection
```

The push is **rejected**. GitHub prints the detected secret type, the file and line, and a remediation URL. The
credential never reaches the remote.

### 2c. The audited bypass (the real lesson)

Sometimes the detection is a genuine false positive (a test fixture, a sample, a rotated value). Push protection
lets a developer proceed **only with an explicit, logged reason**:

- **In the CLI flow**, open the URL GitHub printed and choose to allow the push, selecting a reason
  (*It's used in tests* · *It's a false positive* · *I'll fix it later*). Each choice is **recorded in the
  security audit log** with the actor, repo, and timestamp.
- **In the web/PR flow**, the same prompt appears inline when push protection blocks a commit in the browser.

The discussion point: the bypass is **friction by design**. It is fast enough not to halt real work, but it is
**attributable** — a coach can later show the audit-log entry for "who bypassed what, and why".

### 2d. Clean up — remove the value *and* revoke it

```bash
git rm leak-demo.txt
git commit -m "demo: remove throwaway secret"
git push
git checkout main
git branch -D demo/secret-protection
git push origin --delete demo/secret-protection
```

Then **revoke the throwaway PAT** in GitHub Developer settings. Bypassing push protection does **not** make the
value safe — if it ever reached the remote, treat it as compromised and rotate it. Revocation is the real
remediation.

## 3. Review what got bypassed

```bash
# Org owners / security managers: see push-protection bypasses in the audit log
gh api "orgs/<your-org>/audit-log?phrase=action:secret_scanning_push_protection.bypass" \
  --jq '.[] | {who: .actor, when: .created_at, repo: .repo}'
```

For repository-level alerts that secret scanning has already raised:

```bash
gh api repos/NikoMix/microhack-agentic-devops/secret-scanning/alerts \
  --jq '.[] | {type: .secret_type_display_name, state: .state, file: .locations}'
```

## 4. Hardening beyond the demo

- **Block, do not just warn.** Push protection blocks by default; keep it that way and reserve bypass for true
  false positives.
- **Restrict who can bypass.** Limit push-protection bypass to a small role; route everyone else through a
  security reviewer.
- **Turn on validity checks + custom patterns.** Validity checks tell you if a leaked token is *still live*;
  custom patterns catch Contoso-specific formats the default partners miss.
- **Pair with runtime secrets.** The reason this repo rarely trips secret scanning is that there are no secrets to
  commit — identity is OIDC and runtime secrets live in [Key Vault](key-vault.md).

## What good looks like

By the end of this runbook a developer has *felt* the block, performed an *attributable* bypass, removed and
**revoked** the throwaway value, and can find the corresponding audit-log entry. No real credential ever entered
the repository's history.
