// cosmos.bicep — Azure Cosmos DB (NoSQL) for pipeline state + feedback.
// Keyless: key-based auth disabled; the workload identity is granted the
// Cosmos DB built-in DATA-PLANE "Data Contributor" role via a SQL role
// assignment (not Azure RBAC control plane). Containers use per-workload
// partition keys.

@description('Cosmos DB account name (globally unique, lowercase).')
param name string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Workload identity principal granted Cosmos data-plane contributor.')
param principalId string

@description('SQL database name.')
param databaseName string = 'llmops'

@description('Public network access.')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Containers: name + partition key path.')
param containers array = [
  { name: 'pipeline_state', partitionKey: '/trace_id' } // checkpoint/resume
  { name: 'feedback', partitionKey: '/trace_id' }       // feedback events
]

// Built-in data-plane role: Cosmos DB Built-in Data Contributor.
var dataContributorRoleId = '00000000-0000-0000-0000-000000000002'

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: name
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    disableLocalAuth: true // keyless — Entra (RBAC) data-plane only
    enableAutomaticFailover: false
    publicNetworkAccess: publicNetworkAccess
    minimalTlsVersion: 'Tls12'
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [ { locationName: location, failoverPriority: 0, isZoneRedundant: false } ]
    capabilities: [ { name: 'EnableServerless' } ] // cost-efficient for LLMOps volumes
    backupPolicy: { type: 'Continuous', continuousModeProperties: { tier: 'Continuous7Days' } }
  }
}

resource sqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmos
  name: databaseName
  properties: { resource: { id: databaseName } }
}

resource sqlContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = [
  for c in containers: {
    parent: sqlDatabase
    name: c.name
    properties: {
      resource: {
        id: c.name
        partitionKey: { paths: [ c.partitionKey ], kind: 'Hash' }
        defaultTtl: -1
      }
    }
  }
]

// Data-plane role assignment (keyless access for the workload identity).
resource dataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, principalId, dataContributorRoleId)
  properties: {
    principalId: principalId
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/${dataContributorRoleId}'
    scope: cosmos.id
  }
}

output id string = cosmos.id
output name string = cosmos.name
output endpoint string = cosmos.properties.documentEndpoint
output databaseName string = databaseName
