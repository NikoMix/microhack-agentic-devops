# Coach notes — Challenge 01 (Azure DevOps → GitHub migration)

Trainer companion for the 60-minute migration challenge. Students may arrive **without an Azure DevOps
org** — the bundled sample export + `--dry-run` paths are the default, not a fallback. Make that clear
up front so nobody blocks waiting on access.

## Timing (60 minutes)

| Min | Segment | Focus |
| --- | --- | --- |
| 0–5 | Framing | The "before": Repos + Pipelines + Boards, and the stored-credential problem |
| 5–12 | Task 1 | Build/test the legacy API locally; skim `azure-pipelines.yml` |
| 12–20 | Tasks 2–3 | Importer + PAT scopes; trial run; `migrate-repo --dry-run` |
| 20–35 | Tasks 4–5 | **The core:** translate Pipeline → Actions with Copilot; OIDC + least privilege + SHA pins |
| 35–45 | Task 6 | Boards → Issues; field-mapping decisions |
| 45–55 | Task 7 | Local validation (build/test/scan, actionlint, markdownlint) |
| 55–60 | Debrief | Discussion questions; what good looks like |

Budget the most time for **Tasks 4–5** — pipeline translation and the security model are the point of
the challenge. Repo/Boards migration is mechanical.

## Key teaching points

- **GEI moves repos, not the rest.** Pipelines and Boards are deliberate, opinionated steps. This is a
  feature, not a gap — translation is where you *improve* the SDLC, not just lift-and-shift it.
- **Two extensions.** `gh gei` is the umbrella; `gh ado2gh` is the ADO specialization (`generate-script`,
  `rewire-pipeline`). The official ADO runbook uses `ado2gh`; the lab leads with `gh gei` per the brief.
- **PATs are scaffolding.** They exist only for the migration window: short expiry, used, deleted. The
  *running* system uses **OIDC** and holds **no** long-lived cloud secret. Hammer this contrast.
- **The migration is the upgrade moment.** The source pipeline had no format check and no vuln scan; the
  Actions workflow adds both. Migrating ≠ copying — it's the cheapest time to raise the quality bar.
- **Trial run discipline.** GEI has no delta sync. Trial into `*-sandbox`, validate, then migrate with
  work halted. Skipping the trial is the classic production scar.
- **Read the diff of trust.** Walk the `pipelines-to-actions.md` security table line by line: service
  connections → OIDC, broad token → `contents: read` + scoped `id-token: write`, `@v2` → commit SHA.

## Common pitfalls + fixes

| Pitfall | Symptom | Fix |
| --- | --- | --- |
| No Azure DevOps org | Stuck at Task 3 | Use the **bundled sample export** + `--dry-run` everywhere — this is the intended path |
| ADO OAuth disabled | GEI auth fails on a real org | Enable **Org settings → Policies → Third-party application access via OAuth** |
| Wrong PAT scopes | `403` during migrate | ADO: Code/Project&Team/Work Items/Graph (Read). GitHub: `repo`, `admin:org`, `workflow` |
| `jq` missing | `boards-to-issues.sh` errors immediately | It ships in the dev container; otherwise `apt-get install jq` or use the **PowerShell** script |
| `gh issue create --label` fails | "label not found" | The script pre-creates labels with `gh label create --force`; ensure `gh auth status` is logged in |
| Expecting CI to run | Nothing happens on push | **Actions is billing-blocked in this account** — validate locally; the workflow is correct for when it's restored |
| Editing `/infra` | Touches another workstream | Container deploy **references** Workstream B resources by name; never edit `/infra` here |
| Unpinned actions slip in | `actionlint`/review flags it | Pin every action to a full commit SHA with a `# vX` comment |

## Discussion questions

1. GEI intentionally skips Pipelines and Boards. Why is owning those translations *better* than an
   automatic converter would be?
2. Exactly which credentials existed in the "before," and what replaced each one in the "after"?
3. Why is the `deploy` job gated on `vars.AZURE_CLIENT_ID` rather than always running?
4. ADO identities don't map cleanly to GitHub logins. What did we do with `Assigned To`, and when would
   you invest in a real identity map instead?
5. What breaks if you migrate with work still in flight, given GEI has no delta sync?

## What good looks like

- Local validation is **all green**: build `-warnaserror`, tests pass, **zero** vulnerable packages,
  `actionlint` clean, `markdownlint-cli2` clean.
- The student can point at the workflow and name the **four** security wins (OIDC login, no registry
  credential, least-privilege `permissions:`, SHA-pinned actions) without prompting.
- Both `--dry-run` commands run offline and produce the expected output (correct `migrate-repo` command;
  10 work items mapped to the right labels and open/closed states).
- The student treats PATs as disposable and can articulate the trial-run-then-cutover discipline.
- They resisted editing `/infra` and instead referenced Workstream B resources by the naming contract.
