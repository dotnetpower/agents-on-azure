#!/bin/bash
# ============================================================
# Agents on Azure - Teardown Script
# ============================================================
# Deletes all Azure resources created by deploy.sh or provision.sh.
#
# Usage:
#   ./teardown.sh [dev|prod]
#   ./teardown.sh --all    # Delete all environments
#
# ============================================================

set -euo pipefail

# Default environment
ENV="${1:-dev}"

echo ""
echo "============================================================"
echo "  Agents on Azure - Resource Teardown"
echo "============================================================"
echo ""

delete_resource_group() {
    local rg_name="$1"
    
    if az group exists --name "$rg_name" --output tsv | grep -q "true"; then
        echo "==> Deleting resource group: ${rg_name}..."
        az group delete --name "$rg_name" --yes --no-wait
        echo "    Deletion initiated (running in background)"
    else
        echo "    Resource group '${rg_name}' does not exist. Skipping."
    fi
}

if [[ "$ENV" == "--all" ]]; then
    echo "WARNING: This will delete ALL Agents on Azure resource groups!"
    echo ""
    read -p "Are you sure? Type 'yes' to confirm: " CONFIRM
    
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "Aborted."
        exit 0
    fi
    
    delete_resource_group "rg-agents-on-azure-dev"
    delete_resource_group "rg-agents-on-azure-staging"
    delete_resource_group "rg-agents-on-azure-prod"
    delete_resource_group "rg-agents-on-azure"  # Legacy from provision.sh
else
    if [[ ! "$ENV" =~ ^(dev|staging|prod)$ ]]; then
        echo "Error: Invalid environment '$ENV'. Use: dev, staging, prod, or --all"
        exit 1
    fi
    
    RG="rg-agents-on-azure-${ENV}"
    
    echo "WARNING: This will delete resource group '${RG}' and all its resources!"
    echo ""
    read -p "Are you sure? Type 'yes' to confirm: " CONFIRM
    
    if [[ "$CONFIRM" != "yes" ]]; then
        echo "Aborted."
        exit 0
    fi
    
    delete_resource_group "$RG"
fi

echo ""
echo "============================================================"
echo "  Teardown Complete!"
echo "============================================================"
echo ""
echo "Note: Resource deletion runs in the background."
echo "Check status with: az group list --query \"[?starts_with(name,'rg-agents')].{Name:name,State:properties.provisioningState}\" -o table"
echo ""
