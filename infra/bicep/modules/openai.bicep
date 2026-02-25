// Azure OpenAI Service with GPT-4o deployment
// Security: Local auth disabled, RBAC-only access

@description('Name of the Azure OpenAI resource')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('OpenAI SKU')
param sku string = 'S0'

@description('Model deployment name')
param deploymentName string = 'gpt-4o'

@description('Model name to deploy')
param modelName string = 'gpt-4o'

@description('Model version')
param modelVersion string = '2024-08-06'

@description('Tokens per minute capacity (in thousands)')
@minValue(1)
param capacityK int = 30

@description('Principal IDs to grant Cognitive Services OpenAI User role')
param openaiUserPrincipalIds array = []

@description('Tags to apply to resources')
param tags object = {}

resource openAI 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: sku
  }
  properties: {
    customSubDomainName: name
    disableLocalAuth: true  // Enforce Entra ID authentication only
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// GPT-4o deployment
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAI
  name: deploymentName
  sku: {
    name: 'Standard'
    capacity: capacityK
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}

// Cognitive Services OpenAI User role assignment
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource roleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (principalId, i) in openaiUserPrincipalIds: {
  scope: openAI
  name: guid(openAI.id, principalId, cognitiveServicesOpenAIUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUserRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

@description('Azure OpenAI endpoint')
output endpoint string = openAI.properties.endpoint

@description('Azure OpenAI resource ID')
output resourceId string = openAI.id

@description('Deployment name')
output deploymentName string = deployment.name
