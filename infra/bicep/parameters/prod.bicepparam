using './main.bicep'

// Production environment parameters
param baseName = 'agents'
param environment = 'prod'
param location = 'koreacentral'
param deployContainerApps = true

param tags = {
  costCenter: 'production'
  owner: 'platform-team'
  criticality: 'high'
}
