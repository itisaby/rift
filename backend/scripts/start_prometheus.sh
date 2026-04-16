#!/bin/bash
# Start Prometheus with mounted config and lifecycle API enabled
set -e

PROM_DIR="/tmp/rift_prometheus"
CONTAINER_NAME="rift-prometheus"

mkdir -p "$PROM_DIR"

# Create initial prometheus.yml if not exists
if [ ! -f "$PROM_DIR/prometheus.yml" ]; then
  cat > "$PROM_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets:
          - localhost:9090
EOF
  echo "Created initial Prometheus config"
fi

# Remove existing container if present
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Removing existing ${CONTAINER_NAME} container..."
  docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
fi

echo "Starting Prometheus container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -p 9090:9090 \
  -v "$PROM_DIR":/etc/prometheus \
  prom/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --web.enable-lifecycle \
  --storage.tsdb.retention.time=30d

echo "Prometheus started at http://localhost:9090"
echo "Config directory: $PROM_DIR"
echo "Lifecycle API enabled (POST /-/reload to reload config)"

# Wait for Prometheus to be ready
echo -n "Waiting for Prometheus to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo " ready!"
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo " timeout (may still be starting)"
