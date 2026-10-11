metadata name = 'Contoso Commerce — Agentic DevOps lab landing zone'
metadata description = '''
Resource-group-scoped landing zone for the Contoso Commerce Agentic DevOps MicroHack (Challenge 00).
Composes Azure Verified Modules (`br/public:avm/res/...`) into the shared platform that every later
challenge builds on: Log Analytics + Application Insights (observability), a user-assigned managed
identity (the keyless workload identity), Key Vault (RBAC mode), Azure Container Registry, an Azure
Container Apps environment, and an Azure AI Foundry account + project with a text-only chat deployment.

No secrets are created or stored. Access is granted with Azure RBAC to the managed identity so that
runtime code authenticates with Entra ID / DefaultAzureCredential. Deploy into the pre-created
`rg-ccmh-lab` resource group (see scripts/bootstrap/setup-oidc.*).
'''

targetScope = 'resourceGroup'

// ─────────────────────────────────────────────────────────────────────────────
// Parameters
// ─────────────────────────────────────────────────────────────────────────────

@description('Azure region for all resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@minLength(2)
@maxLength(8)
@description('Short, lowercase resource name prefix for the lab. Drives the deterministic names below.')
param namePrefix string = 'ccmh'

@description('Tags applied to every resource. The lifecycle tag drives the scripted teardown.')
param tags object = {
  project: 'ccmh'
  purpose: 'microhack'
  lifecycle: 'ephemeral'
  workstream: 'infra'
}

@description('''
Object ID of a human admin / break-glass principal to grant data-plane roles (Key Vault Administrator,
Cognitive Services User). Optional — leave empty in CI; set it when an attendee wants portal/CLI access
to secrets and Foundry from their own identity. Never a secret.
''')
param adminPrincipalId string = ''

@description('Principal type of adminPrincipalId. Use ServicePrincipal for an app/MI, User for a person.')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param adminPrincipalType string = 'User'

@description('Log Analytics data retention in days. 30 is the free tier and plenty for the lab.')
@minValue(30)
@maxValue(730)
param logAnalyticsRetentionInDays int = 30

@description('Daily ingestion cap (GB) for Log Analytics — bounds cost. 1 GB/day is ample for a lab.')
@minValue(1)
param logAnalyticsDailyQuotaGb int = 1

@description('Azure Container Registry SKU. Basic is the cheapest tier that supports ACR tasks.')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param acrSku string = 'Basic'

@description('Chat model deployments for the Azure AI Foundry account. Text/chat only — no image models.')
param chatModelDeployments array = [
  {
    name: 'gpt-4o-mini'
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
    sku: {
      name: 'GlobalStandard'
      capacity: 10
    }
  }
]

// ─────────────────────────────────────────────────────────────────────────────
// Names & shared values
// ─────────────────────────────────────────────────────────────────────────────

@description('Deterministic random suffix derived from the resource group — keeps globally-unique names stable across redeploys.')
var rand = take(toLower(uniqueString(resourceGroup().id)), 6)

var names = {
  logAnalytics: 'log-${namePrefix}-lab'
  appInsights: 'appi-${namePrefix}-lab'
  managedIdentity: 'id-${namePrefix}-lab'
  keyVault: 'kv-${namePrefix}-${rand}'
  containerRegistry: 'cr${namePrefix}lab${rand}'
  containerAppsEnv: 'cae-${namePrefix}-lab'
  foundryAccount: 'aif-${namePrefix}-lab'
  foundryProject: 'proj-${namePrefix}-lab'
  foundrySubdomain: 'aif-${namePrefix}-lab-${rand}'
}

// Built-in Azure role definition IDs (RBAC, least privilege).
var roleIds = {
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  keyVaultAdministrator: '00482a5a-887f-4fb3-b363-3b7fe8e74483'
  cognitiveServicesUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  cognitiveServicesOpenAIUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
}

var deployModelDeployments = [
  for (d, i) in chatModelDeployments: {
    name: d.name
    model: d.model
    sku: d.sku
  }
]

// ─────────────────────────────────────────────────────────────────────────────
// Observability — Log Analytics + Application Insights
// ─────────────────────────────────────────────────────────────────────────────

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.15.1' = {
  name: 'law-deploy'
  params: {
    name: names.logAnalytics
    location: location
    tags: tags
    skuName: 'PerGB2018'
    dataRetention: logAnalyticsRetentionInDays
    dailyQuotaGb: string(logAnalyticsDailyQuotaGb)
  }
}

