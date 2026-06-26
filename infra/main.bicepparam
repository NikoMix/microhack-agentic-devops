using './main.bicep'

// Contoso Commerce — Agentic DevOps MicroHack · Challenge 00 landing zone parameters.
// All values here are non-secret. Secrets never live in IaC — runtime config is pulled from
// Key Vault via the managed identity (DefaultAzureCredential).

param location = 'swedencentral'

param namePrefix = 'ccmh'

param tags = {
  project: 'ccmh'
  purpose: 'microhack'
  lifecycle: 'ephemeral'
  workstream: 'infra'
  challenge: '00-foundation'
}

// Optional: grant a human admin / break-glass identity data-plane access (Key Vault + Foundry).
// Leave empty in CI. Set to an Entra object ID (User or Group) for hands-on lab access, e.g.:
//   az ad signed-in-user show --query id -o tsv
param adminPrincipalId = ''
param adminPrincipalType = 'User'

// Cost guard-rails for the lab.
param logAnalyticsRetentionInDays = 30
param logAnalyticsDailyQuotaGb = 1
param acrSku = 'Basic'

// Text/chat inference only — no image generation anywhere in this hack.
param chatModelDeployments = [
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
