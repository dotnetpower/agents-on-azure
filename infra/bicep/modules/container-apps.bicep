// Azure Container Apps environment and apps for hosting agents
// Security: Managed Identity for all Azure service access

@description('Name prefix for Container Apps resources')
param name string

@description('Location for the resource')
param location string = resourceGroup().location

@description('Log Analytics workspace ID for Container Apps logs')
param logAnalyticsWorkspaceId string

@description('Tags to apply to resources')
param tags object = {}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${name}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2022-10-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2022-10-01').primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

// Agent Container App with System-Assigned Managed Identity
resource agentApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${name}-agent'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8080
        transport: 'auto'
      }
      secrets: []  // No secrets - using Managed Identity
    }
    template: {
      containers: [
        {
          name: 'agent'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'  // Placeholder
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: ''  // Will be set after deployment with MI client ID
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 10
        rules: [
          {
            name: 'queue-scaling'
            custom: {
              type: 'azure-servicebus'
              metadata: {
                queueName: 'analyzer-tasks'
                messageCount: '5'
              }
              auth: [
                {
                  secretRef: 'none'  // Uses Managed Identity
                  triggerParameter: 'connection'
                }
              ]
            }
          }
        ]
      }
    }
  }
}

@description('Container Apps environment ID')
output environmentId string = containerAppsEnvironment.id

@description('Agent app managed identity principal ID')
output agentPrincipalId string = agentApp.identity.principalId

@description('Agent app name')
output agentAppName string = agentApp.name
