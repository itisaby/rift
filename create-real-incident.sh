#!/bin/bash

# Create a REAL incident from actual Prometheus metrics for testing

API_URL="http://localhost:8000"
PROM_URL="http://104.236.4.131:9090"

# Droplet mapping
DROPLET_ID="536761938"  # web-app
DROPLET_NAME="web-app"
DROPLET_IP="134.209.37.250"

echo "🔍 Fetching real metrics from Prometheus for $DROPLET_NAME..."
echo ""

# Get CPU usage
CPU_QUERY="100 - (avg(rate(node_cpu_seconds_total{mode='idle',instance='${DROPLET_IP}:9100'}[5m])) * 100)"
CPU_RESPONSE=$(curl -s "${PROM_URL}/api/v1/query?query=${CPU_QUERY}")
CPU_VALUE=$(echo "$CPU_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['result'][0]['value'][1] if data['data']['result'] else '0')" 2>/dev/null || echo "0")

echo "📊 Current CPU Usage: ${CPU_VALUE}%"

# Get Memory usage
MEM_QUERY="(1 - (node_memory_MemAvailable_bytes{instance='${DROPLET_IP}:9100'} / node_memory_MemTotal_bytes{instance='${DROPLET_IP}:9100'})) * 100"
MEM_RESPONSE=$(curl -s "${PROM_URL}/api/v1/query?query=${MEM_QUERY}")
MEM_VALUE=$(echo "$MEM_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['result'][0]['value'][1] if data['data']['result'] else '0')" 2>/dev/null || echo "0")

echo "📊 Current Memory Usage: ${MEM_VALUE}%"

# Get Disk usage
DISK_QUERY="(1 - (node_filesystem_avail_bytes{instance='${DROPLET_IP}:9100',mountpoint='/'} / node_filesystem_size_bytes{instance='${DROPLET_IP}:9100',mountpoint='/'})) * 100"
DISK_RESPONSE=$(curl -s "${PROM_URL}/api/v1/query?query=${DISK_QUERY}")
DISK_VALUE=$(echo "$DISK_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['result'][0]['value'][1] if data['data']['result'] else '0')" 2>/dev/null || echo "0")

echo "📊 Current Disk Usage: ${DISK_VALUE}%"
echo ""

# Determine which metric is highest to create incident for
CPU_INT=$(python3 -c "print(int(float('${CPU_VALUE}')))" 2>/dev/null || echo "0")
MEM_INT=$(python3 -c "print(int(float('${MEM_VALUE}')))" 2>/dev/null || echo "0")
DISK_INT=$(python3 -c "print(int(float('${DISK_VALUE}')))" 2>/dev/null || echo "0")

if [ "$CPU_INT" -gt "$MEM_INT" ] && [ "$CPU_INT" -gt "$DISK_INT" ]; then
    METRIC="cpu_usage"
    CURRENT_VALUE="$CPU_VALUE"
    THRESHOLD="80.0"
    DESCRIPTION="High CPU usage detected on $DROPLET_NAME"
elif [ "$MEM_INT" -gt "$DISK_INT" ]; then
    METRIC="memory_usage"
    CURRENT_VALUE="$MEM_VALUE"
    THRESHOLD="85.0"
    DESCRIPTION="High memory usage detected on $DROPLET_NAME"
else
    METRIC="disk_usage"
    CURRENT_VALUE="$DISK_VALUE"
    THRESHOLD="90.0"
    DESCRIPTION="High disk usage detected on $DROPLET_NAME"
fi

echo "🚨 Creating REAL incident for $METRIC..."
echo ""

# Create incident with real data
cat > /tmp/real_incident.json << EOF
{
  "resource_id": "$DROPLET_ID",
  "resource_name": "$DROPLET_NAME",
  "resource_type": "droplet",
  "metric": "$METRIC",
  "current_value": $CURRENT_VALUE,
  "threshold_value": $THRESHOLD,
  "severity": "high",
  "description": "$DESCRIPTION",
  "metadata": {
    "source": "prometheus",
    "prometheus_url": "$PROM_URL",
    "droplet_ip": "$DROPLET_IP"
  }
}
EOF

echo "📤 Sending incident to backend..."
curl -X POST "$API_URL/incidents" \
  -H "Content-Type: application/json" \
  -d @/tmp/real_incident.json \
  -s | python3 -m json.tool

echo ""
echo "✅ Real incident created! Check the frontend to diagnose and remediate."
