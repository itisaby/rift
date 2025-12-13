#!/bin/bash

# Rift Prometheus Installation Script
# Run this on the control-plane droplet

set -e

echo "========================================"
echo "🌌 Rift Prometheus Setup"
echo "========================================"
echo ""

# Detect what to install based on hostname
HOSTNAME=$(hostname)

if [[ "$HOSTNAME" == "control-plane" ]]; then
    echo "Installing Prometheus on control-plane..."

    # Download Prometheus
    cd /tmp
    wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
    tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
    sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus

    # Create systemd service
    sudo tee /etc/systemd/system/prometheus.service > /dev/null <<EOF
[Unit]
Description=Prometheus
After=network.target

[Service]
User=root
ExecStart=/opt/prometheus/prometheus \\
  --config.file=/opt/prometheus/prometheus.yml \\
  --storage.tsdb.path=/opt/prometheus/data

[Install]
WantedBy=multi-user.target
EOF

    # Start Prometheus
    sudo systemctl daemon-reload
    sudo systemctl start prometheus
    sudo systemctl enable prometheus

    echo "✓ Prometheus installed and started"
    echo "  Access at: http://$(curl -s ifconfig.me):9090"

elif [[ "$HOSTNAME" == "web-app" ]] || [[ "$HOSTNAME" == "api-server" ]]; then
    echo "Installing Node Exporter on $HOSTNAME..."

    # Download Node Exporter
    cd /tmp
    wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
    tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
    sudo mv node_exporter-1.6.1.linux-amd64 /opt/node_exporter

    # Create systemd service
    sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=root
ExecStart=/opt/node_exporter/node_exporter

[Install]
WantedBy=multi-user.target
EOF

    # Start Node Exporter
    sudo systemctl daemon-reload
    sudo systemctl start node_exporter
    sudo systemctl enable node_exporter

    echo "✓ Node Exporter installed and started"
    echo "  Metrics available at: http://localhost:9100/metrics"

else
    echo "Unknown hostname: $HOSTNAME"
    echo "This script should be run on control-plane, web-app, or api-server"
    exit 1
fi

echo ""
echo "Installation complete!"
