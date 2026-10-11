# Coach notes — Challenge 06 (Agentic release pipeline)

> Trainer companion. The student lab is [`README.md`](README.md). This challenge is a **stretch / capstone**:
> run it only if the room is moving well and there is 45+ minutes left. It rewards the security discipline
> built in Challenges 02–05 by making it concrete: agents in the pipeline, still keyless, still least-privilege.

## At a glance

- **Format:** demo-led walkthrough + light hands-on. Most attendees will *read and run*, not author from
  scratch — the agent/prompt/workflow files ship in the repo.
- **Hard dependency:** GitHub Models access (default provider) **or** an Azure provider configured. If
  Actions billing is blocked (common in lab tenants), pivot to the **authoring + local-lint** path below;
  nothing here requires a live run to *teach*.
- **The one idea to land:** *agents propose, workflows act, humans approve.* If attendees leave with only
  that sentence, the challenge succeeded.

## Timing (45 min)

| Min | Segment | Notes |
| --- | --- | --- |
| 0–5 | Frame the problem | "We trust agents to suggest code. Do we trust them to merge it? No. So how do we use them safely in CI?" |
| 5–12 | Walk the safety model | Open an `.agent.md`, show `tools: ['read','search','github/*']`. Then open a workflow, show the *workflow* holds the only write scope. This is the heart of the lab. |
| 12–18 | Modular inference engine | Open `agentic-inference.yml`. Map it to the Python `InferenceClient` from Challenge 05 — same factory, different runtime. Show the keyless auth split. |
| 18–28 | Live: PR triage | Open a PR, watch the sticky comment + labels appear. Show the run Summary. Open a **fork** PR (or simulate) to show the read-only degrade. |
| 28–36 | Live: release notes + on-call | Dispatch release-notes (draft only), then `publish=true`. Label an issue `incident`, watch the draft comment. |
| 36–45 | Discuss + stretch | Trust boundary discussion questions; point at the MCP and Azure-provider stretch goals. |

If billing is blocked, compress 18–36 into a **lint + read** segment: run `actionlint` and `markdownlint-cli2`
live, then read the workflows and explain what *would* happen on each trigger.

## Key teaching points

1. **Two trust tiers, one boundary.** The agent definition (`.agent.md`) is a *capability declaration*. By
   giving it only `read`/`search`/`github/*` we make "this agent cannot write" a reviewable, version-controlled
   fact — not a hope. The workflow is the privileged actor, and its privileges are scoped per job.
2. **Modular inference is a golden rule, not a nicety.** Feature workflows never call a provider SDK directly;
   they call `agentic-inference.yml`. Swapping GitHub Models → Azure OpenAI → Foundry is a *variable change*,
   exactly like flipping `INFERENCE_PROVIDER` in the Python agent. One seam to test, secure, and reason about.
3. **Keyless everywhere.** GitHub Models uses the job's `GITHUB_TOKEN` with `models: read`. Azure providers use
   **OIDC → `azure/login` → a short-lived Entra token** minted at runtime and masked. There is no API key in a
   secret, an env file, or the logs. Tie this back to the OIDC foundation from Challenge 00/02.
4. **Untrusted input is data, never code.** PR titles/bodies/diffs and issue bodies are attacker-controllable.
   We read them through the API in `actions/github-script` and pass them to the model fenced as *untrusted
   data*; we never interpolate them into a `run:` shell (command injection) and never let them widen scope.
5. **Reversibility is the safety net.** Every default action is reversible: labels can be removed, comments
   edited, drafts ignored. The only mutating-by-default step across all three workflows is adding labels and
   posting comments. Updating a release body is **opt-in** (`publish=true`).

## Safety model (explain this slowly)

- **Trigger choice — `pull_request`, never `pull_request_target`.** `pull_request` runs the workflow defined
  in the *base* branch but with a token that is **read-only for fork PRs**. `pull_request_target` would give a
  fork's PR a *writable* token while still running base-branch workflow code — a classic privilege-escalation
  footgun the moment any untrusted value reaches a privileged step. We accept the tradeoff: **fork PRs get a
  read-only token, so triage degrades to a job-summary draft** (the `apply` job detects `pr.head.repo.fork`
  and skips labels/comment). Same-repo PRs get the full experience.
- **Empty top-level `permissions: {}`.** Every workflow starts from zero and grants scopes per job:
  `build-prompt` gets `contents: read` (+ `pull-requests: read`); the reusable engine adds `models: read`
  (and `id-token: write` only for Azure); the `apply`/`post` jobs get the *one* write scope they need
  (`pull-requests: write` or `issues: write`). No job has `write-all`; nothing has more than it uses.
