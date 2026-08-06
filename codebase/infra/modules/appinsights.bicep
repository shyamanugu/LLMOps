// appinsights.bicep — Log Analytics workspace + Application Insights.
// Central observability sink: the backend exports OpenTelemetry traces/metrics
// here via azure-monitor-opentelemetry. Workspace-based App Insights (required).

@description('Application Insights component name.')
param name string

@description('Log Analytics workspace name backing App Insights.')
param logAnalyticsName string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Log retention in days.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: retentionInDays
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    // Never disable; keep local auth off where possible (use managed identity).
    DisableLocalAuth: false
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('App Insights connection string (used by the OTel exporter).')
output connectionString string = appInsights.properties.ConnectionString
output instrumentationKey string = appInsights.properties.InstrumentationKey
output logAnalyticsId string = logAnalytics.id
output logAnalyticsCustomerId string = logAnalytics.properties.customerId
@description('Shared key for the Container Apps environment log sink.')
output logAnalyticsSharedKey string = logAnalytics.listKeys().primarySharedKey
