# Azure Setup Guide

This guide explains how to provision Azure resources for the Agents on Azure project.

## Overview

The project requires the following Azure resources:

| Resource | Purpose | SKU |
|----------|---------|-----|
| Azure OpenAI | LLM inference | Standard S0 |
| Service Bus | Reliable messaging | Standard |
| Event Hubs | Event streaming | Standard |
| Event Grid | Pub/sub routing | Basic |
| Storage Account | Queue endpoints, checkpoints | Standard LRS |
| Application Insights | Observability | Pay-as-you-go |
| Container Apps (optional) | Agent hosting | Consumption |

## Option 1: Automated Deployment (Recommended)

### Using the Deploy Script

```bash
# Login to Azure
az login
az account set --subscription "YOUR_SUBSCRIPTION"

# Deploy dev environment
./infra/scripts/deploy.sh dev eastus

# Deploy prod environment
./infra/scripts/deploy.sh prod eastus
```

The script:
1. Creates a resource group
2. Deploys all Azure resources via Bicep
3. Assigns RBAC roles to your user
4. Generates a `.env` file with endpoints

### Deployment Parameters

| Parameter | Dev | Prod |
|-----------|-----|------|
| Location | koreacentral | koreacentral |
| Service Bus SKU | Standard | Standard |
| Event Hubs SKU | Standard | Standard |
| Container Apps | No | Yes |

## Option 2: Manual Deployment

### Step 1: Create Resource Group

```bash
RESOURCE_GROUP="rg-agents-dev"
LOCATION="eastus"

az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 2: Deploy Azure OpenAI

```bash
OPENAI_NAME="oai-agents-dev"

# Create OpenAI resource
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0 \
  --location $LOCATION \
  --custom-domain $OPENAI_NAME \
  --disable-local-auth true

# Deploy GPT-4o model
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

### Step 3: Deploy Service Bus

```bash
SB_NAMESPACE="sb-agents-dev"

# Create namespace
az servicebus namespace create \
  --name $SB_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard \
  --disable-local-auth true

# Create queues
for queue in analyzer-tasks summarizer-tasks reviewer-tasks pipeline-results; do
  az servicebus queue create \
    --name $queue \
    --namespace-name $SB_NAMESPACE \
    --resource-group $RESOURCE_GROUP \
    --max-delivery-count 5 \
    --default-message-time-to-live P1D
done
```

### Step 4: Deploy Event Hubs

```bash
EH_NAMESPACE="eh-agents-dev"

# Create namespace
az eventhubs namespace create \
  --name $EH_NAMESPACE \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard \
  --disable-local-auth true

# Create event hubs
for hub in analysis-results summary-results review-results; do
  az eventhubs eventhub create \
    --name $hub \
    --namespace-name $EH_NAMESPACE \
    --resource-group $RESOURCE_GROUP \
    --message-retention 1 \
    --partition-count 2
done
```

### Step 5: Deploy Storage Account

```bash
STORAGE_NAME="stagentsdev"

# Create storage account
az storage account create \
  --name $STORAGE_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --allow-shared-key-access false

# Create queues for Event Grid
for queue in analyzer-events summarizer-events reviewer-events results-events; do
  az storage queue create \
    --name $queue \
    --account-name $STORAGE_NAME \
    --auth-mode login
done
```

### Step 6: Deploy Event Grid

```bash
EG_TOPIC="egt-agents-dev"

# Create Event Grid topic
az eventgrid topic create \
  --name $EG_TOPIC \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --input-schema cloudeventschemav1_0 \
  --disable-local-auth true

# Get Storage resource ID
STORAGE_ID=$(az storage account show -n $STORAGE_NAME -g $RESOURCE_GROUP --query id -o tsv)

# Create subscriptions
for item in analyzer:analyzer-events summarizer:summarizer-events reviewer:reviewer-events results:results-events; do
  IFS=':' read -r name queue <<< "$item"
  az eventgrid event-subscription create \
    --name "${name}-sub" \
    --source-resource-id $(az eventgrid topic show -n $EG_TOPIC -g $RESOURCE_GROUP --query id -o tsv) \
    --endpoint-type storagequeue \
    --endpoint "${STORAGE_ID}/queueServices/default/queues/${queue}"
done
```