- **SHA-pinned actions.** Every `uses:` is pinned to a full commit SHA with the version in a trailing comment,
  so a moved tag cannot silently change what runs. (`actions/checkout`, `actions/github-script`,
  `actions/ai-inference`, `azure/login`.)
- **Allowlist on the way out.** The triage `apply` job intersects the model's proposed labels with a fixed
  allowlist mirroring [`.github/labels.json`](../../../.github/labels.json). Even a jailbroken model cannot
  create an arbitrary label; the worst case is a wrong-but-allowlisted label, which a human reverts.
- **Defensive parsing.** The model is asked for minified JSON; the apply step tolerates fences/stray prose and
  **falls back to `risk: medium` for human review** if parsing fails. The pipeline never hard-crashes on a
  bad generation.

### What the agents can and cannot do

| Can | Cannot |
| --- | --- |
| Read PR/issue/release metadata via the read-only `github` tools | Merge, approve, close, or push |
| Propose labels, risk, notes, incident drafts | Apply anything itself (the *workflow* applies, from an allowlist) |
| Be invoked in Copilot Chat / CLI by a human | Call a provider SDK directly or reach the network beyond `github/*` |
| Run on every same-repo PR push | Get a writable token on a fork PR |

## Schema references (cite these — the issue requires it)

The custom-agent and prompt frontmatter in this challenge was authored against the official schemas, verified
at build time:

- **Custom agents (`*.agent.md`)** — GitHub Docs, *Custom agents configuration reference*:
  <https://docs.github.com/en/copilot/reference/custom-agents-configuration>. Fields used: `name`,
  `description` (required), `target: github-copilot`, `tools`, `disable-model-invocation`, `user-invocable`,
  `metadata`. (The legacy `infer` field is retired; do not reintroduce it.)
- **Prompt / skill files (`*.prompt.md`)** — VS Code docs, *Prompt files*:
  <https://code.visualstudio.com/docs/agent-customization/prompt-files>. Fields used: `description`, `agent`,
  `tools`, `argument-hint`, with `${input:...}` placeholders and relative links to the agent definitions.
