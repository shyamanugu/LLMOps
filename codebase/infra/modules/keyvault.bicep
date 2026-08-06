// keyvault.bicep — Key Vault for application secrets, RBAC-authorized.
// Secrets (e.g. Langfuse keys, DB passwords) live here; the workload identity is
// granted "Key Vault Secrets User" so the backend reads them at runtime with
// Managed Identity. No secrets are set by this template — they are created by
// their owning module or seeded out-of-band.

@description('Key Vault name (globally unique, 3-24 chars).')
@minLength(3)
@maxLength(24)
param name string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Principal (workload identity) granted Key Vault Secrets User.')
param principalId string

@description('Role definition GUID for Key Vault Secrets User.')
param secretsUserRoleId string

@description('Enable purge protection (recommended/required for prod).')
param enablePurgeProtection bool = false

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    // RBAC data plane (not access policies) — least privilege, auditable.
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: enablePurgeProtection ? true : null
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow' // TODO(network): set 'Deny' + private endpoint for prod
    }
  }
}

// Grant the workload identity read access to secrets.
resource secretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, principalId, secretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretsUserRoleId)
  }
}

output id string = keyVault.id
output name string = keyVault.name
output uri string = keyVault.properties.vaultUri
