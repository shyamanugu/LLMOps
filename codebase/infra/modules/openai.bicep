// openai.bicep — Azure OpenAI account + model deployments.
// The workload identity is granted "Cognitive Services OpenAI User" (data-plane,
// keyless). Deployment NAMES here must match platform/models.yaml aliases’
// right-hand side. Adjust models/capacity to your quota and region availability.

@description('Azure OpenAI account name.')
param name string

@description('Deployment region (must offer the requested models).')
param location string

@description('Resource tags.')
param tags object = {}

@description('Workload identity principal granted OpenAI User.')
param principalId string

@description('Role definition GUID for Cognitive Services OpenAI User.')
param openaiUserRoleId string

@description('Public network access (Disabled = private endpoint only).')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Model deployments to create. Names must match platform/models.yaml.')
param deployments array = [
  {
    name: 'gpt-5-mini'
    model: { format: 'OpenAI', name: 'gpt-5-mini', version: '2025-08-07' } // TODO(models): confirm version in your region
    sku: { name: 'GlobalStandard', capacity: 50 }
  }
  {
    name: 'text-embedding-3-large'
    model: { format: 'OpenAI', name: 'text-embedding-3-large', version: '1' }
    sku: { name: 'Standard', capacity: 50 }
  }
]

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: name // required for AAD token auth / private endpoints
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: true    // keyless only — force Managed Identity (Entra) auth
    networkAcls: { defaultAction: publicNetworkAccess == 'Enabled' ? 'Allow' : 'Deny' }
  }
}

// Model deployments (serial — Azure OpenAI disallows parallel deployment writes).
@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [
  for d in deployments: {
    parent: account
    name: d.name
    sku: d.sku
    properties: {
      model: d.model
      versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
      raiPolicyName: 'Microsoft.DefaultV2'
    }
  }
]

// Grant keyless data-plane access to the workload identity.
resource openaiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(account.id, principalId, openaiUserRoleId)
  scope: account
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', openaiUserRoleId)
  }
}

output id string = account.id
output name string = account.name
output endpoint string = account.properties.endpoint
