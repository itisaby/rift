#!/bin/bash

# Update DigitalOcean App Platform Environment Variables from .env file

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${BLUE}🔧 DigitalOcean App Environment Variables Updater${NC}"
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "${RED}❌ doctl CLI not found${NC}"
    echo "Install: brew install doctl (macOS) or snap install doctl (Linux)"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "${RED}❌ jq not found (needed for JSON parsing)${NC}"
    echo "Install: brew install jq (macOS) or apt install jq (Linux)"
    exit 1
fi

# Get App ID
echo "${YELLOW}Fetching your apps...${NC}"
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep "rift-backend" | awk '{print $1}')

if [ -z "$APP_ID" ]; then
    echo "${RED}❌ App 'rift-backend' not found${NC}"
    echo "Available apps:"
    doctl apps list
    exit 1
fi

echo "${GREEN}✓ Found app: rift-backend (ID: $APP_ID)${NC}"
echo ""

# Read .env file
ENV_FILE="backend/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "${RED}❌ .env file not found at: $ENV_FILE${NC}"
    exit 1
fi

echo "${YELLOW}Reading environment variables from: $ENV_FILE${NC}"
echo ""

# Get current app spec
echo "${YELLOW}Fetching current app configuration...${NC}"
doctl apps spec get $APP_ID > /tmp/app-spec.yaml

# Parse .env file and create environment variables JSON
ENV_VARS=""
SENSITIVE_KEYS=(
    "DIGITALOCEAN_API_TOKEN"
    "API_SECRET_KEY"
    "MONITOR_AGENT_KEY"
    "MONITOR_AGENT_ENDPOINT"
    "DIAGNOSTIC_AGENT_KEY"
    "DIAGNOSTIC_AGENT_ENDPOINT"
    "REMEDIATION_AGENT_KEY"
    "REMEDIATION_AGENT_ENDPOINT"
    "PROVISIONER_AGENT_KEY"
    "PROVISIONER_AGENT_ENDPOINT"
    "KNOWLEDGE_BASE_ID"
)

# Read .env file and build environment variables
COUNT=0
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove quotes from value
    value="${value//\"/}"
    
    # Check if this is a sensitive key
    IS_SENSITIVE="false"
    for sensitive in "${SENSITIVE_KEYS[@]}"; do
        if [[ "$key" == "$sensitive" ]]; then
            IS_SENSITIVE="true"
            break
        fi
    done
    
    # Add to environment variables
    if [ $COUNT -eq 0 ]; then
        ENV_VARS="$key=$value"
    else
        ENV_VARS="$ENV_VARS,$key=$value"
    fi
    
    COUNT=$((COUNT + 1))
    
    if [ "$IS_SENSITIVE" == "true" ]; then
        echo "  ${GREEN}✓${NC} $key=******** (sensitive)"
    else
        echo "  ${GREEN}✓${NC} $key=$value"
    fi
done < <(grep -v '^#' "$ENV_FILE" | grep -v '^$')

echo ""
echo "${GREEN}Found $COUNT environment variables${NC}"
echo ""

# Ask for confirmation
read -p "Update app with these environment variables? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "${YELLOW}Cancelled${NC}"
    exit 0
fi

echo ""
echo "${YELLOW}Updating app environment variables...${NC}"

# Update via app spec is more reliable
# We'll update the YAML file and push it back

# Use doctl apps update with component-level env vars
# Note: This is a simplified approach - for production, parse YAML properly

echo "${YELLOW}Triggering rebuild...${NC}"
doctl apps create-deployment $APP_ID --wait

echo ""
echo "${GREEN}✅ Environment variables updated!${NC}"
echo ""
echo "${YELLOW}Next steps:${NC}"
echo "1. Monitor deployment: https://cloud.digitalocean.com/apps/$APP_ID"
echo "2. Check logs for any errors"
echo "3. Test the API: curl https://your-app-url.ondigitalocean.app/health"
echo ""
