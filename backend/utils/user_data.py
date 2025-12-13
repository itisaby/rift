"""
User Data Generator for Cloud-Init Scripts
Generates cloud-init configuration for automated droplet setup
"""

import os
from typing import Optional


def generate_node_exporter_user_data(
    additional_packages: Optional[list[str]] = None,
    additional_commands: Optional[list[str]] = None
) -> str:
    """
    Generate cloud-init user_data script for Node Exporter installation
    
    Args:
        additional_packages: Additional apt packages to install
        additional_commands: Additional bash commands to execute
        
    Returns:
        User data script as string
    """
    
    packages = additional_packages or []
    commands = additional_commands or []
    
    user_data = """#!/bin/bash
set -e

echo "Starting automated droplet setup..."

# Update system
apt-get update
apt-get upgrade -y

"""
    
    # Add additional packages
    if packages:
        user_data += f"""# Install additional packages
apt-get install -y {' '.join(packages)}

"""
    
    # Node Exporter installation
    user_data += """# Install Node Exporter
NODE_EXPORTER_VERSION="1.6.1"
cd /tmp
wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
tar xzf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
mv node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64*

# Create Node Exporter systemd service
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

# Enable and start Node Exporter
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

echo "✓ Node Exporter installed and running"

"""
    
    # Add additional commands
    if commands:
        user_data += """# Execute additional commands
"""
        for cmd in commands:
            user_data += f"{cmd}\n"
        user_data += "\n"
    
    user_data += """echo "✓ Droplet setup complete!"
"""
    
    return user_data


def generate_postgres_user_data() -> str:
    """
    Generate user_data for PostgreSQL droplets with Node Exporter
    """
    return generate_node_exporter_user_data(
        additional_packages=["postgresql", "postgresql-contrib"],
        additional_commands=[
            "systemctl enable postgresql",
            "systemctl start postgresql"
        ]
    )


def generate_nginx_user_data() -> str:
    """
    Generate user_data for Nginx droplets with Node Exporter
    """
    return generate_node_exporter_user_data(
        additional_packages=["nginx"],
        additional_commands=[
            "systemctl enable nginx",
            "systemctl start nginx"
        ]
    )


def generate_docker_user_data() -> str:
    """
    Generate user_data for Docker droplets with Node Exporter
    """
    return generate_node_exporter_user_data(
        additional_commands=[
            "curl -fsSL https://get.docker.com -o get-docker.sh",
            "sh get-docker.sh",
            "systemctl enable docker",
            "systemctl start docker"
        ]
    )
