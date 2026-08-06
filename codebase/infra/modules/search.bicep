// search.bicep — Azure AI Search (RAG index backend).
// Keyless: RBAC data-plane enabled and the workload identity granted
// "Search Index Data Reader". A system-assigned identity on the service lets it
// pull embeddings from Azure OpenAI for integrated vectorization if used.

@description('Azure AI Search service name (2-60 chars, lowercase/dash).')
param name string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Workload identity principal granted Search Index Data Reader.')
param principalId string

@description('Role definition GUID for Search Index Data Reader.')
param searchReaderRoleId string

@description('Service SKU.')
@allowed(['basic', 'standard', 'standard2', 'standard3'])
param sku string = 'basic'

@description('Public network access.')
@allowed(['enabled', 'disabled'])
param publicNetworkAccess string = 'enabled'

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: { name: sku }
  identity: { type: 'SystemAssigned' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: publicNetworkAccess
    // Keyless: force Entra (RBAC) auth for data-plane calls.
    authOptions: null
    disableLocalAuth: true
    semanticSearch: 'standard' // enables semantic ranking for higher-quality RAG
  }
}

resource searchReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, principalId, searchReaderRoleId)
  scope: search
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchReaderRoleId)
  }
}

output id string = search.id
output name string = search.name
output endpoint string = 'https://${search.name}.search.windows.net'
output searchIdentityPrincipalId string = search.identity.principalId