- **Inference action** — [`actions/ai-inference`](https://github.com/actions/ai-inference) `@v2.1.1`. Note its
  default `max-tokens` is only 200, so we set `max-completion-tokens` explicitly on every call.
- **Reference example** the issue pointed at:
  [`NikoMix/specialization-agentic-devops` → `.github/agents/engagement-agent.agent.md`](https://github.com/NikoMix/specialization-agentic-devops/blob/main/.github/agents/engagement-agent.agent.md).

## The `GH_MODELS_MODEL` naming gotcha

The app-wide modular-inference contract names the GitHub Models model env `GITHUB_MODELS_MODEL`. **GitHub
Actions forbids repository/organization variables (and secrets) that start with the `GITHUB_` prefix** — it is
reserved. So inside the workflows that env maps to the repository variable **`GH_MODELS_MODEL`**. Call this
out explicitly; attendees *will* try to `gh variable set GITHUB_MODELS_MODEL` and get a confusing rejection.
All other variables keep their documented names (`INFERENCE_PROVIDER`, `AZURE_OPENAI_ENDPOINT`, etc.).

## Azure-provider caveat (be honest about this)

The **validated, runnable default is GitHub Models** — it needs no Azure setup and costs nothing. The Azure
paths (`azure_openai`, `foundry`) are wired keylessly (OIDC → Entra token on the
`https://cognitiveservices.azure.com` resource) and are correct in shape, but the exact endpoint/path and
`api-version` handling that `actions/ai-inference` expects can vary by provider:

- **Azure AI Foundry** exposes an `azure-ai-inference`-compatible surface
  (`https://<proj>.services.ai.azure.com/models`) and is the closest fit for this action.
- **Azure OpenAI** uses deployment-scoped paths and an `?api-version=` query parameter; depending on the action
  version you may need to encode that into the endpoint variable.

Because lab CI may be billing-blocked, treat Azure as a **stretch** and verify the precise request shape against
the **Challenge 05 `InferenceClient`**, which is the source of truth for per-provider wiring. Do not claim the
Azure path is "tested" in the room unless you have actually run it in your tenant.

## Cross-dependency wiring (integration)

This workstream deliberately owns only `.github/agents/**`, `.github/prompts/**`,
`.github/workflows/agentic-*.yml`, and this challenge folder. Two integrations land when sibling workstreams
merge:

### Workstream E (#6) — custom MCP server (`/mcp/**`)

E's custom MCP server (`mcp/contoso-orders-mcp`) ships read-only order/inventory tools. The **on-call**
agent is already wired to it via an `mcp-servers` block in `oncall-incident.agent.md`, so an incident can be
correlated with affected orders/SKUs. The exact frontmatter addition:

```yaml
mcp-servers:
  contoso-orders:
    type: 'local'
    command: 'uv'
    args: ['run', '--project', 'mcp/contoso-orders-mcp', 'contoso-orders-mcp']
    tools: ['get_order', 'lookup_inventory', 'get_order_history']
```

Those tool names must also appear in the agent's top-level `tools:` list as `contoso-orders/*`. Keep the
agent read-only: only expose **read** MCP tools, never mutating ones. The default offline repository needs
no secrets; for the live Azure path set `ORDERS_API_BASE_URL` via a `COPILOT_MCP_*` agents variable.

### Workstream D (#2) — Secure SDLC (`security-*.yml`, Dependabot, CodeQL)

Feed security signals into triage and release-notes once D merges:

- **Triage risk:** in `agentic-pr-triage.yml`'s `build-prompt`, add a step that reads open Dependabot/CodeQL
  alerts for the PR's head SHA and appends a `Security signals:` block to the prompt, so the agent can raise
  risk when a change touches a flagged area.
- **Release-notes provenance:** have the release-notes prompt note when a PR carries `area:security` /
  `workstream:secure-sdlc` so the Security section cites the fix.

Do **not** edit D's or E's paths in this PR — reference them here and wire at integration.

## Common pitfalls + fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `gh variable set GITHUB_MODELS_MODEL` rejected | `GITHUB_` prefix is reserved in Actions | Use `GH_MODELS_MODEL` (see the naming note above) |
| Triage runs but adds no labels / no comment on a PR | It's a **fork** PR → read-only token | Expected. Read the draft in the run **Summary**; full apply only on same-repo PRs |
| `Resource not accessible by integration` in `apply` | Missing `pull-requests: write` on that job, or org policy restricts default `GITHUB_TOKEN` | Confirm the job's `permissions:`; check **Settings → Actions → Workflow permissions** |
| Azure provider step 401/404 | Endpoint/api-version mismatch or missing `id-token: write` | Add `id-token: write` to the caller; verify the endpoint shape against Challenge 05; start on GitHub Models |
| `actions/ai-inference` returns a truncated answer | Default `max-tokens` is 200 | We set `max-completion-tokens` per call; raise it for long release notes |
| Model returns prose instead of JSON (triage) | LLM ignored the format instruction | The apply step parses defensively and falls back to `risk: medium`; re-run, or tighten the system prompt |
| `actionlint` flags a `${{ }}` in a `run:` | Untrusted/dynamic value interpolated into shell | Pass it via `env:` and reference `$VAR`; we never inline PR text into shells |
| A reusable-workflow job has `steps:` | A job that `uses:` a workflow cannot also define steps | Keep the 3-job split: build-prompt → (uses: inference) → apply |

## Discussion questions

1. Where exactly is the trust boundary in this design? If the model were fully compromised, what is the worst
   it could do — and which control stops each escalation?
2. Why `pull_request` and not `pull_request_target`? What capability do we lose, and is the tradeoff right for
   a public repo? For a private one?
3. We let the workflow *create* labels that do not exist yet (idempotently). Is that the right call, or should
   missing labels fail the run? What does each choice optimize for?
4. The on-call agent drafts an incident summary but takes no action. At what severity, if ever, would you let
   an agent take an *automated* mitigation — and what guardrails would that demand?
5. Modular inference lets you swap providers with a variable. What new testing, cost, and data-residency
   questions does that flexibility create?

## What good looks like

- An attendee can point at a line in an `.agent.md` and a line in a workflow and say *"this is why the agent
  can't merge, and this is the only thing that can apply a label."*
- They run the PR-triage flow, get a sensible risk + allowlisted labels, and can explain the fork-PR degrade
  without prompting.
- They flip `INFERENCE_PROVIDER` (at least conceptually) and articulate that **nothing else changes** —
  same workflow, same prompts, keyless auth.
- They leave able to repeat the sentence that matters: **agents propose, least-privilege workflows act,
  humans approve.**
