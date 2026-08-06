// contentsafety.bicep — Azure AI Content Safety (guardrails).
// Backs the guardrails engine (content_safety.py, injection Prompt Shields).
// Keyless: "Cognitive Services User" granted to the workload identity.

@description('Content Safety account name.')
param name string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Workload identity principal granted Cognitive Services User.')
param principalId string

@description('Role definition GUID for Cognitive Services User.')
param cognitiveUserRoleId string

@description('Public network access.')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

resource contentSafety 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'ContentSafety'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: true // keyless — Managed Identity only
    networkAcls: { defaultAction: publicNetworkAccess == 'Enabled' ? 'Allow' : 'Deny' }
  }
}

resource cognitiveUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(contentSafety.id, principalId, cognitiveUserRoleId)
  scope: contentSafety
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveUserRoleId)
  }
}

output id string = contentSafety.id
output name string = contentSafety.name
output endpoint string = contentSafety.properties.endpoint
