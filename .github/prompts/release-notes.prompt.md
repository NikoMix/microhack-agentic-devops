---
description: Draft Markdown release notes from the pull requests merged since the last release.
agent: agent
tools: ['read', 'search', 'github/*']
argument-hint: '[previous tag] [target tag]'
---

# Draft release notes

Act as the [Release Notes agent](../agents/release-notes.agent.md). Draft release notes for
${input:range:the range since the last release tag}.

Steps:

1. Use the read-only `github` tools to list the pull requests merged in range (number, title, author,
   labels, merge date).
2. Group each PR into exactly one category — ✨ Features, 🐛 Fixes, 🔒 Security, 📖 Docs,
   🏗️ Infrastructure, 🧹 Maintenance — driven by its `area:*` / `workstream:*` labels, falling back to the
   title. A security fix always lands under **Security**.
3. Write one verb-first bullet per PR (≤ ~120 chars) ending in `(#number)`, and lead with a short
   plain-language **highlights** paragraph.
4. Never fabricate PRs, numbers, authors, or changes. If the range is empty, return a skeleton noting
   "No merged pull requests in range."

Output Markdown ready to paste into a GitHub Release body. Draft only — tagging and publishing stay with
the `agentic-release-notes.yml` workflow and a human maintainer.
