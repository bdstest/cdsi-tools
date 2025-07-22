#!/bin/bash
# CDSI Quick Deployment Script
# Automated cloud bridge deployment with competitive pricing
# Author: bdstest
# Copyright: 2025 CDSI - Compliance Data Systems Insights

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

# Banner
echo -e "${BLUE}"
echo "==========================================="
echo "  CDSI Cloud Bridge Quick Deployment"
echo "  Competitive Hybrid/On-Prem Solution"
echo "  Author: bdstest"
echo "==========================================="
echo -e "${NC}"

# Default values
CUSTOMER_ID=""
DEPLOYMENT_SIZE="small"
CLOUD_PROVIDER="linode"  # Most cost-effective
BRIDGE_ARCHITECTURE="reverse_tunnel"
REGION="us-east"
ENABLE_MONITORING="true"
AUTO_APPROVE="false"
DRY_RUN="false"

# Show help
show_help() {
    cat << EOF
CDSI Cloud Bridge Quick Deployment

Usage: $0 [OPTIONS]

Required:
  --customer-id ID        Customer identifier (required)

Optional:
  --size SIZE            Deployment size: small, medium, large (default: small)
  --provider PROVIDER    Cloud provider: aws, digitalocean, linode (default: linode)
  --architecture ARCH    Bridge type: reverse_tunnel, vpn_gateway, container_bridge, api_proxy (default: reverse_tunnel)
  --region REGION        Cloud region (default: us-east)
  --no-monitoring        Disable monitoring (default: enabled)
  --auto-approve         Skip confirmation prompts
  --dry-run              Show plan without deploying
  --help                 Show this help

Examples:
  # Quick small business deployment (cheapest)
  $0 --customer-id small-biz-001
  
  # Enterprise deployment with monitoring
  $0 --customer-id enterprise-001 --size medium --provider aws --architecture vpn_gateway
  
  # Government deployment (most secure)
  $0 --customer-id gov-agency-001 --size large --architecture reverse_tunnel --provider aws

Platform Pricing (monthly):
  🌱 AWARE:       Free    (vs competitors: \$500-2000)   - 100% savings
  🌿 BUILDER:     \$2,997  (vs competitors: \$5000-8000)  - 40% savings
  🪴 ACCELERATOR: \$5,997  (vs competitors: \$10000-15000) - 40% savings
  🌲 TRANSFORMER: \$12,997 (vs competitors: \$20000-30000) - 35% savings
  🌳 CHAMPION:    \$25,000+ (vs competitors: \$50000-100000) - 50% savings

Deployment time: 2-12 hours (vs competitors: 1-8 months)
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --customer-id)
            CUSTOMER_ID="$2"
            shift 2
            ;;
        --size)
            DEPLOYMENT_SIZE="$2"
            shift 2
            ;;
        --provider)
            CLOUD_PROVIDER="$2"
            shift 2
            ;;
        --architecture)
            BRIDGE_ARCHITECTURE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --no-monitoring)
            ENABLE_MONITORING="false"
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE="true"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate required parameters
if [[ -z "$CUSTOMER_ID" ]]; then
    error "Customer ID is required. Use --customer-id <ID>"
fi

# Validate deployment size
if [[ ! "$DEPLOYMENT_SIZE" =~ ^(small|medium|large)$ ]]; then
    error "Invalid deployment size. Must be: small, medium, or large"
fi

# Validate cloud provider
if [[ ! "$CLOUD_PROVIDER" =~ ^(aws|digitalocean|linode)$ ]]; then
    error "Invalid cloud provider. Must be: aws, digitalocean, or linode"
fi

# Validate bridge architecture
if [[ ! "$BRIDGE_ARCHITECTURE" =~ ^(reverse_tunnel|vpn_gateway|container_bridge|api_proxy)$ ]]; then
    error "Invalid bridge architecture. Must be: reverse_tunnel, vpn_gateway, container_bridge, or api_proxy"
fi

# Check dependencies
log "Checking dependencies..."

command -v terraform >/dev/null 2>&1 || error "Terraform is required but not installed. Visit: https://terraform.io/downloads"
command -v docker >/dev/null 2>&1 || warn "Docker not found. Will be installed on target system."
command -v jq >/dev/null 2>&1 || error "jq is required but not installed. Install with: apt-get install jq"

