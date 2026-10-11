metadata name = 'Contoso Commerce — self-hosted GitHub Actions runners (VMSS)'
metadata description = '''
Cost-optimized, secretless self-hosted runner pool for the Contoso Commerce Agentic DevOps MicroHack
(Challenge 02). Deploys a dedicated VNet + NSG (deny inbound) + NAT Gateway (stable, secure egress)
and a B-series **Spot** Virtual Machine Scale Set of ephemeral GitHub Actions runners.

The runners attach the landing-zone user-assigned managed identity and, at boot, read a short-lived
runner *registration token* from Key Vault via that identity (cloud-init → IMDS → Key Vault REST).
No credentials are ever placed in this template, the VMSS model, or source control.
'''

targetScope = 'resourceGroup'

// ─────────────────────────────────────────────────────────────────────────────
// Parameters
// ─────────────────────────────────────────────────────────────────────────────

@description('Azure region. Defaults to the resource group location.')
param location string = resourceGroup().location

@minLength(2)
@maxLength(8)
@description('Short, lowercase resource name prefix.')
param namePrefix string = 'ccmh'

@description('Tags applied to every resource.')
param tags object = {
  project: 'ccmh'
  purpose: 'microhack'
  lifecycle: 'ephemeral'
  workstream: 'infra'
  challenge: '02-runners-oidc'
}

@description('Resource ID of the landing-zone user-assigned managed identity (output managedIdentityResourceId).')
param managedIdentityResourceId string

@description('Client ID of the landing-zone managed identity (output managedIdentityClientId). Used by cloud-init for IMDS.')
param managedIdentityClientId string

@description('Name of the Key Vault that holds the runner registration token (output keyVaultName).')
param keyVaultName string

@description('Key Vault secret name holding the JIT runner registration token (written by the deploy workflow).')
param registrationTokenSecretName string = 'gh-runner-registration-token'

@description('GitHub scope URL the runners register against, e.g. https://github.com/<owner>/<repo> (repo) or https://github.com/<org> (org).')
param githubRunnerScopeUrl string

@description('Comma-separated runner labels. Workflows target these via runs-on.')
param runnerLabels string = 'self-hosted,linux,x64,ccmh,azure'

@description('GitHub runner group. "Default" works for repo-scoped runners.')
param runnerGroup string = 'Default'

@description('Register ephemeral runners (a clean runner per job — recommended). Set false for persistent demo runners.')
param runnerEphemeral bool = true

@description('Pinned GitHub Actions runner version (no leading v).')
param runnerVersion string = '2.335.1'

@description('SHA-256 of actions-runner-linux-x64-<version>.tar.gz (verified at boot).')
param runnerSha256 string = '4ef2f25285f0ae4477f1fe1e346db76d2f3ebf03824e2ddd1973a2819bf6c8cf'

@description('VM size. B-series burstable is cheapest for bursty CI; Spot drops cost further.')
param vmSku string = 'Standard_B2s'

@description('Number of runner instances in the pool.')
@minValue(0)
@maxValue(20)
param instanceCount int = 2

@description('Use Azure Spot capacity for maximum savings (recommended for ephemeral CI).')
param useSpot bool = true

@description('Admin username for the runner VMs.')
param adminUsername string = 'ccmhadmin'

@description('Optional SSH public key for break-glass access. Recommended. If empty, password auth stays enabled but no inbound path exists (NAT-only egress, NSG denies inbound).')
param adminSshPublicKey string = ''

@description('Optional CIDR allowed to SSH in for debugging (e.g. 203.0.113.4/32). Empty keeps the pool fully closed to inbound.')
param allowSshFromCidr string = ''

@description('VNet address space for the runner pool.')
param vnetAddressPrefix string = '10.80.0.0/24'

@description('Subnet for runner instances.')
param subnetAddressPrefix string = '10.80.0.0/25'

@secure()
@description('Optional admin password override. Leave empty to use an auto-generated value (never surfaced; password login is unreachable on this pool).')
param adminPasswordOverride string = ''

// ─────────────────────────────────────────────────────────────────────────────
// Names & derived values
// ─────────────────────────────────────────────────────────────────────────────

var names = {
  vmss: 'vmss-${namePrefix}-runners'
  vnet: 'vnet-${namePrefix}-runners'
  subnet: 'snet-runners'
  nsg: 'nsg-${namePrefix}-runners'
  natGateway: 'ng-${namePrefix}-runners'
  natPublicIp: 'pip-${namePrefix}-runners-nat'
}

var useSsh = !empty(adminSshPublicKey)

// Azure requires an auth method; password login is unreachable (no inbound, NAT-only egress).
var generatedPassword = 'Aa1!${uniqueString(resourceGroup().id, names.vmss)}${uniqueString(deployment().name, names.vmss)}'
var effectivePassword = empty(adminPasswordOverride) ? generatedPassword : adminPasswordOverride

