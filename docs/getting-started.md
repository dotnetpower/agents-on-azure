# Getting Started

This guide helps you run the Agents on Azure samples in under 10 minutes.

## Prerequisites

- **Python 3.11+** installed
- **uv** package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Azure CLI** ([install](https://docs.microsoft.com/cli/azure/install-azure-cli))
- **Azure Subscription** with Contributor access

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/agents-on-azure.git
cd agents-on-azure

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

### 2. Deploy Azure Resources

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "YOUR_SUBSCRIPTION_NAME"

# Deploy infrastructure (creates .env automatically)
./infra/scripts/deploy.sh dev eastus
```

This deploys:
- Azure OpenAI with GPT-4o
- Azure Service Bus with queues
- Azure Event Hubs with topics
- Azure Event Grid with subscriptions
- Azure Storage Account
- Azure Application Insights

### 3. Run a Sample

```bash
# Navigate to a sample
cd samples/semantic-kernel/single-agent

# Run the sample
uv run python src/main.py
```

## Sample Matrix

Choose a sample based on your framework and messaging preference:

| Framework | Single Agent | Service Bus | Event Hubs | Event Grid |
|-----------|--------------|-------------|------------|------------|
| Semantic Kernel | ✅ | ✅ | ✅ | ✅ |
| LangGraph | ✅ | ✅ | ✅ | ✅ |
| AutoGen | ✅ | ✅ | ✅ | ✅ |
| MS Agent Framework | ✅ | ✅ | ✅ | ✅ |

## Running Each Sample Type

### Single Agent (No Messaging)

Simplest setup - one agent processes the document directly:

```bash
cd samples/semantic-kernel/single-agent
uv run python src/main.py
```

### Multi-Agent with Service Bus

Three agents communicate via Service Bus queues:

```bash
# Terminal 1 - Start all agents
cd samples/semantic-kernel/multi-agent-servicebus
uv run python src/main.py
```

### Multi-Agent with Event Hubs

Agents communicate via Event Hub streams:

```bash
cd samples/semantic-kernel/multi-agent-eventhub
uv run python src/main.py
```

### Multi-Agent with Event Grid

Event-driven architecture with Event Grid:

```bash
cd samples/semantic-kernel/multi-agent-eventgrid
uv run python src/main.py
```

## Microsoft Agent Framework Setup

The MS Agent Framework requires additional Azure AI Foundry setup:

### 1. Create AI Services Resource

```bash
# Create Azure AI Services with agents capability
az cognitiveservices account create \
    --name ais-agents \
    --resource-group rg-agents-on-azure \
    --kind AIServices \
    --sku S0 \
    --location eastus \
    --yes

# Deploy gpt-4o model
az cognitiveservices account deployment create \
    --name ais-agents \
    --resource-group rg-agents-on-azure \
    --deployment-name gpt-4o \
    --model-name gpt-4o \
    --model-version "2024-08-06" \
    --model-format OpenAI \
    --sku-capacity 10 \
    --sku-name GlobalStandard
```

### 2. Create AI Hub and Project

```bash
# Create AI Hub
az ml workspace create \
    --name ai-hub-agents \
    --resource-group rg-agents-on-azure \
    --location eastus \
    --kind hub

# Create Project under hub
az ml workspace create \
    --name agents-project \
    --resource-group rg-agents-on-azure \
    --location eastus \
    --kind project \
    --hub-id "/subscriptions/{SUB_ID}/resourceGroups/rg-agents-on-azure/providers/Microsoft.MachineLearningServices/workspaces/ai-hub-agents"
```

### 3. Connect AI Services to Hub

Open [Azure AI Foundry Portal](https://ai.azure.com):
1. Navigate to your Hub (ai-hub-agents)
2. Go to **Connections** > **Add Connection**
3. Select **Azure AI Services**
4. Choose your AI Services resource (ais-agents)
5. Use **AAD Authentication**

### 4. Update Environment Variable

```bash
# In your .env file:
AZURE_AI_FOUNDRY_ENDPOINT=https://ais-agents.services.ai.azure.com/api/projects/agents-project
```

### 5. Run MS Agent Framework Samples

```bash
cd samples/microsoft-agent-framework/single-agent
uv run python src/main.py
```

## Expected Output

```
=== Document Analysis Pipeline ===

Processing document: "The recent advancements in artificial intelligence..."

[Analyzer Agent]
Analyzing document...
Key topics identified: AI, machine learning, neural networks
Sentiment: Positive
Word count: 150

[Summarizer Agent]
Creating summary...
Summary: "This document discusses recent AI advancements..."

[Reviewer Agent]
Reviewing summary...
Quality score: 0.92
Recommendation: Approved

=== Pipeline Complete ===
Total time: 8.3 seconds
```

## Troubleshooting

### Authentication Errors

```
DefaultAzureCredential failed to retrieve a token
```

**Solution**: Ensure you're logged in to Azure CLI:
```bash
az login
az account show  # Verify correct subscription
```

### Missing Environment Variables

```
AZURE_OPENAI_ENDPOINT not set
```

**Solution**: Run the deployment script or create `.env` manually:
```bash
cp .env.example .env
# Edit .env with your resource endpoints
```

### Module Not Found

```
ModuleNotFoundError: No module named 'contracts'
```

**Solution**: Install from the workspace root:
```bash
cd /path/to/agents-on-azure
uv sync
```

### Permission Denied

```
azure.core.exceptions.HttpResponseError: (AuthorizationFailed)
```

**Solution**: Ensure RBAC roles are assigned:
```bash
./infra/scripts/deploy.sh dev eastus  # Re-run to assign roles
```

## Next Steps

- [Azure Setup](azure-setup.md): Manual resource provisioning
- [Architecture Overview](architecture/overview.md): System design
- [Messaging Patterns](architecture/messaging-patterns.md): Pattern details

## Cleanup

Remove all Azure resources when done:

```bash
./infra/scripts/teardown.sh rg-agents-dev
```
