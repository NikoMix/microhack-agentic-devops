# Sample Azure DevOps export

A small, self-contained snapshot of an Azure DevOps team project — **Contoso \\ Orders** — captured so
attendees **without their own Azure DevOps organization** can still complete every task in
[Challenge 01](../../docs/challenges/challenge-01-migration/). Every script in
[`../scripts/`](../scripts/) can run against this folder in `--dry-run` mode with no network access.

## What's inside

| Path | Represents | Used by |
| --- | --- | --- |
| [`boards/work-items.json`](boards/work-items.json) | Azure Boards backlog (machine-readable) | `boards-to-issues` script |
| [`boards/work-items.csv`](boards/work-items.csv) | The same backlog as an ADO "Export to CSV" file | Human reference / Excel |
| [`pipelines/azure-pipelines.yml`](pipelines/azure-pipelines.yml) | The classic build/release pipeline | Pipelines → Actions exercise |
| [`repo/README.md`](repo/README.md) | The source repository's README | Repo-migration trial run |

## Shape of a work item

```jsonc
{
  "id": 103,                         // ADO work item id
  "workItemType": "User Story",      // Epic | Feature | User Story | Bug | Task
  "title": "As a client app, I can create an order",
  "state": "Closed",                 // New | Active | Resolved | Closed | Done | Removed
  "assignedTo": "Lee Backend <lee@contoso.example>",
  "areaPath": "Contoso\\Orders",
  "iterationPath": "Contoso\\Q2",
  "tags": ["api"],
  "parent": 102,                     // parent work item id, or null
  "description": "POST /orders ..."
}
```

The data is fictional. Identities are `@contoso.example` placeholders — there is nothing to
authenticate against and no secret anywhere in this bundle.
