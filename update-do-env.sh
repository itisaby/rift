#!/bin/bash

# Simple CLI method to update DigitalOcean App environment variables

# USAGE:
# 1. Find your app ID: doctl apps list
# 2. Run this script with your app ID

APP_ID="$1"

if [ -z "$APP_ID" ]; then
    echo "Usage: ./update-do-env.sh YOUR_APP_ID"
    echo ""
    echo "Find your app ID with: doctl apps list"
    exit 1
fi

echo "📥 Downloading current app spec..."
doctl apps spec get "$APP_ID" > app-current.yaml

echo "✏️  Edit app-current.yaml and add your environment variables"
echo ""
echo "Then run: doctl apps update $APP_ID --spec app-current.yaml"
echo ""
echo "File ready to edit: app-current.yaml"