// Inject non-secret config into the cloud-init template (registration token is NOT here —
// it is fetched at boot from Key Vault via the managed identity).
var cloudInit = replace(
  replace(
    replace(
      replace(
        replace(
          replace(
            replace(
              replace(
                replace(
                  loadTextContent('../runners/cloud-init.runner.yaml'),
                  '__GITHUB_URL__',
                  githubRunnerScopeUrl
                ),
                '__RUNNER_VERSION__',
                runnerVersion
              ),
              '__RUNNER_SHA256__',
              runnerSha256
            ),
            '__RUNNER_LABELS__',
            runnerLabels
          ),
          '__RUNNER_GROUP__',
          runnerGroup
        ),
        '__RUNNER_EPHEMERAL__',
        string(runnerEphemeral)
      ),
      '__KV_NAME__',
      keyVaultName
    ),
    '__SECRET_NAME__',
    registrationTokenSecretName
  ),
  '__UAMI_CLIENT_ID__',
  managedIdentityClientId
)

var sshSecurityRules = empty(allowSshFromCidr)
  ? []
  : [
      {
        name: 'Allow-SSH-Debug'
        properties: {
          priority: 300
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: allowSshFromCidr
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '22'
        }
      }
    ]

// ─────────────────────────────────────────────────────────────────────────────
// Network — NSG (deny inbound), NAT Gateway (secure egress), VNet/subnet
// ─────────────────────────────────────────────────────────────────────────────

module nsg 'br/public:avm/res/network/network-security-group:0.5.3' = {
  name: 'runners-nsg-deploy'
  params: {
    name: names.nsg
    location: location
    tags: tags
    securityRules: concat(sshSecurityRules, [
      {
        name: 'Deny-All-Inbound'
        properties: {
          priority: 4000
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ])
  }
}

module natGateway 'br/public:avm/res/network/nat-gateway:2.1.0' = {
  name: 'runners-natgw-deploy'
  params: {
    name: names.natGateway
    location: location
    tags: tags
    availabilityZone: 1
    publicIPAddresses: [
      {
        name: names.natPublicIp
      }
    ]
  }
}

module vnet 'br/public:avm/res/network/virtual-network:0.9.0' = {
  name: 'runners-vnet-deploy'
  params: {
    name: names.vnet
    location: location
    tags: tags
    addressPrefixes: [
      vnetAddressPrefix
    ]
    subnets: [
      {
        name: names.subnet
        addressPrefix: subnetAddressPrefix
        networkSecurityGroupResourceId: nsg.outputs.resourceId
        natGatewayResourceId: natGateway.outputs.resourceId
        privateEndpointNetworkPolicies: 'Enabled'
      }
    ]
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Runner pool — B-series Spot VMSS with cloud-init + managed identity
// ─────────────────────────────────────────────────────────────────────────────

module runnerVmss 'br/public:avm/res/compute/virtual-machine-scale-set:0.11.1' = {
  name: 'runners-vmss-deploy'
  params: {
    name: names.vmss
    location: location
    tags: tags
    osType: 'Linux'
    skuName: vmSku
    skuCapacity: instanceCount
    adminUsername: adminUsername
    adminPassword: effectivePassword
    disablePasswordAuthentication: useSsh
    publicKeys: useSsh
      ? [
          {
            keyData: adminSshPublicKey
            path: '/home/${adminUsername}/.ssh/authorized_keys'
          }
        ]
      : []
    imageReference: {
      publisher: 'Canonical'
      offer: '0001-com-ubuntu-server-jammy'
      sku: '22_04-lts-gen2'
      version: 'latest'
    }
    osDisk: {
      createOption: 'fromImage'
      diskSizeGB: 64
      managedDisk: {
        storageAccountType: 'StandardSSD_LRS'
      }
    }
    nicConfigurations: [
      {
        nicSuffix: '-nic01'
        ipConfigurations: [
          {
            name: 'ipconfig1'
            properties: {
              subnet: {
                id: vnet.outputs.subnetResourceIds[0]
              }
            }
          }
        ]
      }
    ]
    managedIdentities: {
      systemAssigned: false
      userAssignedResourceIds: [
        managedIdentityResourceId
      ]
    }
    vmPriority: useSpot ? 'Spot' : 'Regular'
    enableEvictionPolicy: useSpot
    upgradePolicyMode: 'Manual'
    bootDiagnosticEnabled: true
    customData: cloudInit
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Outputs
// ─────────────────────────────────────────────────────────────────────────────

@description('Runner VMSS resource ID.')
output runnerVmssResourceId string = runnerVmss.outputs.resourceId

@description('Runner VMSS name.')
output runnerVmssName string = runnerVmss.outputs.name

@description('Runner subnet resource ID.')
output runnerSubnetResourceId string = vnet.outputs.subnetResourceIds[0]

@description('NAT Gateway resource ID (egress).')
output natGatewayResourceId string = natGateway.outputs.resourceId
