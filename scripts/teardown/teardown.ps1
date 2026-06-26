#Requires -Version 7.0
<#
.SYNOPSIS
    Tear down the Contoso Commerce Agentic DevOps MicroHack lab.

.DESCRIPTION
    Deletes the ephemeral resource group and optionally purges soft-deleted
    Key Vaults / Cognitive Services and removes the GitHub OIDC app
    registration, so nothing keeps accruing cost or retention.

.EXAMPLE
    ./teardown.ps1 -ResourceGroup rg-ccmh-lab -Purge -RemoveOidc -Yes
#>
[CmdletBinding()]
param(
    [string] $ResourceGroup = 'rg-ccmh-lab',
    [string] $Subscription  = '',
    [string] $AppName       = 'id-ccmh-deploy',
    [switch] $Purge,
    [switch] $RemoveOidc,
    [switch] $NoWait,
    [switch] $Yes
)

$ErrorActionPreference = 'Stop'

function Write-Log  { param($m) Write-Host "▶ $m" -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "✓ $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Warning $m }
function Die        { param($m) Write-Host "✗ $m" -ForegroundColor Red; exit 1 }

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { Die 'Azure CLI (az) is required.' }
if (-not (az account show 2>$null)) { Die "Not logged in. Run 'az login' first." }
if ($Subscription) { az account set --subscription $Subscription }

$subName = az account show --query name -o tsv
$subId   = az account show --query id -o tsv

# ---- confirm ----------------------------------------------------------------
Write-Log 'About to tear down:'
Write-Host "    Subscription : $subName ($subId)"
Write-Host "    Resource grp : $ResourceGroup"
Write-Host "    Purge vaults : $Purge"
Write-Host "    Remove OIDC  : $RemoveOidc (app '$AppName')"
if (-not $Yes) {
    $confirm = Read-Host "Type the resource group name to confirm deletion"
    if ($confirm -ne $ResourceGroup) { Die 'Confirmation did not match. Aborting.' }
}

# ---- capture names to purge BEFORE deleting the RG --------------------------
$kvNames = @(); $csNames = @()
if ($Purge -and (az group exists -n $ResourceGroup) -eq 'true') {
    $kvNames = az keyvault list -g $ResourceGroup --query "[].name" -o tsv 2>$null
    $csNames = az cognitiveservices account list -g $ResourceGroup --query "[].name" -o tsv 2>$null
}

# ---- delete the resource group ----------------------------------------------
if ((az group exists -n $ResourceGroup) -eq 'true') {
    Write-Log "Deleting resource group '$ResourceGroup'…"
    if ($NoWait) {
        az group delete -n $ResourceGroup --yes --no-wait
        Write-Ok 'Deletion started (running in background).'
    } else {
        az group delete -n $ResourceGroup --yes
        Write-Ok 'Resource group deleted.'
    }
} else {
    Write-Warn "Resource group '$ResourceGroup' does not exist — nothing to delete."
}

# ---- purge soft-deleted resources ------------------------------------------
if ($Purge -and -not $NoWait) {
    foreach ($kv in $kvNames) {
        if (-not $kv) { continue }
        Write-Log "Purging soft-deleted Key Vault '$kv'…"
        if (az keyvault purge --name $kv 2>$null) { Write-Ok "Purged vault '$kv'" } else { Write-Warn "Could not purge vault '$kv'." }
    }
    foreach ($cs in $csNames) {
        if (-not $cs) { continue }
        $loc = az cognitiveservices account list-deleted --query "[?name=='$cs'].location | [0]" -o tsv 2>$null
        if ($loc) {
            Write-Log "Purging soft-deleted Cognitive Services '$cs'…"
            if (az cognitiveservices account purge -n $cs -g $ResourceGroup -l $loc 2>$null) { Write-Ok "Purged '$cs'" } else { Write-Warn "Could not purge '$cs'." }
        }
    }
} elseif ($Purge -and $NoWait) {
    Write-Warn '-Purge skipped because -NoWait was set (RG must finish deleting first). Re-run with -Purge only.'
}

# ---- remove OIDC app registration ------------------------------------------
if ($RemoveOidc) {
    $appId = az ad app list --display-name $AppName --query "[0].appId" -o tsv 2>$null
    if ($appId) {
        Write-Log "Deleting Entra ID app registration '$AppName' ($appId)…"
        az ad app delete --id $appId
        Write-Ok 'App registration removed (federated credentials go with it).'
    } else {
        Write-Warn "No app registration named '$AppName' found."
    }
}

# ---- verify -----------------------------------------------------------------
Write-Host ''
Write-Log 'Verification:'
Write-Host "    az group exists -n $ResourceGroup  → $(az group exists -n $ResourceGroup)"
Write-Ok 'Teardown complete. Remember to deregister any self-hosted runners in GitHub (Settings → Actions → Runners).'