### Step 7: Deploy Application Insights

```bash
APPINSIGHTS_NAME="appi-agents-dev"
WORKSPACE_NAME="log-agents-dev"

# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --workspace-name $WORKSPACE_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create Application Insights
az monitor app-insights component create \
  --app $APPINSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --workspace $(az monitor log-analytics workspace show \
    --workspace-name $WORKSPACE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query id -o tsv)
```

### Step 8: Assign RBAC Roles

```bash
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# OpenAI
az role assignment create \
  --assignee $USER_ID \
  --role "Cognitive Services OpenAI User" \
  --scope $(az cognitiveservices account show -n $OPENAI_NAME -g $RESOURCE_GROUP --query id -o tsv)

# Service Bus
az role assignment create \
  --assignee $USER_ID \
  --role "Azure Service Bus Data Owner" \
  --scope $(az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

# Event Hubs
az role assignment create \
  --assignee $USER_ID \
  --role "Azure Event Hubs Data Owner" \
  --scope $(az eventhubs namespace show -n $EH_NAMESPACE -g $RESOURCE_GROUP --query id -o tsv)

# Storage
az role assignment create \
  --assignee $USER_ID \
  --role "Storage Blob Data Contributor" \
  --scope $(az storage account show -n $STORAGE_NAME -g $RESOURCE_GROUP --query id -o tsv)

az role assignment create \
  --assignee $USER_ID \
  --role "Storage Queue Data Contributor" \
  --scope $(az storage account show -n $STORAGE_NAME -g $RESOURCE_GROUP --query id -o tsv)

# Event Grid
az role assignment create \
  --assignee $USER_ID \
  --role "EventGrid Data Sender" \
  --scope $(az eventgrid topic show -n $EG_TOPIC -g $RESOURCE_GROUP --query id -o tsv)
```

## Environment Variables

After provisioning, create `.env` in the project root:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://oai-agents-dev.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4o

# Azure Service Bus
AZURE_SERVICEBUS_NAMESPACE=sb-agents-dev.servicebus.windows.net

# Azure Event Hubs
AZURE_EVENTHUB_NAMESPACE=eh-agents-dev.servicebus.windows.net

# Azure Event Grid
AZURE_EVENTGRID_ENDPOINT=https://egt-agents-dev.eastus-1.eventgrid.azure.net/api/events

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=stagentsdev

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=...
```

## Security Checklist

Verify all security settings:

```bash
# Check local auth disabled
az cognitiveservices account show -n $OPENAI_NAME -g $RESOURCE_GROUP \
  --query "properties.disableLocalAuth"

az servicebus namespace show -n $SB_NAMESPACE -g $RESOURCE_GROUP \
  --query "disableLocalAuth"

az eventhubs namespace show -n $EH_NAMESPACE -g $RESOURCE_GROUP \
  --query "disableLocalAuth"

# Check storage shared key disabled
az storage account show -n $STORAGE_NAME -g $RESOURCE_GROUP \
  --query "allowSharedKeyAccess"
```

All should return `true` (disabled) or `false` (shared key disabled).

## Cost Estimation

| Resource | Monthly Cost (Dev) |
|----------|-------------------|
| Azure OpenAI | ~$5-50 (usage-based) |
| Service Bus | ~$10 |
| Event Hubs | ~$11 |
| Event Grid | ~$0.60/million events |
| Storage | ~$1 |
| App Insights | ~$2-10 |
| **Total** | **~$30-80** |

## Cleanup

Remove all resources:

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

Or use the teardown script:

```bash
./infra/scripts/teardown.sh rg-agents-dev
```

## Next Steps

- [Getting Started](getting-started.md): Run the samples
- [Architecture Overview](architecture/overview.md): System design
