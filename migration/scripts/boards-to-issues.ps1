# =============================================================================
# Recreate Azure Boards work items as GitHub Issues.
#
# Reads a work-items.json export (default: the bundled sample export) and creates
# one GitHub issue per work item, mapping the work item type to a label and
# closing issues whose source state was terminal.
#
# With -DryRun it prints what it would create without calling the GitHub API,
# so it runs fully offline against migration/sample-export/boards/work-items.json.
# =============================================================================
#Requires -Version 7.0
[CmdletBinding()]
param(
    [string] $Repo,
    [string] $InputPath,
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path -Path $PSScriptRoot -ChildPath 'common.ps1')

if (-not $InputPath) {
    $InputPath = Join-Path -Path $PSScriptRoot -ChildPath '..' -AdditionalChildPath 'sample-export', 'boards', 'work-items.json'
}
if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Input file not found: $InputPath"
}
if (-not $DryRun) {
    Test-MigCommand -Name 'gh'
    if (-not $Repo) { throw '-Repo OWNER/NAME is required unless -DryRun is set.' }
}

$workItems = @(Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json)
Write-MigLog "Found $($workItems.Count) work item(s) in $InputPath"

# Pre-create the labels we map to, so `gh issue create --label` never fails.
if (-not $DryRun) {
    $labels = @(
        @{ Name = 'type:epic'; Color = '6f42c1'; Description = 'Migrated Azure Boards Epic' },
        @{ Name = 'type:feature'; Color = '1d76db'; Description = 'Migrated Azure Boards Feature' },
        @{ Name = 'type:user-story'; Color = '0e8a16'; Description = 'Migrated Azure Boards User Story' },
        @{ Name = 'type:task'; Color = 'fbca04'; Description = 'Migrated Azure Boards Task' },
        @{ Name = 'bug'; Color = 'd73a4a'; Description = 'Migrated Azure Boards Bug' }
    )
    foreach ($label in $labels) {
        & gh label create $label.Name --repo $Repo --color $label.Color --description $label.Description --force *> $null
    }
}

$created = 0
foreach ($item in $workItems) {
    $label = Get-MigLabel -WorkItemType $item.workItemType
    $closeAfter = Test-MigStateClosed -State $item.state
    $assigned = if ($item.assignedTo) { $item.assignedTo } else { 'unassigned' }
    $tags = if ($item.tags) { ($item.tags -join ', ') } else { '' }
    $parent = if ($null -ne $item.parent) { $item.parent } else { 'none' }
    $closeLabel = if ($closeAfter) { 'yes' } else { 'no' }

    $body = @"
Migrated from Azure Boards work item **#$($item.id)** ($($item.workItemType)).

$($item.description)

---
- **Original state:** $($item.state)
- **Originally assigned to:** $assigned
- **Area path:** $($item.areaPath)
- **Iteration:** $($item.iterationPath)
- **Parent work item:** $parent
- **Tags:** $tags
"@

    if ($DryRun) {
        Write-MigLog "[#$($item.id)] $($item.workItemType) -> label '$label', close after create: $closeLabel"
        Write-MigLog "        title: $($item.title)"
        continue
    }

    $issueUrl = & gh issue create --repo $Repo --title $item.title --body $body --label $label
    if (-not $issueUrl) {
        Write-MigWarning "[#$($item.id)] failed to create issue for: $($item.title)"
        continue
    }
    $created++
    Write-MigLog "[#$($item.id)] created $issueUrl"
    if ($closeAfter) {
        & gh issue close $issueUrl --reason completed *> $null
        Write-MigLog "[#$($item.id)] closed (original state: $($item.state))"
    }
}

if ($DryRun) {
    Write-MigLog "DRY RUN complete - $($workItems.Count) issue(s) would be created."
}
else {
    Write-MigLog "Done - created $created of $($workItems.Count) issue(s) in $Repo."
}
