// ===========================================================================
// main.bicep — LLMOps platform infrastructure orchestrator.
//
// Scope: resourceGroup. Create the resource group first (or via a subscription
// wrapper), then:
//   az deployment group create -g <rg> -f infra/main.bicep -p @infra/params/dev.json
//
// Design:
//   * One USER-ASSIGNED MANAGED IDENTITY is shared by both Container Apps and is
//     granted least-privilege data-plane roles on each dependency (no keys).
//   * Every module receives that identity's principalId and creates its own RBAC
//     role assignment (dependency inversion: each module owns its access grant).
//   * No secrets are passed in or stored; the backend authenticates to Azure at
//     runtime with the managed identity (DefaultAzureCredential). Endpoints are
//     surfaced as (non-secret) Container App env vars.
//   * Names are derived from a short prefix + environment + a stable unique
//     suffix so redeploys are idempotent and globally-unique where required.
// ===========================================================================

targetScope = 'resourceGroup'

// --------------------------- parameters ------------------------------------
@description('Short prefix for all resource names (3-8 chars, lowercase).')
@minLength(3)
@maxLength(8)
param namePrefix string = 'llmops'

@allowed(['dev', 'test', 'prod'])
@description('Target environment. Drives naming, SKUs and network posture.')
param environmentName string = 'dev'

@description('Azure region for all resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Existing Azure Container Registry name (images are pulled from here). Leave blank to skip ACR role assignment.')
param acrName string = ''

@description('Deploy private-endpoint / network-restricted posture (recommended for prod).')
param privateNetworking bool = false

@description('Additional resource tags merged onto every resource.')
param tags object = {}

// --------------------------- derived values --------------------------------
// Short, deterministic suffix for globally-unique names (storage, kv, cosmos…).
var suffix = toLower(substring(uniqueString(subscription().id, resourceGroup().id, environmentName), 0, 6))
var baseName = '${namePrefix}-${environmentName}'
var commonTags = union({
  application: 'llmops-platform'
  environment: environmentName
  managedBy: 'bicep'
}, tags)

// Built-in role definition IDs (data-plane, least privilege).
var roleIds = {
  openaiUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'       // Cognitive Services OpenAI User
  cognitiveUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'    // Cognitive Services User (Content Safety / Doc Intel)
  searchIndexReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f' // Search Index Data Reader
  kvSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'    // Key Vault Secrets User
  blobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'          // AcrPull
}

// --------------------------- shared identity -------------------------------
// One workload identity used by both apps and granted access to each service.
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${baseName}-id'
  location: location
  tags: commonTags
}

// Existing ACR (optional) — grant the identity pull rights.
resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = if (!empty(acrName)) {
  name: acrName
}
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(acrName)) {
  name: guid(resourceGroup().id, uami.id, roleIds.acrPull)
  scope: acr
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.acrPull)
  }
}

// --------------------------- observability ---------------------------------
module appInsights 'modules/appinsights.bicep' = {
  name: 'appinsights'
  params: {
    name: '${baseName}-appi'
    logAnalyticsName: '${baseName}-law'
    location: location
    tags: commonTags
  }
}

// --------------------------- secrets store ---------------------------------
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: take('${namePrefix}${environmentName}kv${suffix}', 24)
    location: location
    tags: commonTags
    principalId: uami.properties.principalId
    secretsUserRoleId: roleIds.kvSecretsUser
    enablePurgeProtection: environmentName == 'prod'
  }
}

// --------------------------- AI services -----------------------------------
module openai 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    name: '${baseName}-aoai-${suffix}'
    location: location
    tags: commonTags
    principalId: uami.properties.principalId
    openaiUserRoleId: roleIds.openaiUser
    publicNetworkAccess: privateNetworking ? 'Disabled' : 'Enabled'
  }
}

module search 'modules/search.bicep' = {
  name: 'search'
  params: {
    name: '${baseName}-srch-${suffix}'
    location: location
    tags: commonTags
    principalId: uami.properties.principalId
    searchReaderRoleId: roleIds.searchIndexReader
    sku: environmentName == 'prod' ? 'standard' : 'basic'
    publicNetworkAccess: privateNetworking ? 'disabled' : 'enabled'
  }
}

