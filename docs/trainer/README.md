# Train-the-Trainer — delivery kit

Everything you need to **run** the Contoso Commerce Agentic DevOps MicroHack for a room of attendees, and to
**train other facilitators** to run it. Read this page first, then the facilitator guide.

## What this microhack is (and isn't)

- **Is:** a hands-on, 1-day technical enablement that walks attendees through migrating and modernizing a real
  app on **Azure + GitHub**, with the latest agentic tooling (Copilot agents, MCP, Microsoft Agent Framework,
  modular inference).
- **Isn't:** an audit-prep workshop. The Module B *business/evidence* controls (ACR, certifications, audit
  packaging, onboarding) live in the [specialization accelerator](https://github.com/NikoMix/specialization-agentic-devops).
  Here we build the **B.1.1 capability** that the audit later references.

## Trainer kit contents

| File | Use |
| --- | --- |
| [`facilitator-guide.md`](facilitator-guide.md) | Minute-by-minute delivery playbook, room setup, recovery tactics |
| [`agenda.md`](agenda.md) | The timetable + the two delivery variants (full day / short day) |
| [`prerequisites.md`](prerequisites.md) | Attendee + trainer pre-flight, subscriptions, quotas, cost guardrails |
| [`slides-outline.md`](slides-outline.md) | Section-by-section deck outline with talking points |
| [`teardown.md`](teardown.md) | How (and when) to clean up Azure + GitHub artifacts |
| [`../challenges/`](../challenges/) | The labs attendees follow; each has a `coach-notes.md` for you |

## The Train-the-Trainer model

This microhack is designed to be **re-delivered by the people who attend it**. Run it in three passes:

1. **Pass 1 — Attend as a learner.** Complete every challenge yourself end-to-end. Keep a "friction log".
2. **Pass 2 — Shadow-facilitate.** Co-deliver one challenge block with an experienced trainer; you own the
   demo, they own recovery. Use the relevant `coach-notes.md` as your script.
3. **Pass 3 — Lead-facilitate.** Run a full day with a co-trainer on point for unblocking. Debrief with the
   [retro template](#retro--continuous-improvement).

A facilitator is "certified" to solo-deliver after one successful lead-facilitation with green attendee
outcomes (≥ 80% of attendees reach each challenge's success criteria).

## Roles in the room

| Role | Ratio | Responsibility |
| --- | --- | --- |
| Lead facilitator | 1 | Pace, demos, transitions, time-boxing |
| Floating coach | 1 per ~6 attendees | Unblock, pair-debug, watch the chat |
| Producer (optional) | 1 | Manages the slide deck, timer, and links; handles logistics |

## Pacing principles

- **Time-box hard.** Every challenge has a *core path* (must finish) and *stretch goals* (optional). Protect the
  core. Use the published [solution branches](#solutions) to fast-forward anyone who falls behind.
- **Demo → do.** Open each challenge with a 3–5 minute live demo of the end state, then let attendees work.
- **Checkpoint, don't wait.** At each checkpoint, fast movers help slow movers; don't hold the room for the last
  10%. Coaches catch stragglers during the next break.
- **Default to Codespaces.** It removes 90% of "works on my machine" issues. Local is a fallback.

## Solutions

Each challenge folder may include a `solution/` directory or a pointer to a `solution/challenge-XX` branch.
Use these to (a) demo the end-state, and (b) unblock attendees who hit a wall — have them diff their work
against the solution rather than copy-paste.

## Retro & continuous improvement

After every delivery, capture in a GitHub Issue (label `area:docs`, `type:chore`):

- Which checkpoints slipped and by how long.
- Top 3 attendee blockers + the fix you used.
- Any product/UI drift (the platforms move fast — screenshots age quickly).
- One improvement PR per delivery is the goal.

> The platforms change frequently. Before each delivery, re-run the labs yourself and reconcile any UI/CLI
> drift. The `coach-notes.md` "Known drift" sections are the first place to record changes.
