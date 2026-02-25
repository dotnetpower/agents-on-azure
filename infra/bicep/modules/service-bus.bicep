// Azure Service Bus namespace with queues for agent messaging
// Security: Local auth disabled, RBAC-only access

@description('Name of the Service Bus namespace')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Service Bus SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Standard'

@description('Principal IDs to grant Service Bus Data Owner role')
param dataOwnerPrincipalIds array = []

@description('Tags to apply to resources')
param tags object = {}

// Queue names for the pipeline
var queueNames = [
  'analyzer-tasks'
  'summarizer-tasks'
  'reviewer-tasks'
  'pipeline-results'
]

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    disableLocalAuth: true  // Enforce Entra ID authentication only
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

// Create queues for the agent pipeline
resource queues 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = [for queueName in queueNames: {
  parent: serviceBusNamespace
  name: queueName
  properties: {
    maxDeliveryCount: 10
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT1M'
    deadLetteringOnMessageExpiration: true
    requiresDuplicateDetection: false
    requiresSession: false
  }
}]

// Service Bus Data Owner role assignment
var serviceBusDataOwnerRoleId = '090c5cfd-751d-490a-894a-3ce6f1109419'

resource roleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in dataOwnerPrincipalIds: {
  scope: serviceBusNamespace
  name: guid(serviceBusNamespace.id, principalId, serviceBusDataOwnerRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', serviceBusDataOwnerRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

@description('Service Bus namespace FQDN')
output namespaceFqdn string = '${serviceBusNamespace.name}.servicebus.windows.net'

@description('Service Bus namespace resource ID')
output namespaceId string = serviceBusNamespace.id

@description('Queue names created')
output queueNames array = queueNames