module contentSafety 'modules/contentsafety.bicep' = {
  name: 'contentsafety'
  params: {
    name: '${baseName}-cs-${suffix}'
    location: location
    tags: commonTags
    principalId: uami.properties.principalId
    cognitiveUserRoleId: roleIds.cognitiveUser
    publicNetworkAccess: privateNetworking ? 'Disabled' : 'Enabled'
  }
}

// --------------------------- data stores -----------------------------------
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: take('${namePrefix}${environmentName}st${suffix}', 24)
    location: location
    tags: commonTags
    principalId: uami.properties.principalId
    blobContributorRoleId: roleIds.blobDataContributor
    allowPublicAccess: !privateNetworking
  }
}

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    name: '${baseName}-cosmos-${suffix}'
    location: location
    tags: commonTags
    principalId: uami.properties.principalId
    databaseName: 'llmops'
    publicNetworkAccess: privateNetworking ? 'Disabled' : 'Enabled'
  }
}

// --------------------------- self-hosted Langfuse --------------------------
// Container App + Azure Database for PostgreSQL (observability + prompt registry).
module langfuse 'modules/[REDACTED_SQL_PASSWORD_1].bicep' = {
  name: '[REDACTED_SQL_PASSWORD_1]'
  params: {
    baseName: '${baseName}-lf'
    location: location
    tags: commonTags
    containerAppsEnvironmentId: containerApps.outputs.environmentId
    keyVaultName: keyVault.outputs.name
    postgresSkuTier: environmentName == 'prod' ? 'GeneralPurpose' : 'Burstable'
  }
}

// --------------------------- serving (Container Apps) ----------------------
module containerApps 'modules/containerapps.bicep' = {
  name: 'containerapps'
  params: {
    baseName: baseName
    location: location
    tags: commonTags
    userAssignedIdentityId: uami.id
    userAssignedClientId: uami.properties.clientId
    acrLoginServer: empty(acrName) ? '' : '${acrName}.azurecr.io'
    logAnalyticsCustomerId: appInsights.outputs.logAnalyticsCustomerId
    logAnalyticsSharedKey: appInsights.outputs.logAnalyticsSharedKey
    appInsightsConnectionString: appInsights.outputs.connectionString
    // Non-secret endpoints injected as env vars; auth is via managed identity.
    environmentVariables: {
      LLMOPS_ENVIRONMENT: environmentName
      LLMOPS_AZURE_OPENAI_ENDPOINT: openai.outputs.endpoint
      LLMOPS_AZURE_SEARCH_ENDPOINT: search.outputs.endpoint
      LLMOPS_CONTENT_SAFETY_ENDPOINT: contentSafety.outputs.endpoint
      LLMOPS_COSMOS_ENDPOINT: cosmos.outputs.endpoint
      LLMOPS_KEY_VAULT_URI: keyVault.outputs.uri
      LLMOPS_AZURE_CLIENT_ID: uami.properties.clientId
    }
    minReplicas: environmentName == 'prod' ? 2 : 0
    maxReplicas: environmentName == 'prod' ? 10 : 3
  }
}

// --------------------------- gateway (APIM) --------------------------------
module apim 'modules/apim.bicep' = {
  name: 'apim'
  params: {
    name: '${baseName}-apim-${suffix}'
    location: location
    tags: commonTags
    sku: environmentName == 'prod' ? 'Standard' : 'Developer'
    backendUrl: 'https://${containerApps.outputs.backendFqdn}'
    publisherEmail: 'platform@example.com'   // TODO(config): APIM notification email
    publisherName: 'LLMOps Platform'
  }
}

// --------------------------- outputs ---------------------------------------
output managedIdentityClientId string = uami.properties.clientId
output managedIdentityPrincipalId string = uami.properties.principalId
output backendUrl string = 'https://${containerApps.outputs.backendFqdn}'
output frontendUrl string = 'https://${containerApps.outputs.frontendFqdn}'
output apimGatewayUrl string = apim.outputs.gatewayUrl
output openAiEndpoint string = openai.outputs.endpoint
output searchEndpoint string = search.outputs.endpoint
output cosmosEndpoint string = cosmos.outputs.endpoint
output keyVaultUri string = keyVault.outputs.uri
output appInsightsConnectionString string = appInsights.outputs.connectionString
