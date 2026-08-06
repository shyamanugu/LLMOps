// storage.bicep — Storage account for RAG source documents + doc-extraction blobs.
// Keyless: shared-key auth disabled; workload identity granted
// "Storage Blob Data Contributor". TLS 1.2 enforced, no public blob access.

@description('Storage account name (3-24, lowercase alphanumeric, globally unique).')
@minLength(3)
@maxLength(24)
param name string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Workload identity principal granted Storage Blob Data Contributor.')
param principalId string

@description('Role definition GUID for Storage Blob Data Contributor.')
param blobContributorRoleId string

@description('Allow public network access (false = firewall Deny, prod posture).')
param allowPublicAccess bool = true

@description('Blob containers to create.')
param containers array = [
  'knowledge-source' // raw source content re-indexed into Azure AI Search
  'documents'        // uploads processed by extract_document
]

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false            // no anonymous blob access
    allowSharedKeyAccess: false             // keyless — Entra (RBAC) only
    publicNetworkAccess: allowPublicAccess ? 'Enabled' : 'Disabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: allowPublicAccess ? 'Allow' : 'Deny'
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 7 }
  }
}

resource blobContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for c in containers: {
    parent: blobService
    name: c
    properties: { publicAccess: 'None' }
  }
]

resource blobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, principalId, blobContributorRoleId)
  scope: storage
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobContributorRoleId)
  }
}

output id string = storage.id
output name string = storage.name
output blobEndpoint string = storage.properties.primaryEndpoints.blob
