#!/bin/bash

# Rift Deployment Script
# Deploys frontend to Vercel and backend to DigitalOcean

set -e

echo "🚀 Starting Rift Deployment..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "PROJECT_STORY.md" ]; then
    echo "❌ Please run this script from the root of the Rift repository"
    exit 1
fi

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}  Frontend Deployment - Vercel${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Deploy frontend
cd frontend

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "${YELLOW}⚠️  Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
fi

echo "📦 Deploying frontend to Vercel..."
vercel --prod

echo ""
echo "${GREEN}✅ Frontend deployed successfully!${NC}"
echo ""

cd ..

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}  Backend Deployment - DigitalOcean${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "${YELLOW}⚠️  doctl CLI not found.${NC}"
    echo ""
    echo "Please choose deployment method:"
    echo "  1) Install doctl and deploy via CLI"
    echo "  2) Deploy manually via DigitalOcean Dashboard"
    echo ""
    read -p "Enter choice (1 or 2): " choice
    
    if [ "$choice" = "1" ]; then
        echo ""
        echo "Install doctl:"
        echo "  macOS: brew install doctl"
        echo "  Linux: snap install doctl"
        echo ""
        echo "Then authenticate:"
        echo "  doctl auth init"
        echo ""
        echo "Run this script again after installation."
        exit 0
    else
        echo ""
        echo "${YELLOW}Manual Deployment Steps:${NC}"
        echo ""
        echo "1. Go to: https://cloud.digitalocean.com/apps/new"
        echo "2. Connect GitHub repo: itisaby/rift"
        echo "3. Use configuration from: .do/app.yaml"
        echo "4. Add environment variables from: backend/.env"
        echo "5. Deploy!"
        echo ""
        exit 0
    fi
fi

echo "🐙 Deploying backend to DigitalOcean App Platform..."

# Check if app already exists
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep "rift-backend" | awk '{print $1}' || echo "")

if [ -z "$APP_ID" ]; then
    echo "📝 Creating new app..."
    doctl apps create --spec .do/app.yaml
    echo ""
    echo "${GREEN}✅ Backend app created successfully!${NC}"
    echo ""
    echo "${YELLOW}⚠️  Remember to add SECRET environment variables in the dashboard:${NC}"
    echo "  - DIGITALOCEAN_API_TOKEN"
    echo "  - MONITOR_AGENT_ENDPOINT, KEY, ID"
    echo "  - DIAGNOSTIC_AGENT_ENDPOINT, KEY, ID"
    echo "  - REMEDIATION_AGENT_ENDPOINT, KEY, ID"
    echo "  - PROVISIONER_AGENT_ENDPOINT, KEY, ID"
    echo "  - KNOWLEDGE_BASE_ID"
    echo ""
    echo "Dashboard: https://cloud.digitalocean.com/apps"
else
    echo "📝 Updating existing app (ID: $APP_ID)..."
    doctl apps update $APP_ID --spec .do/app.yaml
    echo ""
    echo "${GREEN}✅ Backend app updated successfully!${NC}"
fi

echo ""
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${GREEN}  Deployment Complete!${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📱 Frontend: Check Vercel dashboard for URL"
echo "🖥️  Backend: Check DigitalOcean Apps dashboard for URL"
echo ""
echo "${YELLOW}Next Steps:${NC}"
echo "1. Get backend URL from DO Apps dashboard"
echo "2. Update Vercel environment variable:"
echo "   NEXT_PUBLIC_API_URL=https://your-backend-url.com"
echo "3. Redeploy frontend on Vercel"
echo ""
echo "🎉 Happy deploying!"
