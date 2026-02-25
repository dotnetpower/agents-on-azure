// Main deployment template for Agents on Azure infrastructure
// Deploys all required Azure resources with Managed Identity authentication

targetScope = 'resourceGroup'

@description('Base name for all resources (will have environment suffix appended)')
param baseName string = 'agents'

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Deploy Container Apps for hosting agents')
param deployContainerApps bool = false

@description('Tags to apply to all resources')
param tags object = {}

// Generate unique suffix from resource group ID
var uniqueSuffix = uniqueString(resourceGroup().id)
var resourcePrefix = '${baseName}-${environment}'

// Naming convention: {abbreviation}-{baseName}-{environment}-{uniqueSuffix}
var names = {
  serviceBus: 'sb-${baseName}-${uniqueSuffix}'
  eventHubs: 'eh-${baseName}-${uniqueSuffix}'
  eventGrid: 'egt-${baseName}-${uniqueSuffix}'
  openAI: 'aoai-${baseName}-${uniqueSuffix}'
  appInsights: 'appi-${baseName}-${uniqueSuffix}'
  storage: 'st${baseName}${uniqueSuffix}'  // Storage names: lowercase, no hyphens
  containerApps: 'ca-${baseName}-${uniqueSuffix}'
}

// Common tags
var commonTags = union(tags, {
  environment: environment
  project: 'agents-on-azure'
  managedBy: 'bicep'
})

// ============================================================================
// Storage Account (must be deployed first for Event Grid subscriptions)
// ============================================================================
module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    name: names.storage
    location: location
    tags: commonTags
    dataContributorPrincipalIds: deployContainerApps ? [containerApps.outputs.agentPrincipalId] : []
  }
}

// ============================================================================
// Azure OpenAI
// ============================================================================
module openAI 'modules/openai.bicep' = {
  name: 'openai-deployment'
  params: {
    name: names.openAI
    location: location
    tags: commonTags
    openaiUserPrincipalIds: deployContainerApps ? [containerApps.outputs.agentPrincipalId] : []
  }
}

// ============================================================================
// Azure Service Bus
// ============================================================================
module serviceBus 'modules/service-bus.bicep' = {
  name: 'servicebus-deployment'
  params: {
    name: names.serviceBus
    location: location
    tags: commonTags
    dataOwnerPrincipalIds: deployContainerApps ? [containerApps.outputs.agentPrincipalId] : []
  }
}

// ============================================================================
// Azure Event Hubs
// ============================================================================
module eventHubs 'modules/event-hubs.bicep' = {
  name: 'eventhubs-deployment'
  params: {
    name: names.eventHubs
    location: location
    tags: commonTags
    dataOwnerPrincipalIds: deployContainerApps ? [containerApps.outputs.agentPrincipalId] : []
  }
}

// ============================================================================
// Azure Event Grid
// ============================================================================
module eventGrid 'modules/event-grid.bicep' = {
  name: 'eventgrid-deployment'
  params: {
    name: names.eventGrid
    location: location
    tags: commonTags
    storageAccountName: storage.outputs.storageAccountName
    dataSenderPrincipalIds: deployContainerApps ? [containerApps.outputs.agentPrincipalId] : []
  }
  dependsOn: [storage]
}

// ============================================================================
// Application Insights
// ============================================================================
module appInsights 'modules/app-insights.bicep' = {
  name: 'appinsights-deployment'
  params: {
    name: names.appInsights
    location: location
    tags: commonTags
  }
}

// ============================================================================
// Container Apps (optional)
// ============================================================================
module containerApps 'modules/container-apps.bicep' = if (deployContainerApps) {
  name: 'containerapps-deployment'
  params: {
    name: names.containerApps
    location: location
    tags: commonTags
    logAnalyticsWorkspaceId: appInsights.outputs.logAnalyticsWorkspaceId
  }
  dependsOn: [appInsights]
}

// ============================================================================
// Outputs - Environment Variables for .env file
// ============================================================================

@description('Azure OpenAI endpoint')
output AZURE_OPENAI_ENDPOINT string = openAI.outputs.endpoint

@description('Azure OpenAI model deployment name')
output AZURE_OPENAI_MODEL string = openAI.outputs.deploymentName

@description('Service Bus namespace FQDN')
output AZURE_SERVICEBUS_NAMESPACE string = serviceBus.outputs.namespaceFqdn

@description('Event Hubs namespace FQDN')
output AZURE_EVENTHUB_NAMESPACE string = eventHubs.outputs.namespaceFqdn

@description('Event Grid topic endpoint')
output AZURE_EVENTGRID_ENDPOINT string = eventGrid.outputs.topicEndpoint

@description('Storage account name')
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.storageAccountName

@description('Application Insights connection string')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.outputs.connectionString

@description('Container Apps agent principal ID (for manual RBAC if needed)')
output AGENT_PRINCIPAL_ID string = deployContainerApps ? containerApps.outputs.agentPrincipalId : ''
