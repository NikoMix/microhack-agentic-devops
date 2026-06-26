using './runners-vmss.bicep'

// Contoso Commerce — Agentic DevOps MicroHack · Challenge 02 runner pool parameters.
// All values are non-secret. The runner registration token is NEVER here — the deploy workflow
// writes a short-lived token to Key Vault and the runners read it at boot via managed identity.

param location = 'swedencentral'
param namePrefix = 'ccmh'

param tags = {
  project: 'ccmh'
  purpose: 'microhack'
  lifecycle: 'ephemeral'
  workstream: 'infra'
  challenge: '02-runners-oidc'
}

// ── Wire to the landing-zone outputs (Challenge 00). Replace with your deployment's values:
//    az deployment group show -g rg-ccmh-lab -n <infra-deployment> --query properties.outputs
param managedIdentityResourceId = '/subscriptions/<sub-id>/resourceGroups/rg-ccmh-lab/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-ccmh-lab'
param managedIdentityClientId = '<managed-identity-client-id>'
param keyVaultName = '<kv-ccmh-xxxxxx>'
param registrationTokenSecretName = 'gh-runner-registration-token'

// ── GitHub scope the runners register against (repo-level shown):
param githubRunnerScopeUrl = 'https://github.com/NikoMix/microhack-agentic-devops'
param runnerLabels = 'self-hosted,linux,x64,ccmh,azure'
param runnerGroup = 'Default'
param runnerEphemeral = true

// ── Pinned runner binary (bump together; SHA is verified at boot):
param runnerVersion = '2.335.1'
param runnerSha256 = '4ef2f25285f0ae4477f1fe1e346db76d2f3ebf03824e2ddd1973a2819bf6c8cf'

// ── Cost-optimized compute:
param vmSku = 'Standard_B2s'
param instanceCount = 2
param useSpot = true

// ── Access (optional break-glass). Paste an SSH public key to enable key auth; leave the CIDR
//    empty to keep the pool fully closed to inbound.
param adminUsername = 'ccmhadmin'
param adminSshPublicKey = ''
param allowSshFromCidr = ''

// ── Network:
param vnetAddressPrefix = '10.80.0.0/24'
param subnetAddressPrefix = '10.80.0.0/25'
