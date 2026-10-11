#Requires -Version 7.0
<#
.SYNOPSIS
    Bootstrap GitHub <-> Entra ID <-> Azure OIDC for the Contoso Commerce
    Agentic DevOps MicroHack (Challenge 00).

.DESCRIPTION
    Creates (idempotently): an Entra ID app registration + service principal,
    GitHub federated credentials (no client secret), a least-privilege role
    assignment scoped to the lab resource group, and optionally the resource
    group, required resource providers, and a budget alert. No secrets are
    ever created or stored. Re-running is safe.

.EXAMPLE
    ./setup-oidc.ps1 -Repo 'my-org/microhack-agentic-devops' -CreateRg -RegisterProviders -SetGhVars
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $Repo,
    [string] $AppName        = 'id-ccmh-deploy',
    [string] $ResourceGroup  = 'rg-ccmh-lab',
    [string] $Location       = 'swedencentral',
    [string] $Subscription   = '',
    [string] $Role           = 'Contributor',
    [string] $Branch         = 'main',
    [string] $Environment    = 'lab',
    [switch] $CreateRg,
    [switch] $RegisterProviders,
    [string] $Budget         = '',
    [switch] $SetGhVars
)

$ErrorActionPreference = 'Stop'

function Write-Log  { param($m) Write-Host "▶ $m" -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "✓ $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Warning $m }
function Die        { param($m) Write-Host "✗ $m" -ForegroundColor Red; exit 1 }

$providers = @(
    'Microsoft.App','Microsoft.ContainerRegistry','Microsoft.KeyVault',
    'Microsoft.OperationalInsights','Microsoft.Insights','Microsoft.CognitiveServices',
    'Microsoft.ManagedIdentity','Microsoft.Compute','Microsoft.Network'
)

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { Die 'Azure CLI (az) is required.' }
if ($SetGhVars -and -not (Get-Command gh -ErrorAction SilentlyContinue)) { Die 'GitHub CLI (gh) is required for -SetGhVars.' }

# ---- context ----------------------------------------------------------------
Write-Log 'Resolving Azure context…'
if (-not (az account show 2>$null)) { Die "Not logged in. Run 'az login' first." }
if ($Subscription) { az account set --subscription $Subscription }
$subId    = az account show --query id -o tsv
$tenantId = az account show --query tenantId -o tsv
$subName  = az account show --query name -o tsv
Write-Ok "Subscription: $subName ($subId)"
Write-Ok "Tenant:       $tenantId"

# ---- app registration + service principal -----------------------------------
Write-Log "Ensuring app registration '$AppName'…"
$appId = az ad app list --display-name $AppName --query "[0].appId" -o tsv
if (-not $appId) {
    $appId = az ad app create --display-name $AppName --query appId -o tsv
    Write-Ok "Created app registration ($appId)"
} else {
    Write-Ok "App registration already exists ($appId)"
}

if (-not (az ad sp show --id $appId 2>$null)) {
    az ad sp create --id $appId | Out-Null
    Write-Ok 'Created service principal'
} else {
    Write-Ok 'Service principal already exists'
}

# ---- federated credentials (OIDC — no secrets) ------------------------------
function Add-Fic {
    param([string] $Name, [string] $Subject)
    $existing = az ad app federated-credential list --id $appId --query "[?name=='$Name'].name" -o tsv 2>$null
    if ($existing) { Write-Ok "Federated credential '$Name' exists"; return }
    $params = @{
        name      = $Name
        issuer    = 'https://token.actions.githubusercontent.com'
        subject   = $Subject
        audiences = @('api://AzureADTokenExchange')
        description = "GitHub OIDC for $Repo ($Name)"
    } | ConvertTo-Json -Compress
    $params | az ad app federated-credential create --id $appId --parameters '@-' | Out-Null
    Write-Ok "Added federated credential '$Name' → $Subject"
}

Write-Log "Configuring GitHub OIDC federated credentials for '$Repo'…"
Add-Fic -Name "gh-branch-$Branch" -Subject "repo:${Repo}:ref:refs/heads/$Branch"
Add-Fic -Name 'gh-pull-request'   -Subject "repo:${Repo}:pull_request"
if ($Environment) { Add-Fic -Name "gh-env-$Environment" -Subject "repo:${Repo}:environment:$Environment" }

# ---- optional: resource providers ------------------------------------------
if ($RegisterProviders) {
    Write-Log 'Registering resource providers…'
    foreach ($p in $providers) {
        $state = az provider show -n $p --query registrationState -o tsv 2>$null
        if ($state -ne 'Registered') { az provider register -n $p | Out-Null; Write-Ok "Registering $p" }
        else { Write-Ok "$p already registered" }
    }
}

# ---- optional: resource group ----------------------------------------------
if ($CreateRg) {
    if ((az group exists -n $ResourceGroup) -eq 'true') {
        Write-Ok "Resource group '$ResourceGroup' exists"
    } else {
        az group create -n $ResourceGroup -l $Location --tags purpose=microhack lifecycle=ephemeral project=ccmh | Out-Null
        Write-Ok "Created resource group '$ResourceGroup' in $Location"
    }
}

# ---- role assignment (scoped, least privilege) ------------------------------
$spObjectId = az ad sp show --id $appId --query id -o tsv
if ((az group exists -n $ResourceGroup) -eq 'true') {
    $scope = "/subscriptions/$subId/resourceGroups/$ResourceGroup"
    Write-Log "Assigning role '$Role' to the SP at RG scope…"
    $assigned = az role assignment list --assignee $appId --scope $scope --query "[?roleDefinitionName=='$Role']" -o tsv
    if ($assigned) {
        Write-Ok "Role '$Role' already assigned at $scope"
    } else {
        az role assignment create --assignee-object-id $spObjectId --assignee-principal-type ServicePrincipal --role $Role --scope $scope | Out-Null
        Write-Ok "Assigned '$Role' at $scope"
    }
} else {
    Write-Warn "Resource group '$ResourceGroup' does not exist yet — skipping role assignment. Re-run with -CreateRg."
}

# ---- optional: budget alert -------------------------------------------------
if ($Budget) {
    Write-Log "Creating monthly budget alert (£$Budget) on the resource group…"
    $start = (Get-Date -Format 'yyyy-MM-01')
    try {
        az consumption budget create --budget-name 'budget-ccmh-lab' --amount $Budget `
            --category Cost --time-grain Monthly --start-date $start --end-date '2099-12-31' `
            --resource-group $ResourceGroup | Out-Null
        Write-Ok 'Budget alert created'
    } catch {
        Write-Warn 'Could not create budget (needs Cost Management permissions) — set one in the Portal instead.'
    }
}

# ---- emit / set the three values -------------------------------------------
Write-Host ''
Write-Ok 'OIDC bootstrap complete. Set these as GitHub repository Variables (Settings → Secrets and variables → Actions → Variables) — they are non-secret IDs, so the repo holds ZERO secrets:'
Write-Host "  AZURE_CLIENT_ID=$appId"
Write-Host "  AZURE_TENANT_ID=$tenantId"
Write-Host "  AZURE_SUBSCRIPTION_ID=$subId"

if ($SetGhVars) {
    Write-Log 'Setting GitHub Actions variables via gh…'
    gh variable set AZURE_CLIENT_ID       --repo $Repo --body $appId;    Write-Ok 'Set AZURE_CLIENT_ID'
    gh variable set AZURE_TENANT_ID       --repo $Repo --body $tenantId; Write-Ok 'Set AZURE_TENANT_ID'
    gh variable set AZURE_SUBSCRIPTION_ID --repo $Repo --body $subId;     Write-Ok 'Set AZURE_SUBSCRIPTION_ID'
}

Write-Host ''
Write-Ok 'Done. Your workflows can now use azure/login with federated OIDC — no client secret required.'
