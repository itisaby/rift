#!/bin/bash

# Simple script to create CPU load on web-app and manually create incident

echo "🔥 Step 1: Creating CPU load on web-app (134.209.37.250)"
echo "SSH into the droplet and run: stress --cpu 2 --timeout 120s"
echo ""
echo "Command to run on your terminal:"
echo "  ssh root@134.209.37.250"
echo "  apt-get install -y stress  # if not installed"
echo "  stress --cpu 2 --timeout 120s &"
echo ""
echo "🚨 Step 2: Create incident via demo endpoint with REAL droplet ID"
echo ""

curl -X POST "http://localhost:8000/demo/inject-failure?failure_type=cpu&target=web-app&duration=300" -s | python3 -m json.tool

echo ""
echo "The incident is created with real droplet IP (134.209.37.250)"
echo "Now you can:"
echo "  1. Click 'Diagnose' - it will query the REAL droplet from DigitalOcean API"
echo "  2. Click 'Remediate' - it will generate real remediation actions"
