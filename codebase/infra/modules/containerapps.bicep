// containerapps.bicep — Container Apps environment + backend and frontend apps.
// Both apps run under the shared user-assigned identity (keyless ACR pull +
// keyless access to Azure services). Backend is public via APIM; frontend is
// public. Ingress is external here — restrict backend ingress to the APIM
// subnet for defence in depth (TODO noted).

@description('Base name (prefix-env) for derived app/environment names.')
param baseName string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Resource id of the shared user-assigned managed identity.')
param userAssignedIdentityId string

@description('Client id of the shared user-assigned managed identity (for DefaultAzureCredential).')
param userAssignedClientId string

@description('ACR login server, e.g. myacr.azurecr.io. Empty = use placeholder image.')
param acrLoginServer string = ''

@description('Log Analytics workspace customer id (for the CA environment log sink).')
param logAnalyticsCustomerId string

@description('Log Analytics shared key.')
@secure()
param logAnalyticsSharedKey string

@description('App Insights connection string for OTel export.')
param appInsightsConnectionString string

@description('Non-secret environment variables injected into the backend.')
param environmentVariables object = {}

@description('Backend image tag.')
param backendImageTag string = 'latest'

@description('Frontend image tag.')
param frontendImageTag string = 'latest'

@description('Backend min/max replicas.')
param minReplicas int = 1
param maxReplicas int = 5

// Fallbacks so first-time infra deploys succeed before images exist in ACR.
var backendImage = empty(acrLoginServer) ? 'mcr.microsoft.com/k8se/quickstart:latest' : '${acrLoginServer}/llmops/backend:${backendImageTag}'
var frontendImage = empty(acrLoginServer) ? 'mcr.microsoft.com/k8se/quickstart:latest' : '${acrLoginServer}/llmops/frontend:${frontendImageTag}'

// Convert the env-var map into the Container Apps array shape.
var backendEnv = [for k in items(environmentVariables): { name: k.key, value: string(k.value) }]

resource caEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${baseName}-cae'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    zoneRedundant: false
  }
}

// Registry block only when a real ACR is provided (keyless pull via identity).
var registries = empty(acrLoginServer) ? [] : [
  { server: acrLoginServer, identity: userAssignedIdentityId }
]

// ------------------------------- backend -----------------------------------
resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${baseName}-backend'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${userAssignedIdentityId}': {} }
  }
  properties: {
    managedEnvironmentId: caEnv.id
    configuration: {
      activeRevisionsMode: 'Multiple' // required for canary traffic splitting
      registries: registries
      ingress: {
        external: true // TODO(network): restrict to APIM via ipSecurityRestrictions / internal env
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: concat(backendEnv, [
            { name: 'AZURE_CLIENT_ID', value: userAssignedClientId } // DefaultAzureCredential -> this UAMI
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'LLMOPS_APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'PORT', value: '8000' }
          ])
          probes: [
            { type: 'Liveness', httpGet: { path: '/api/v1/health', port: 8000 }, periodSeconds: 30 }
            { type: 'Readiness', httpGet: { path: '/api/v1/health', port: 8000 }, periodSeconds: 15 }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          { name: 'http-scale', http: { metadata: { concurrentRequests: '50' } } }
        ]
      }
    }
  }
}

// ------------------------------- frontend ----------------------------------
resource frontend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${baseName}-frontend'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${userAssignedIdentityId}': {} }
  }
  properties: {
    managedEnvironmentId: caEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: registries
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            // The SPA is built with VITE_API_BASE; served via nginx. At runtime it
            // points at the gateway/backend. TODO(config): set to APIM URL in prod.
            { name: 'VITE_API_BASE', value: 'https://${baseName}-backend.${caEnv.properties.defaultDomain}/api/v1' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output environmentId string = caEnv.id
output environmentDefaultDomain string = caEnv.properties.defaultDomain
output backendFqdn string = backend.properties.configuration.ingress.fqdn
output frontendFqdn string = frontend.properties.configuration.ingress.fqdn
output backendAppName string = backend.name
output frontendAppName string = frontend.name
