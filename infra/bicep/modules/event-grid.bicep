// Azure Event Grid topic with Storage Queue subscriptions
// Security: RBAC-only access for publishing

@description('Name of the Event Grid topic')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Storage account name for queue subscriptions')
param storageAccountName string

@description('Principal IDs to grant EventGrid Data Sender role')
param dataSenderPrincipalIds array = []

@description('Tags to apply to resources')
param tags object = {}

// Queue names that will receive events (must exist in Storage Account)
var queueSubscriptions = [
  { name: 'analyzer-sub', queueName: 'analyzer-events', eventTypes: ['Pipeline.AnalyzeRequest'] }
  { name: 'summarizer-sub', queueName: 'summarizer-events', eventTypes: ['Pipeline.SummarizeRequest'] }
  { name: 'reviewer-sub', queueName: 'reviewer-events', eventTypes: ['Pipeline.ReviewRequest'] }
  { name: 'results-sub', queueName: 'results-events', eventTypes: ['Pipeline.Complete'] }
]

resource eventGridTopic 'Microsoft.EventGrid/topics@2023-12-15-preview' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    inputSchema: 'EventGridSchema'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true  // Enforce Entra ID authentication only
    minimumTlsVersionAllowed: '1.2'
  }
}

// Reference to existing storage account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

// Create subscriptions that route to Storage Queues
resource subscriptions 'Microsoft.EventGrid/topics/eventSubscriptions@2023-12-15-preview' = [for sub in queueSubscriptions: {
  parent: eventGridTopic
  name: sub.name
  properties: {
    destination: {
      endpointType: 'StorageQueue'
      properties: {
        resourceId: storageAccount.id
        queueName: sub.queueName
        queueMessageTimeToLiveInSeconds: 86400  // 1 day
      }
    }
    filter: {
      includedEventTypes: sub.eventTypes
    }
    eventDeliverySchema: 'EventGridSchema'
    retryPolicy: {
      maxDeliveryAttempts: 30
      eventTimeToLiveInMinutes: 1440
    }
  }
}]

// EventGrid Data Sender role assignment
var eventGridDataSenderRoleId = 'd5a91429-5739-47e2-a06b-3470a27159e7'

resource roleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in dataSenderPrincipalIds: {
  scope: eventGridTopic
  name: guid(eventGridTopic.id, principalId, eventGridDataSenderRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', eventGridDataSenderRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

@description('Event Grid topic endpoint')
output topicEndpoint string = eventGridTopic.properties.endpoint

@description('Event Grid topic resource ID')
output topicId string = eventGridTopic.id

@description('Event Grid topic managed identity principal ID')
output topicPrincipalId string = eventGridTopic.identity.principalId
