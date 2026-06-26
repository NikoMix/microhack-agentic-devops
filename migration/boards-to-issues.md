# Boards → Issues

GitHub Enterprise Importer moves repositories, not **Azure Boards**. There is no first-party Boards
importer, so we recreate work items as **GitHub Issues** from an export. The
[`boards-to-issues`](scripts/) scripts do this from a `work-items.json` file and run fully offline
against the bundled [`sample-export`](sample-export/boards/).

## Field mapping

| Azure Boards field | GitHub Issue | Mapping rule |
| --- | --- | --- |
| Title | Issue title | Verbatim |
| Description | Issue body | Verbatim, followed by a metadata footer |
| Work Item Type | Label | `Epic→type:epic`, `Feature→type:feature`, `User Story→type:user-story`, `Bug→bug`, `Task→type:task` |
| State | Open / closed | `Closed`/`Done`/`Removed`/`Resolved` → **closed**; everything else → **open** |
| Assigned To | Body footer | Preserved as text (ADO identities rarely map 1:1 to GitHub logins) |
| Area Path | Body footer | Preserved as text (use labels or a Project if you need to filter) |
| Iteration Path | Body footer | Preserved as text (or map to a GitHub **Milestone**) |
| Tags | Body footer | Preserved as text (promote to labels in a stretch goal) |
| Parent | Body footer | Preserved as text (rebuild hierarchy with **sub-issues** or a Project as a stretch goal) |

### Why metadata goes in the body

ADO identities, area paths, and iterations don't have reliable GitHub equivalents, and silently dropping
them loses traceability. Writing them into a footer keeps every issue auditable and lets you decide
later which fields are worth promoting to **labels**, **milestones**, or **Project fields**.

## How to run it

```bash
# Offline: print the plan from the bundled export — no API calls, no source org
./scripts/boards-to-issues.sh --dry-run

# Live: create issues in a real repo (labels are auto-created first)
./scripts/boards-to-issues.sh --repo OWNER/orders-api

# Use your own export instead of the bundled sample
./scripts/boards-to-issues.sh --repo OWNER/orders-api --input ./my-work-items.json
```

```powershell
./scripts/boards-to-issues.ps1 -DryRun
./scripts/boards-to-issues.ps1 -Repo OWNER/orders-api
./scripts/boards-to-issues.ps1 -Repo OWNER/orders-api -InputPath ./my-work-items.json
```

## Producing a `work-items.json` from a real organization

The bundled sample is hand-authored. From a live org, query the Azure DevOps Analytics/WIQL API (or
**Boards → Export to CSV**) and shape the result to the schema in
[`sample-export/README.md`](sample-export/README.md). For example, with the `az` CLI + the
`azure-devops` extension:

```bash
az boards query --wiql "SELECT [System.Id] FROM workitems WHERE [System.TeamProject] = 'Orders'" \
  --output json > raw.json
# Then project raw.json into the {id,workItemType,title,state,assignedTo,areaPath,
# iterationPath,tags,parent,description} shape the scripts expect.
```

## Verify after a live run

```bash
gh issue list  --repo OWNER/orders-api --state all --limit 100
gh label list  --repo OWNER/orders-api
```

You should see one issue per work item, the five mapped labels, and the items that were `Closed`/`Done`
in Boards already closed in GitHub.
