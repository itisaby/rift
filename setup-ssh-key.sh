#!/bin/bash
#
# Setup SSH Key for Autonomous Remediation
# This script uploads your SSH key to DigitalOcean and configures Rift to use it
#

set -e

echo "🔑 Setting up SSH Key for Autonomous Remediation"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SSH_KEY_PATH="$HOME/.ssh/id_ed25519_do_rift"
SSH_KEY_NAME="rift-automation"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/backend/.env"

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH.pub" ]; then
    echo -e "${RED}❌ SSH key not found at $SSH_KEY_PATH.pub${NC}"
    echo "Please run the key generation first or specify the correct path"
    exit 1
fi

echo -e "${GREEN}✓ Found SSH key at $SSH_KEY_PATH.pub${NC}"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${YELLOW}⚠ doctl not found. Using API method instead${NC}"
    USE_API=true
else
    echo -e "${GREEN}✓ doctl found${NC}"
    USE_API=false
fi

# Get DO API token
if [ -f "$ENV_FILE" ]; then
    DO_API_TOKEN=$(grep "^DIGITALOCEAN_API_TOKEN=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
fi

if [ -z "$DO_API_TOKEN" ]; then
    echo -e "${RED}❌ DIGITALOCEAN_API_TOKEN not found in $ENV_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found DigitalOcean API token${NC}"

# Upload SSH key
echo ""
echo "Uploading SSH key to DigitalOcean..."

if [ "$USE_API" = true ]; then
    # Use API method
    PUBLIC_KEY=$(cat "$SSH_KEY_PATH.pub")
    
    RESPONSE=$(curl -s -X POST "https://api.digitalocean.com/v2/account/keys" \
        -H "Authorization: Bearer $DO_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$SSH_KEY_NAME\",\"public_key\":\"$PUBLIC_KEY\"}")
    
    # Check if upload was successful
    if echo "$RESPONSE" | grep -q "\"ssh_key\""; then
        SSH_KEY_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['ssh_key']['id'])")
        echo -e "${GREEN}✓ SSH key uploaded successfully via API${NC}"
    elif echo "$RESPONSE" | grep -q "SSH Key is already in use on your account"; then
        echo -e "${YELLOW}⚠ SSH key already exists, fetching existing key...${NC}"
        
        # Get existing key ID
        LIST_RESPONSE=$(curl -s -X GET "https://api.digitalocean.com/v2/account/keys" \
            -H "Authorization: Bearer $DO_API_TOKEN")
        
        SSH_KEY_ID=$(echo "$LIST_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for key in data['ssh_keys']:
    if key['name'] == '$SSH_KEY_NAME':
        print(key['id'])
        break
")
        
        if [ -z "$SSH_KEY_ID" ]; then
            echo -e "${RED}❌ Could not find existing SSH key${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✓ Found existing SSH key${NC}"
    else
        echo -e "${RED}❌ Failed to upload SSH key${NC}"
        echo "$RESPONSE"
        exit 1
    fi
else
    # Use doctl method
    # Check if key already exists
    if doctl compute ssh-key list --format Name --no-header | grep -q "^$SSH_KEY_NAME$"; then
        echo -e "${YELLOW}⚠ SSH key '$SSH_KEY_NAME' already exists${NC}"
        SSH_KEY_ID=$(doctl compute ssh-key list --format ID,Name --no-header | grep "$SSH_KEY_NAME" | awk '{print $1}')
        echo -e "${GREEN}✓ Using existing SSH key${NC}"
    else
        # Upload new key
        UPLOAD_OUTPUT=$(doctl compute ssh-key import "$SSH_KEY_NAME" \
            --public-key-file "$SSH_KEY_PATH.pub" \
            --format ID --no-header 2>&1)
        
        if [ $? -eq 0 ]; then
            SSH_KEY_ID="$UPLOAD_OUTPUT"
            echo -e "${GREEN}✓ SSH key uploaded successfully via doctl${NC}"
        else
            echo -e "${RED}❌ Failed to upload SSH key${NC}"
            echo "$UPLOAD_OUTPUT"
            exit 1
        fi
    fi
fi

echo ""
echo "SSH Key ID: $SSH_KEY_ID"

# Update .env file
echo ""
echo "Updating $ENV_FILE..."

if grep -q "^SSH_KEY_ID=" "$ENV_FILE"; then
    # Update existing entry
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^SSH_KEY_ID=.*/SSH_KEY_ID=$SSH_KEY_ID/" "$ENV_FILE"
    else
        sed -i "s/^SSH_KEY_ID=.*/SSH_KEY_ID=$SSH_KEY_ID/" "$ENV_FILE"
    fi
    echo -e "${GREEN}✓ Updated SSH_KEY_ID in $ENV_FILE${NC}"
else
    # Add new entry
    echo "" >> "$ENV_FILE"
    echo "# SSH Key for Autonomous Remediation" >> "$ENV_FILE"
    echo "SSH_KEY_ID=$SSH_KEY_ID" >> "$ENV_FILE"
    echo -e "${GREEN}✓ Added SSH_KEY_ID to $ENV_FILE${NC}"
fi

# Verify key is accessible
echo ""
echo "Verifying SSH key in DigitalOcean..."

if [ "$USE_API" = true ]; then
    VERIFY=$(curl -s -X GET "https://api.digitalocean.com/v2/account/keys/$SSH_KEY_ID" \
        -H "Authorization: Bearer $DO_API_TOKEN")
    
    if echo "$VERIFY" | grep -q "\"ssh_key\""; then
        KEY_NAME=$(echo "$VERIFY" | python3 -c "import sys, json; print(json.load(sys.stdin)['ssh_key']['name'])")
        KEY_FINGERPRINT=$(echo "$VERIFY" | python3 -c "import sys, json; print(json.load(sys.stdin)['ssh_key']['fingerprint'])")
        echo -e "${GREEN}✓ SSH key verified${NC}"
        echo "  Name: $KEY_NAME"
        echo "  Fingerprint: $KEY_FINGERPRINT"
    else
        echo -e "${RED}❌ Could not verify SSH key${NC}"
        exit 1
    fi
else
    KEY_INFO=$(doctl compute ssh-key get "$SSH_KEY_ID" --format Name,FingerPrint --no-header)
    echo -e "${GREEN}✓ SSH key verified${NC}"
    echo "  $KEY_INFO"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart your backend server to load the new SSH_KEY_ID"
echo "2. Provision new droplets - they will automatically have SSH key access"
echo "3. Autonomous remediation will work immediately on new VMs"
echo ""
echo "For existing VMs, you still need to manually add the SSH key once."
echo "Run this on each existing VM:"
echo ""
echo "  ssh root@<VM_IP> \"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$(cat $SSH_KEY_PATH.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""
echo ""
