#!/bin/bash

# Test the complete incident flow: inject → diagnose → remediate

set -e

API_URL="http://localhost:8000"

echo "🔥 Step 1: Inject Failure"
echo "=========================="
RESPONSE=$(curl -s -X POST "$API_URL/demo/inject-failure?failure_type=high_cpu&target=web-app&duration=300")
echo "$RESPONSE" | python3 -m json.tool

# Extract incident_id from response
INCIDENT_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['incident_id'])")
echo ""
echo "✅ Created incident: $INCIDENT_ID"
echo ""

sleep 2

echo "🔍 Step 2: Diagnose Incident"
echo "============================"
echo "Calling: POST $API_URL/incidents/diagnose?incident_id=$INCIDENT_ID"
curl -s -X POST "$API_URL/incidents/diagnose?incident_id=$INCIDENT_ID" | python3 -m json.tool
echo ""

sleep 2

echo "💊 Step 3: Remediate Incident"
echo "=============================="
echo "Calling: POST $API_URL/incidents/remediate?incident_id=$INCIDENT_ID&auto_approve=true"
curl -s -X POST "$API_URL/incidents/remediate?incident_id=$INCIDENT_ID&auto_approve=true" | python3 -m json.tool
echo ""

echo "✅ Complete flow finished!"
