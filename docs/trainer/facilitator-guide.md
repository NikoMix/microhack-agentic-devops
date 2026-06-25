# Facilitator guide

A practical, minute-by-minute playbook for delivering the Contoso Commerce Agentic DevOps MicroHack.

## Before the day (T-minus checklist)

**T-1 week**

- [ ] Confirm every attendee has: a GitHub account with **Copilot** enabled, and an **Azure subscription** with
      Owner on at least one resource group. (See [`prerequisites.md`](prerequisites.md).)
- [ ] Confirm the deployment region (`swedencentral` default) has quota for Container Apps + the chosen model.
- [ ] Send the **pre-flight email**: link to this repo, the prerequisites page, and the "open in Codespaces" button.
- [ ] Decide the inference path for the room (default **GitHub Models** for zero Azure spend during dev; switch to
      **Azure OpenAI / Foundry** for Challenge 05's deploy).

**T-1 day**

- [ ] Re-run Challenges 00–06 yourself end-to-end. Note any UI/CLI drift in the matching `coach-notes.md`.
- [ ] Pre-create one **solution Codespace** per challenge so you can demo instantly.
- [ ] Load the [slide deck](slides-outline.md), a visible **countdown timer**, and the shared chat/Q&A channel.
- [ ] Pre-stage a **shared Azure region + naming** convention so resource names don't collide (`ccmh` prefix).

**T-30 min**

- [ ] Open the room Codespace, `az login`, `gh auth status` — confirm green on the projector.
- [ ] Post the repo link + today's checkpoints in the chat.

## Running the day

### 09:00 — Welcome & framing (30 min)

- 5 min: Who's in the room (show of hands: ADO users, GitHub users, Copilot users).
- 10 min: The Contoso Commerce story + the [before/after diagram](../../README.md). Sell the *why*.
- 10 min: The 6 reference architectures and how the challenges map to them.
- 5 min: Logistics — Codespaces, checkpoints, "ask a coach", teardown at the end.

> Teaching point: emphasize that this is the **delivery capability** an Agentic DevOps specialization audit
> looks for — they're learning to *do the engagement*, not to pass a quiz.

### Challenge blocks

For **every** challenge, run this loop:

1. **Demo (3–5 min).** Show the end state from your pre-built solution Codespace.
2. **Orient (2 min).** Open the challenge `README.md`, point at the *Success criteria*.
3. **Work (bulk).** Attendees go. Coaches float. You watch the room + chat.
4. **Checkpoint.** When ~70% hit the criteria, do a 3-min recap, then move on. Coaches catch the rest at the break.

Per-challenge teaching points, pitfalls, and "what good looks like" are in each
[`coach-notes.md`](../challenges/). Highlights:

| Challenge | Watch for | Fast unblock |
|---|---|---|
| 00 Foundation | OIDC federated-credential subject typos; wrong subscription selected | Re-run `setup-oidc.sh`; `az account set` |
| 01 Migration | `gh gei` auth/PAT scopes; ADO org access | Use the dry-run; fall back to repo export ZIP |
| 02 Runners | Runner registration token; VMSS/ARC networking egress | Use the provided Bicep + registration script |
| 03 Secure SDLC | CodeQL language autodetect; push protection blocking a demo secret | Show the bypass-with-reason flow on purpose |
| 04 Copilot + MCP | MCP server not discovered by Copilot; tool scopes | Check `.vscode/mcp.json`; restart the MCP server |
| 05 Agent service | Inference provider env vars; ACA ingress + managed identity RBAC | Switch `INFERENCE_PROVIDER=github_models` to isolate |
| 06 Agentic pipeline | Workflow `permissions:`; agent token scopes | Use the least-privilege snippet in coach notes |

### 17:00 — Wrap-up & teardown (30 min)

- 10 min: Each table shares one "I can now deliver…" takeaway.
- 10 min: Map what they built back to the 6 reference architectures + the specialization.
- 10 min: **Run teardown together** — [`scripts/teardown/teardown.sh`](../../scripts/teardown/) — and confirm
  resource groups are gone. (Cost discipline is part of the craft.)

## Recovery tactics (when a lab goes sideways)

- **Time sink on Azure provisioning?** Switch the table to GitHub Models inference and continue; deploy later.
- **Auth black hole?** Re-bootstrap OIDC; verify with `az account show` and the federated-credential subject.
- **Whole region degraded?** Move to an alternate region (`westeurope`/`eastus2`) — naming is region-agnostic.
- **Attendee far behind?** Have them check out the `solution/challenge-XX` branch to rejoin at the next checkpoint.

## Facilitator do's & don'ts

- ✅ Do narrate your thinking during demos; the *reasoning* is the lesson.
- ✅ Do keep the timer visible and call checkpoints out loud.
- ✅ Do show failures on purpose (push protection, failing CodeQL) — they're memorable.
- ❌ Don't debug one attendee for 15 minutes during a work block — hand to a coach.
- ❌ Don't let the room wait for 100% completion — protect the core path.
- ❌ Don't skip teardown — leaving resources running is the most common post-event complaint.
