# =============================================================================
# Shared helpers for the Contoso Commerce ADO -> GitHub migration scripts.
# Dot-sourced by migrate-repo.ps1 and boards-to-issues.ps1.
# =============================================================================
#Requires -Version 7.0
Set-StrictMode -Version Latest

function Write-MigLog {
    [CmdletBinding()]
    [OutputType([void])]
    param([Parameter(Mandatory)][string] $Message)
    Write-Information -MessageData "[migration] $Message" -InformationAction Continue
}

function Write-MigWarning {
    [CmdletBinding()]
    [OutputType([void])]
    param([Parameter(Mandatory)][string] $Message)
    Write-Warning $Message
}

function Test-MigCommand {
    [CmdletBinding()]
    [OutputType([void])]
    param([Parameter(Mandatory)][string] $Name)
    if (-not (Get-Command -Name $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

function Get-MigLabel {
    [CmdletBinding()]
    [OutputType([string])]
    param([Parameter(Mandatory)][string] $WorkItemType)
    switch ($WorkItemType) {
        'Epic' { 'type:epic' }
        'Feature' { 'type:feature' }
        'User Story' { 'type:user-story' }
        'Bug' { 'bug' }
        'Task' { 'type:task' }
        default { 'type:work-item' }
    }
}

function Test-MigStateClosed {
    [CmdletBinding()]
    [OutputType([bool])]
    param([Parameter(Mandatory)][string] $State)
    return @('Closed', 'Done', 'Removed', 'Resolved') -contains $State
}