module appInsights 'br/public:avm/res/insights/component:0.7.2' = {
  name: 'appi-deploy'
  params: {
    name: names.appInsights
    location: location
    tags: tags
    workspaceResourceId: logAnalytics.outputs.resourceId
    applicationType: 'web'
    kind: 'web'
    disableLocalAuth: true
    roleAssignments: [
      {
        roleDefinitionIdOrName: roleIds.monitoringMetricsPublisher
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        description: 'Workload identity publishes OpenTelemetry to App Insights keylessly (Entra).'
      }
    ]
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Workload identity — user-assigned managed identity (keyless everywhere)
// ─────────────────────────────────────────────────────────────────────────────

module managedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.5.1' = {
  name: 'uami-deploy'
  params: {
    name: names.managedIdentity
    location: location
    tags: tags
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Key Vault (RBAC mode, no access policies, no stored bootstrap secrets)
// ─────────────────────────────────────────────────────────────────────────────

module keyVault 'br/public:avm/res/key-vault/vault:0.13.3' = {
  name: 'kv-deploy'
  params: {
    name: names.keyVault
    location: location
    tags: tags
    sku: 'standard'
    enableRbacAuthorization: true
    enablePurgeProtection: false
    softDeleteRetentionInDays: 7
    enableSoftDelete: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    roleAssignments: concat(
      [
        {
          roleDefinitionIdOrName: roleIds.keyVaultSecretsUser
          principalId: managedIdentity.outputs.principalId
          principalType: 'ServicePrincipal'
          description: 'Workload identity reads runtime config + JIT runner tokens.'
        }
      ],
      empty(adminPrincipalId)
        ? []
        : [
            {
              roleDefinitionIdOrName: roleIds.keyVaultAdministrator
              principalId: adminPrincipalId
              principalType: adminPrincipalType
              description: 'Lab admin manages secrets in the portal/CLI.'
            }
          ]
    )
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Azure Container Registry
// ─────────────────────────────────────────────────────────────────────────────

module containerRegistry 'br/public:avm/res/container-registry/registry:0.12.1' = {
  name: 'acr-deploy'
  params: {
    name: names.containerRegistry
    location: location
    tags: tags
    acrSku: acrSku
    acrAdminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    roleAssignments: [
      {
        roleDefinitionIdOrName: roleIds.acrPull
        principalId: managedIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        description: 'Workload identity + runners pull images without credentials.'
      }
    ]
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Azure Container Apps environment (Consumption, workspace-based logs)
// ─────────────────────────────────────────────────────────────────────────────

module containerAppsEnv 'br/public:avm/res/app/managed-environment:0.13.3' = {
  name: 'cae-deploy'
  params: {
    name: names.containerAppsEnv
    location: location
    tags: tags
    appLogsConfiguration: {
      destination: 'azure-monitor'
    }
    zoneRedundant: false
    publicNetworkAccess: 'Enabled'
  }
}

// Keyless console/system log routing: a diagnostic setting on the environment forwards the
// 'azure-monitor' app logs to Log Analytics (no shared keys involved).
resource containerAppsEnvRef 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: names.containerAppsEnv
}

resource containerAppsEnvDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: containerAppsEnvRef
  name: 'send-to-law'
  properties: {
    workspaceId: logAnalytics.outputs.resourceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
  dependsOn: [
    containerAppsEnv
  ]
}

// ─────────────────────────────────────────────────────────────────────────────
// Azure AI Foundry — AIServices account (+ text/chat deployment) and project
// ─────────────────────────────────────────────────────────────────────────────

module foundryAccount 'br/public:avm/res/cognitive-services/account:0.15.0' = {
  name: 'aif-deploy'
  params: {
    name: names.foundryAccount
    location: location
    tags: tags
    kind: 'AIServices'
    sku: 'S0'
    customSubDomainName: names.foundrySubdomain
    allowProjectManagement: true
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    managedIdentities: {
      systemAssigned: true
    }
    deployments: deployModelDeployments
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    roleAssignments: concat(
      [
        {
          roleDefinitionIdOrName: roleIds.cognitiveServicesUser
          principalId: managedIdentity.outputs.principalId
          principalType: 'ServicePrincipal'
          description: 'Workload identity calls inference keylessly (Entra).'
        }
        {
          roleDefinitionIdOrName: roleIds.cognitiveServicesOpenAIUser
          principalId: managedIdentity.outputs.principalId
          principalType: 'ServicePrincipal'
          description: 'Workload identity calls the Azure OpenAI surface keylessly.'
        }
      ],
      empty(adminPrincipalId)
        ? []
        : [
            {
              roleDefinitionIdOrName: roleIds.cognitiveServicesUser
              principalId: adminPrincipalId
              principalType: adminPrincipalType
              description: 'Lab admin exercises the playground/CLI against Foundry.'
            }
          ]
    )
  }
}

// The AVM account module enables project management but does not create the project child resource,
// so create it natively against the account the module just deployed.
resource foundryAccountRef 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: names.foundryAccount
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundryAccountRef
  name: names.foundryProject
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'Contoso Commerce — Order Support'
    description: 'Foundry project backing the Order Support / Triage agent (modular inference).'
  }
  dependsOn: [
    foundryAccount
  ]
}

// ─────────────────────────────────────────────────────────────────────────────
// Outputs — consumed by later challenges / workstreams and the deploy workflow
// ─────────────────────────────────────────────────────────────────────────────

@description('Resource group the landing zone was deployed into.')
output resourceGroupName string = resourceGroup().name

@description('Deployment region.')
output location string = location

@description('Log Analytics workspace resource ID.')
output logAnalyticsWorkspaceResourceId string = logAnalytics.outputs.resourceId

@description('Application Insights resource name.')
output applicationInsightsName string = appInsights.outputs.name

@description('Application Insights connection string (runtime telemetry config — not a credential).')
output applicationInsightsConnectionString string = appInsights.outputs.connectionString

@description('User-assigned managed identity resource ID (attach to Container Apps + runner VMSS).')
output managedIdentityResourceId string = managedIdentity.outputs.resourceId

@description('User-assigned managed identity client ID (for az login --identity / DefaultAzureCredential).')
output managedIdentityClientId string = managedIdentity.outputs.clientId

@description('User-assigned managed identity principal (object) ID.')
output managedIdentityPrincipalId string = managedIdentity.outputs.principalId

@description('Key Vault name.')
output keyVaultName string = keyVault.outputs.name

@description('Key Vault URI.')
output keyVaultUri string = keyVault.outputs.uri

@description('Key Vault resource ID.')
output keyVaultResourceId string = keyVault.outputs.resourceId

@description('Azure Container Registry name.')
output containerRegistryName string = containerRegistry.outputs.name

@description('Azure Container Registry login server (e.g. crccmhlabxxxxxx.azurecr.io).')
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer

@description('Azure Container Registry resource ID.')
output containerRegistryResourceId string = containerRegistry.outputs.resourceId

@description('Azure Container Apps environment resource ID.')
output containerAppsEnvironmentResourceId string = containerAppsEnv.outputs.resourceId

@description('Azure Container Apps environment name.')
output containerAppsEnvironmentName string = containerAppsEnv.outputs.name

@description('Azure AI Foundry (AIServices) account name.')
output foundryAccountName string = foundryAccount.outputs.name

@description('Azure AI Foundry account endpoint (AZURE_OPENAI_ENDPOINT / AZURE_AI_FOUNDRY_PROJECT_ENDPOINT base).')
output foundryAccountEndpoint string = foundryAccount.outputs.endpoint

@description('Azure AI Foundry project name.')
output foundryProjectName string = foundryProject.name

@description('First chat model deployment name (AZURE_OPENAI_CHAT_DEPLOYMENT / AZURE_AI_FOUNDRY_CHAT_DEPLOYMENT).')
output chatDeploymentName string = length(chatModelDeployments) > 0 ? chatModelDeployments[0].name : ''
