// Azure Event Hubs namespace with hubs for agent event streaming
// Security: Local auth disabled, RBAC-only access

@description('Name of the Event Hubs namespace')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Event Hubs SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Standard'

@description('Number of throughput units (Standard SKU)')
@minValue(1)
@maxValue(20)
param capacity int = 1

@description('Principal IDs to grant Event Hubs Data Owner role')
param dataOwnerPrincipalIds array = []

@description('Tags to apply to resources')
param tags object = {}

// Hub names for the pipeline stages
var hubNames = [
  'analysis-results'
  'summary-results'
  'review-results'
]

resource eventHubsNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
    tier: sku
    capacity: capacity
  }
  properties: {
    disableLocalAuth: true  // Enforce Entra ID authentication only
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    isAutoInflateEnabled: false
  }
}

// Create Event Hubs for each pipeline stage
resource eventHubs 'Microsoft.EventHub/namespaces/eventhubs@2023-01-01-preview' = [for hubName in hubNames: {
  parent: eventHubsNamespace
  name: hubName
  properties: {
    partitionCount: 2
    messageRetentionInDays: 1
  }
}]

// Consumer groups for each hub (besides $Default)
resource consumerGroups 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2023-01-01-preview' = [for hubName in hubNames: {
  parent: eventHubs[indexOf(hubNames, hubName)]
  name: 'agent-consumers'
  properties: {}
}]

// Event Hubs Data Owner role assignment
var eventHubsDataOwnerRoleId = 'f526a384-b230-433a-b45c-95f59c4a2dec'

resource roleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in dataOwnerPrincipalIds: {
  scope: eventHubsNamespace
  name: guid(eventHubsNamespace.id, principalId, eventHubsDataOwnerRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', eventHubsDataOwnerRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

@description('Event Hubs namespace FQDN')
output namespaceFqdn string = '${eventHubsNamespace.name}.servicebus.windows.net'

@description('Event Hubs namespace resource ID')
output namespaceId string = eventHubsNamespace.id

@description('Hub names created')
output hubNames array = hubNames