# Check cloud provider credentials
case "$CLOUD_PROVIDER" in
    "aws")
        if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
            error "AWS credentials required. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
        fi
        ;;
    "digitalocean")
        if [[ -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
            error "DigitalOcean token required. Set DIGITALOCEAN_TOKEN environment variable."
        fi
        ;;
    "linode")
        if [[ -z "${LINODE_TOKEN:-}" ]]; then
            error "Linode token required. Set LINODE_TOKEN environment variable."
        fi
        ;;
esac

# Show configuration summary
log "Deployment Configuration:"
echo "  Customer ID: $CUSTOMER_ID"
echo "  Size: $DEPLOYMENT_SIZE"
echo "  Provider: $CLOUD_PROVIDER"
echo "  Architecture: $BRIDGE_ARCHITECTURE"
echo "  Region: $REGION"
echo "  Monitoring: $ENABLE_MONITORING"

# Calculate and show pricing
log "Calculating deployment costs..."

case "$DEPLOYMENT_SIZE" in
    "small")
        MONTHLY_COST=48
        COMPETITOR_RANGE="\$150-800"
        SAVINGS="68-94%"
        SETUP_TIME="2-4 hours"
        MAX_USERS=100
        MAX_DEVICES=500
        ;;
    "medium")
        MONTHLY_COST=74
        COMPETITOR_RANGE="\$200-1200"
        SAVINGS="70-94%"
        SETUP_TIME="4-6 hours"
        MAX_USERS=500
        MAX_DEVICES=2000
        ;;
    "large")
        MONTHLY_COST=128
        COMPETITOR_RANGE="\$10000-20000"
        SAVINGS="75-93%"
        SETUP_TIME="6-12 hours"
        MAX_USERS=1000
        MAX_DEVICES=5000
        ;;
esac

echo
echo -e "${GREEN}💰 PRICING BREAKDOWN:${NC}"
echo "  CDSI Monthly Cost: \$$MONTHLY_COST"
echo "  Competitor Range: $COMPETITOR_RANGE"
echo "  Your Savings: $SAVINGS"
echo "  Setup Cost: \$0 (competitors: \$3,000-50,000)"
echo "  Deployment Time: $SETUP_TIME (competitors: 1-8 months)"
echo
echo -e "${GREEN}📊 CAPACITY:${NC}"
echo "  Max Users: $MAX_USERS"
echo "  Max Devices: $MAX_DEVICES"
echo "  Architecture: $BRIDGE_ARCHITECTURE"
echo "  Provider: $CLOUD_PROVIDER ($REGION)"
echo

