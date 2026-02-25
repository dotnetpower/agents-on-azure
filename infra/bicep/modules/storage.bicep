// Azure Storage Account for Event Grid queue subscriptions and checkpoints
// Security: Shared key access disabled, RBAC-only

@description('Name of the Storage Account (must be globally unique)')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_ZRS'])
param sku string = 'Standard_LRS'

@description('Principal IDs to grant Storage Blob/Queue Data Contributor role')
param dataContributorPrincipalIds array = []

@description('Tags to apply to resources')
param tags object = {}

// Queue names for Event Grid subscriptions
var queueNames = [
  'analyzer-events'
  'summarizer-events'
  'reviewer-events'
  'results-events'
]

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowSharedKeyAccess: false  // Enforce Entra ID authentication only
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
    allowBlobPublicAccess: false
  }
}

resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

// Create queues for Event Grid subscriptions
resource queues 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-01-01' = [for queueName in queueNames: {
  parent: queueService
  name: queueName
}]

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

// Container for Event Hubs checkpoints
resource checkpointContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'eventhub-checkpoints'
  properties: {
    publicAccess: 'None'
  }
}

// Storage Blob Data Contributor role
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
// Storage Queue Data Contributor role
var storageQueueDataContributorRoleId = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'

resource blobRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in dataContributorPrincipalIds: {
  scope: storageAccount
  name: guid(storageAccount.id, principalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

resource queueRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in dataContributorPrincipalIds: {
  scope: storageAccount
  name: guid(storageAccount.id, principalId, storageQueueDataContributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageQueueDataContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

@description('Storage account name')
output storageAccountName string = storageAccount.name

@description('Storage account resource ID')
output storageAccountId string = storageAccount.id

@description('Queue names created')
output queueNames array = queueNames
