#!/bin/bash
#
# Node Exporter Installation Script
# This script is injected via cloud-init user_data when provisioning new droplets
# It automatically installs and configures Node Exporter for Prometheus monitoring
#

set -e

echo "Starting Node Exporter installation..."

# Update system
apt-get update

# Download Node Exporter
NODE_EXPORTER_VERSION="1.6.1"
cd /tmp
wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz

# Extract and install
tar xzf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
mv node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64*

# Create systemd service
cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Documentation=https://prometheus.io/docs/guides/node-exporter/
After=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/node_exporter
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Wait for service to be ready
sleep 3

# Verify installation
if systemctl is-active --quiet node_exporter; then
    echo "✓ Node Exporter installed and running on port 9100"
else
    echo "✗ Node Exporter installation failed"
    exit 1
fi

echo "Node Exporter setup complete!"