# Confirmation
if [[ "$AUTO_APPROVE" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
    echo -e "${YELLOW}⚠️  This will create cloud resources that incur costs.${NC}"
    echo "Monthly estimated cost: \$$MONTHLY_COST"
    echo
    read -p "Do you want to proceed? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled by user."
        exit 0
    fi
fi

# Prepare Terraform workspace
log "Preparing Terraform workspace..."
WORKSPACE_DIR="./terraform-workspace-$CUSTOMER_ID"
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

# Copy Terraform files
cp -r ../deployment/terraform/* .

# Create terraform.tfvars
log "Creating Terraform configuration..."
cat > terraform.tfvars << EOF
# CDSI Bridge Deployment Configuration
# Customer: $CUSTOMER_ID
# Generated: $(date)

customer_id = "$CUSTOMER_ID"
deployment_size = "$DEPLOYMENT_SIZE"
cloud_provider = "$CLOUD_PROVIDER"
bridge_architecture = "$BRIDGE_ARCHITECTURE"
region = "$REGION"
enable_monitoring = $ENABLE_MONITORING

# Network configuration
customer_cidr = "10.0.0.0/16"
backup_retention_days = 30
EOF

# Initialize Terraform
log "Initializing Terraform..."
terraform init

# Plan deployment
log "Planning deployment..."
terraform plan -var-file=terraform.tfvars

if [[ "$DRY_RUN" == "true" ]]; then
    success "Dry run complete. No resources were created."
    exit 0
fi

# Apply deployment
log "Deploying cloud bridge infrastructure..."
if [[ "$AUTO_APPROVE" == "true" ]]; then
    terraform apply -var-file=terraform.tfvars -auto-approve
else
    terraform apply -var-file=terraform.tfvars
fi

# Get deployment outputs
log "Retrieving deployment information..."
DEPLOYMENT_INFO=$(terraform output -json deployment_info | jq -r .value)
CONNECTION_INFO=$(terraform output -json connection_info | jq -r .value)
SETUP_GUIDE=$(terraform output -json customer_setup_guide | jq -r .value)

# Extract key information based on cloud provider
case "$CLOUD_PROVIDER" in
    "aws")
        BRIDGE_IP=$(echo "$DEPLOYMENT_INFO" | jq -r .aws_info.public_ip)
        INSTANCE_ID=$(echo "$DEPLOYMENT_INFO" | jq -r .aws_info.instance_id)
        ;;
    "digitalocean")
        BRIDGE_IP=$(echo "$DEPLOYMENT_INFO" | jq -r .digitalocean_info.public_ip)
        INSTANCE_ID=$(echo "$DEPLOYMENT_INFO" | jq -r .digitalocean_info.instance_id)
        ;;
    "linode")
        BRIDGE_IP=$(echo "$DEPLOYMENT_INFO" | jq -r .linode_info.public_ip)
        INSTANCE_ID=$(echo "$DEPLOYMENT_INFO" | jq -r .linode_info.instance_id)
        ;;
esac

# Create customer package
log "Creating customer setup package..."
CUSTOMER_PACKAGE_DIR="./customer-package-$CUSTOMER_ID"
mkdir -p "$CUSTOMER_PACKAGE_DIR"

# Generate customer setup script
cat > "$CUSTOMER_PACKAGE_DIR/setup.sh" << EOF
#!/bin/bash
# CDSI On-Premise Connector Setup
# Customer: $CUSTOMER_ID
# Bridge IP: $BRIDGE_IP

set -euo pipefail

echo "🌉 CDSI On-Premise Connector Setup"
echo "Customer: $CUSTOMER_ID"
echo "Bridge IP: $BRIDGE_IP"
echo "Architecture: $BRIDGE_ARCHITECTURE"
echo ""

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "📥 Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker found: \$(docker --version)"

# Create connector directory
echo "📁 Creating connector directory..."
sudo mkdir -p /opt/cdsi-connector/{config,data,logs}
sudo chown \$USER:\$USER -R /opt/cdsi-connector

# Download connector
echo "📥 Downloading CDSI connector..."
wget -O /opt/cdsi-connector/docker-compose.yml "https://$BRIDGE_IP/customer-package/docker-compose.yml" || {
    echo "❌ Failed to download connector. Check bridge connectivity."
    exit 1
}

# Create environment configuration
cat > /opt/cdsi-connector/.env << ENV_EOF
CUSTOMER_ID=$CUSTOMER_ID
BRIDGE_ENDPOINT=wss://$BRIDGE_IP:8443/tunnel
BRIDGE_SECRET=\$(terraform output -raw connection_info | jq -r .bridge_secret)
CONNECTOR_MODE=$BRIDGE_ARCHITECTURE
ENV_EOF

# Test connectivity
echo "🔗 Testing bridge connectivity..."
if curl -k -f "https://$BRIDGE_IP/health" &>/dev/null; then
    echo "✅ Bridge is reachable"
else
    echo "❌ Cannot reach bridge. Check firewall settings."
    echo "Required outbound ports: $(echo "$SETUP_GUIDE" | jq -r .required_ports[])"
    exit 1
fi

# Start connector
echo "🚀 Starting CDSI connector..."
cd /opt/cdsi-connector
docker-compose up -d

echo ""
echo "✅ CDSI Connector setup complete!"
echo ""
echo "📊 Status commands:"
echo "  docker-compose -f /opt/cdsi-connector/docker-compose.yml ps"
echo "  docker-compose -f /opt/cdsi-connector/docker-compose.yml logs -f"
echo ""
echo "🌐 Bridge endpoints:"
echo "  Status: https://$BRIDGE_IP/health"
echo "  API: https://$BRIDGE_IP/api"
if [[ "$ENABLE_MONITORING" == "true" ]]; then
echo "  Monitoring: http://$BRIDGE_IP:9090"
fi
echo ""
EOF

chmod +x "$CUSTOMER_PACKAGE_DIR/setup.sh"

# Create README
cat > "$CUSTOMER_PACKAGE_DIR/README.md" << EOF
# CDSI Bridge Deployment - $CUSTOMER_ID

## Deployment Summary
- **Customer ID:** $CUSTOMER_ID
- **Bridge IP:** $BRIDGE_IP
- **Instance ID:** $INSTANCE_ID
- **Architecture:** $BRIDGE_ARCHITECTURE
- **Provider:** $CLOUD_PROVIDER ($REGION)
- **Monthly Cost:** \$$MONTHLY_COST
- **Deployed:** $(date)

## Quick Start
1. Copy this package to your on-premise server
2. Run: \`bash setup.sh\`
3. Verify connectivity

## Architecture: $BRIDGE_ARCHITECTURE
$(echo "$SETUP_GUIDE" | jq -r .setup_steps[] | sed 's/^/- /')

## Network Requirements
**Required Outbound Ports:**
$(echo "$SETUP_GUIDE" | jq -r .required_ports[] | sed 's/^/- /')

## Endpoints
- **Health Check:** https://$BRIDGE_IP/health
- **API:** https://$BRIDGE_IP/api/v1
- **WebSocket:** wss://$BRIDGE_IP:8443/tunnel
$(if [[ "$ENABLE_MONITORING" == "true" ]]; then echo "- **Monitoring:** http://$BRIDGE_IP:9090"; fi)

## Support
- **Estimated Setup Time:** $(echo "$SETUP_GUIDE" | jq -r .estimated_setup_time)
- **Support:** consulting@getcdsi.com
- **Documentation:** https://docs.getcdsi.com

## Cost Comparison
| Solution | Monthly Cost | Setup Cost | Timeline |
|----------|-------------|------------|----------|
| **CDSI** | **\$$MONTHLY_COST** | **\$0** | **$(echo "$SETUP_GUIDE" | jq -r .estimated_setup_time)** |
| OneTrust | \$200-800 | \$5,000-25,000 | 2-6 months |
| TrustArc | \$150-600 | \$3,000-15,000 | 1-4 months |
| Privacera | \$300-1,200 | \$10,000-50,000 | 3-8 months |

**Your Savings: $SAVINGS vs competitors**
EOF

# Create connection details file
echo "$CONNECTION_INFO" > "$CUSTOMER_PACKAGE_DIR/connection-details.json"

# Success message
echo
success "🎉 CDSI Cloud Bridge deployed successfully!"
echo
echo -e "${GREEN}📋 DEPLOYMENT SUMMARY:${NC}"
echo "  Customer ID: $CUSTOMER_ID"
echo "  Bridge IP: $BRIDGE_IP"
echo "  Instance ID: $INSTANCE_ID"
echo "  Monthly Cost: \$$MONTHLY_COST"
echo "  Architecture: $BRIDGE_ARCHITECTURE"
echo
echo -e "${GREEN}🔗 NEXT STEPS:${NC}"
echo "  1. Share customer package: $CUSTOMER_PACKAGE_DIR/"
echo "  2. Customer runs: bash setup.sh"
echo "  3. Verify connectivity: curl -k https://$BRIDGE_IP/health"
echo
echo -e "${GREEN}🌐 ENDPOINTS:${NC}"
echo "  Health: https://$BRIDGE_IP/health"
echo "  API: https://$BRIDGE_IP/api/v1"
if [[ "$ENABLE_MONITORING" == "true" ]]; then
echo "  Monitoring: http://$BRIDGE_IP:9090"
fi
echo
echo -e "${GREEN}💡 COMPETITIVE ADVANTAGE:${NC}"
echo "  Cost Savings: $SAVINGS vs competitors"
echo "  Deployment Speed: Hours vs months"
echo "  Zero Setup Fees: \$0 vs \$3K-50K"
echo
echo -e "${BLUE}📞 Support: consulting@getcdsi.com${NC}"
echo

# Save deployment info for reference
cat > "deployment-$CUSTOMER_ID.json" << EOF
{
  "customer_id": "$CUSTOMER_ID",
  "deployed_at": "$(date -Iseconds)",
  "configuration": {
    "size": "$DEPLOYMENT_SIZE",
    "provider": "$CLOUD_PROVIDER",
    "architecture": "$BRIDGE_ARCHITECTURE",
    "region": "$REGION",
    "monitoring": $ENABLE_MONITORING
  },
  "infrastructure": {
    "bridge_ip": "$BRIDGE_IP",
    "instance_id": "$INSTANCE_ID",
    "monthly_cost": $MONTHLY_COST
  },
  "customer_package": "$CUSTOMER_PACKAGE_DIR",
  "terraform_workspace": "$WORKSPACE_DIR"
}
EOF

log "Deployment details saved to: deployment-$CUSTOMER_ID.json"
log "Customer package ready: $CUSTOMER_PACKAGE_DIR/"
log "Terraform workspace: $WORKSPACE_DIR/"

echo
echo -e "${GREEN}✅ CDSI Bridge deployment complete!${NC}"
echo -e "${BLUE}Ready to compete with enterprise solutions at 50-90% lower cost!${NC}"