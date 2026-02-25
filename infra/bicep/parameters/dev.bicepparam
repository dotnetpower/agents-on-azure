using './main.bicep'

// Development environment parameters
param baseName = 'agents'
param environment = 'dev'
param location = 'koreacentral'
param deployContainerApps = false

param tags = {
  costCenter: 'development'
  owner: 'platform-team'
}
