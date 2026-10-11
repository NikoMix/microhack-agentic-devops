---
description: Draft a structured incident summary from pasted alerts, logs, and signals.
agent: agent
tools: ['read', 'search', 'github/*']
argument-hint: '[SevN] [service] — paste signals in the chat'
---

# Draft an incident summary

Act as the [On-Call Incident agent](../agents/oncall-incident.agent.md). Draft an incident summary for
${input:incident:the incident described below}.

Provide as much as you have: a **title**, **severity** (Sev1/Sev2/Sev3), **affected service**, and the raw
**signals** (alert text, log excerpts, error messages, metric anomalies, a run/trace URL).

Steps:

1. Separate **facts** (straight from the signals) from **hypotheses** (your inference). Never present a
   guess as a confirmed root cause; tag each hypothesis with a confidence level.
2. Optionally use the read-only `github` tools to check whether a recent merge or workflow run plausibly
   correlates — list it as a hypothesis with its PR number, not a verdict.
3. Order suggested next steps by safety and reversibility: read-only diagnostics first, risky mitigations
   last, each flagged for human judgement.
4. If the signals are too thin, say which additional data to collect instead of speculating.

Output the Markdown incident summary (Impact · Probable cause · Timeline · Suggested next steps · Comms
blurb). Advisory only — the agent never remediates, deploys, scales, or pages; a human owns every action.
