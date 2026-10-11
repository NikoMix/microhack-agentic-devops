# =============================================================================
# Migrate one Azure DevOps Git repository to GitHub with GitHub Enterprise
# Importer (the `gh gei` extension).
#
# With -DryRun the script validates prerequisites and prints the exact command
# instead of executing it, so it is safe to run during the lab with no source
# Azure DevOps organization and no network access.
# =============================================================================
#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string] $AdoOrg,
    [Parameter(Mandatory)][string] $AdoTeamProject,
    [Parameter(Mandatory)][string] $AdoRepo,
    [Parameter(Mandatory)][string] $GithubOrg,
    [Parameter(Mandatory)][string] $GithubRepo,
    [ValidateSet('private', 'internal', 'public')][string] $TargetVisibility = 'private',
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path -Path $PSScriptRoot -ChildPath 'common.ps1')

# Required ADO_PAT scopes: Code (Read), Project and Team (Read), Work Items (Read), Graph (Read).
# Required GH_PAT scopes:  repo, admin:org, workflow.

Test-MigCommand -Name 'gh'

$extensions = & gh extension list 2>$null
if (-not ($extensions -match 'gh-gei')) {
    Write-MigWarning 'The gh-gei extension is not installed. Install it with: gh extension install github/gh-gei'
}

$ghArgs = @(
    'gei', 'migrate-repo',
    '--ado-org', $AdoOrg,
    '--ado-team-project', $AdoTeamProject,
    '--ado-repo', $AdoRepo,
    '--github-org', $GithubOrg,
    '--github-repo', $GithubRepo,
    '--target-repo-visibility', $TargetVisibility
)

if ($DryRun) {
    Write-MigLog 'DRY RUN - no migration will be performed.'
    Write-MigLog 'Would run (PATs are read from $env:ADO_PAT and $env:GH_PAT):'
    Write-MigLog ('  gh ' + ($ghArgs -join ' '))
    if ($env:ADO_PAT) { Write-MigLog 'ADO_PAT is set.' } else { Write-MigWarning 'ADO_PAT is not set.' }
    if ($env:GH_PAT) { Write-MigLog 'GH_PAT is set.' } else { Write-MigWarning 'GH_PAT is not set.' }
    return
}

if (-not $env:ADO_PAT) { throw 'Required environment variable is not set: ADO_PAT' }
if (-not $env:GH_PAT) { throw 'Required environment variable is not set: GH_PAT' }

Write-MigLog "Migrating $AdoOrg/$AdoTeamProject/$AdoRepo -> $GithubOrg/$GithubRepo"
& gh @ghArgs
Write-MigLog 'Migration submitted. Review the migration log in the destination organization.'
