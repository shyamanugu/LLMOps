// apim.bicep — API Management gateway in front of the backend.
// Fronts the Container Apps backend, applies the policies in
// platform/gateway/apim-policies/*.xml (JWT validate, rate limit, cache, set
// backend). The gateway has a managed identity for Key Vault-backed named
// values. No secrets are stored in this template.

@description('APIM service name (globally unique).')
param name string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('APIM SKU (Developer for non-prod, Standard/Premium for prod).')
@allowed(['Developer', 'Basic', 'Standard', 'Premium'])
param sku string = 'Developer'

@description('SKU capacity (units).')
param skuCapacity int = 1

@description('Backend base URL the gateway routes to (Container Apps FQDN).')
param backendUrl string

@description('Publisher notification email.')
param publisherEmail string

@description('Publisher/org name shown in the developer portal.')
param publisherName string

resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: { name: sku, capacity: skuCapacity }
  identity: { type: 'SystemAssigned' } // for Key Vault named values
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// Named value for the backend URL (referenced as {{backend-base-url}} in policy).
resource nvBackend 'Microsoft.ApiManagement/service/namedValues@2023-05-01-preview' = {
  parent: apim
  name: 'backend-base-url'
  properties: { displayName: 'backend-base-url', value: backendUrl, secret: false }
}

// Backend registration pointing at the Container Apps ingress.
resource backend 'Microsoft.ApiManagement/service/backends@2023-05-01-preview' = {
  parent: apim
  name: 'llmops-backend'
  properties: {
    protocol: 'http'
    url: backendUrl
    // TODO(security): mutual auth / IP allow-list so only APIM reaches the app.
  }
}

// The LLMOps API surface (v1). OpenAPI import + operation policies are wired in
// CI or a follow-up deployment referencing platform/gateway/apim-policies/*.xml.
resource api 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'llmops-api'
  properties: {
    displayName: 'LLMOps API'
    path: 'llmops'
    protocols: [ 'https' ]
    subscriptionRequired: false // authn is JWT (Entra) via inbound policy, not APIM keys
    serviceUrl: backendUrl
    apiType: 'http'
  }
}

// Product-scope policy. TODO(policy): load from platform/gateway/apim-policies/
// (inbound.xml + ratelimit.xml). Inlined reference kept minimal here.
resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '<policies><inbound><base /><set-backend-service base-url="{{backend-base-url}}" /></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'
    // TODO(policy): replace with the full inbound.xml + ratelimit.xml content,
    // or deploy via `az apim api policy import --xml-path`.
  }
}

output id string = apim.id
output name string = apim.name
output gatewayUrl string = apim.properties.gatewayUrl
output apimPrincipalId string = apim.identity.principalId
