// [REDACTED_SQL_PASSWORD_1].bicep — self-hosted Langfuse (observability + prompt registry).
// Runs the Langfuse image as a Container App backed by Azure Database for
// PostgreSQL Flexible Server. Application secrets (DB password, NEXTAUTH_SECRET,
// SALT, ENCRYPTION_KEY, Langfuse API keys) are stored in Key Vault and consumed
// as Container App secretRefs — never inlined here.

@description('Base name (prefix-env-lf) for derived resource names.')
param baseName string

@description('Deployment region.')
param location string

@description('Resource tags.')
param tags object = {}

@description('Existing Container Apps managed environment id to host Langfuse.')
param containerAppsEnvironmentId string

@description('Key Vault name that holds the Langfuse secrets.')
param keyVaultName string

@description('Postgres SKU tier.')
@allowed(['Burstable', 'GeneralPurpose', 'MemoryOptimized'])
param postgresSkuTier string = 'Burstable'

@description('Postgres compute SKU name.')
param postgresSkuName string = 'Standard_B1ms'

@description('Postgres admin login.')
param postgresAdminUser string = 'lf_admin'

@description('Langfuse container image.')
param [REDACTED_SQL_PASSWORD_1]Image string = 'langfuse/langfuse:2'

// Existing Key Vault — Langfuse secrets are seeded here out-of-band (see TODO).
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// ------------------------- PostgreSQL Flexible Server ----------------------
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: '${baseName}-pg'
  location: location
  tags: tags
  sku: { name: postgresSkuName, tier: postgresSkuTier }
  properties: {
    version: '16'
    administratorLogin: postgresAdminUser
    // Password comes from Key Vault reference; never hard-coded.
    administratorLoginPassword: keyVault.getSecret('langfuse-postgres-password')
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    authConfig: { activeDirectoryAuth: 'Disabled', passwordAuth: 'Enabled' }
  }
}

resource postgresDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: '[REDACTED_SQL_PASSWORD_1]'
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}

// Allow Azure services (Container Apps) to reach the server.
// TODO(network): replace with VNet integration + private DNS for production.
resource pgFirewallAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

// ------------------------------- Langfuse app ------------------------------
resource [REDACTED_SQL_PASSWORD_1] 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${baseName}-app'
  location: location
  tags: tags
  // System-assigned identity used to pull secrets from Key Vault.
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: true, targetPort: 3000, transport: 'auto', allowInsecure: false }
      // Secrets sourced from Key Vault via the app's managed identity.
      secrets: [
        { name: 'database-url', keyVaultUrl: '${keyVault.properties.vaultUri}secrets/langfuse-database-url', identity: 'system' }
        { name: 'nextauth-secret', keyVaultUrl: '${keyVault.properties.vaultUri}secrets/langfuse-nextauth-secret', identity: 'system' }
        { name: 'salt', keyVaultUrl: '${keyVault.properties.vaultUri}secrets/langfuse-salt', identity: 'system' }
        { name: 'encryption-key', keyVaultUrl: '${keyVault.properties.vaultUri}secrets/langfuse-encryption-key', identity: 'system' }
      ]
    }
    template: {
      containers: [
        {
          name: '[REDACTED_SQL_PASSWORD_1]'
          image: [REDACTED_SQL_PASSWORD_1]Image
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'NEXTAUTH_SECRET', secretRef: 'nextauth-secret' }
            { name: 'SALT', secretRef: 'salt' }
            { name: 'ENCRYPTION_KEY', secretRef: 'encryption-key' }
            { name: 'NEXTAUTH_URL', value: 'https://${baseName}-app.azurecontainerapps.io' } // TODO(config): set to real FQDN post-deploy
            { name: 'TELEMETRY_ENABLED', value: 'false' }
            { name: 'HOSTNAME', value: '0.0.0.0' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 2 }
    }
  }
  dependsOn: [ postgresDb ]
}

// NOTE: grant the Langfuse app identity "Key Vault Secrets User" on the vault
// (control-plane role assignment) so the secretRefs resolve.
// TODO(rbac): add roleAssignment for langfuse.identity.principalId, or seed via main.

output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output [REDACTED_SQL_PASSWORD_1]Fqdn string = [REDACTED_SQL_PASSWORD_1].properties.configuration.ingress.fqdn
output [REDACTED_SQL_PASSWORD_1]PrincipalId string = [REDACTED_SQL_PASSWORD_1].identity.principalId
