# Slide deck outline

A lightweight outline you can build into PowerPoint/Google Slides/Marp. Keep slides sparse — the labs are the
content. Suggested total: ~25 slides. Speaker notes in *italics*.

## Section 0 — Open (5 slides, 09:00)

1. **Title** — "Contoso Commerce — Agentic DevOps MicroHack" + your name + date.
2. **Why we're here** — From Azure DevOps + manual ops → GitHub + Agentic DevOps on Azure.
   *Set the stakes: this is the delivery capability behind the specialization.*
3. **The Contoso Commerce story** — legacy .NET Orders API, a migration, a new Python triage agent.
   *Use the before/after diagram from the README.*
4. **The 6 reference architectures** — one line each; these are the backbone of the day.
5. **How today works** — Codespaces, 7 challenges, checkpoints, coaches, teardown.

## Section 1 — Foundations (3 slides, before Challenge 00)

6. **Control plane** — GitHub Enterprise Cloud + Entra ID + Azure landing zone.
7. **OIDC, not secrets** — federated credentials; why we never store cloud keys in CI.
   *This is the single most important security idea of the day.*
8. **Challenge 00 brief** — objectives + success criteria.

## Section 2 — Migration (2 slides, before Challenge 01)

9. **ADO → GitHub** — Repos via GitHub Enterprise Importer, Pipelines → Actions, Boards → Issues.
10. **Challenge 01 brief** — objectives + success criteria; mention Copilot-assisted pipeline translation.

## Section 3 — Runners (2 slides, before Challenge 02)

11. **Self-hosted runners on Azure** — VMSS vs Actions Runner Controller (ARC) on AKS; OIDC to Azure.
12. **Challenge 02 brief**.

## Section 4 — Secure SDLC (3 slides, before Challenge 03)

13. **The 2025 GHAS split** — GitHub **Code Security** (CodeQL + Copilot Autofix) + GitHub **Secret Protection**.
14. **Defense in depth** — Dependabot, Defender for Cloud, Key Vault, signed artifacts (cosign/SLSA).
15. **Challenge 03 brief**.

## Section 5 — Agentic dev (4 slides, before Challenges 04–05)

16. **Copilot coding agent + custom agents/skills** — `.github/agents/*.agent.md`, prompts, MCP in Copilot.
17. **What is MCP?** — tools/servers; why a custom Azure-facing MCP server is powerful (and risky).
    *Cover egress + secret model explicitly.*
18. **Modular inference** — one interface, three providers (GitHub Models / Azure OpenAI / Foundry).
    *Show the single env var switch.*
19. **Challenges 04 + 05 brief** — build the MCP server, then the Order Support agent on Container Apps.

## Section 6 — Agentic delivery (2 slides, before Challenge 06)

20. **Agents in the pipeline** — PR-triage, release-notes, on-call agents via Actions + MCP.
21. **Challenge 06 brief** *(stretch)*.

## Section 7 — Close (4 slides, 17:00)

22. **What you built** — map the day back to the 6 reference architectures.
23. **From lab to engagement** — how this becomes a customer Agentic DevOps delivery.
24. **Teardown now** — cost discipline; run the script together.
25. **Resources & next steps** — repo, specialization link, Microsoft Agent Framework, GitHub docs.

## Design notes

- One idea per slide; diagrams over bullet walls.
- Reuse the **mermaid diagrams** from the README and `agenda.md` (export to PNG for the deck).
- Keep a persistent footer: current challenge + "Success criteria on the repo".
- Have a **"Parking lot"** slide for off-topic questions so you protect the timeline.
