# Rift Phase 1 Setup Guide

## Prerequisites

Ensure you have the following installed:

```bash
# Check versions
doctl version     # DigitalOcean CLI
terraform version # Terraform
python3 --version # Python 3.11+
```

## Step 1: Install Dependencies

```bash
# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Authenticate with DigitalOcean

```bash
# Authenticate doctl
doctl auth init

# Verify authentication
doctl account get
```

## Step 3: Create DigitalOcean Infrastructure

### Create Droplets

```bash
# Control Plane - Main application server
doctl compute droplet create control-plane \
  --image ubuntu-24-04-x64 \
  --size s-2vcpu-4gb \
  --region nyc3 \
  --enable-monitoring \
  --tag-name rift \
  --tag-name control-plane \
  --wait

# Web App - Demo target
doctl compute droplet create web-app \
  --image ubuntu-24-04-x64 \
  --size s-1vcpu-1gb \
  --region nyc3 \
  --enable-monitoring \
  --tag-name rift \
  --tag-name target \
  --wait

# API Server - Demo target
doctl compute droplet create api-server \
  --image ubuntu-24-04-x64 \
  --size s-1vcpu-1gb \
  --region nyc3 \
  --enable-monitoring \
  --tag-name rift \
  --tag-name target \
  --wait

# Get droplet IPs
doctl compute droplet list --format Name,PublicIPv4
```

### Create Spaces for Terraform State

```bash
# Create Spaces bucket for Terraform state
doctl spaces create rift-tfstate --region nyc3

# Generate Spaces access keys
doctl spaces keys create rift-spaces-key
# Save the access key and secret key - you'll need these!
```

## Step 4: Set Up Prometheus Monitoring

### Install Prometheus on Control Plane

```bash
# Get control plane IP
CONTROL_PLANE_IP=$(doctl compute droplet get control-plane --format PublicIPv4 --no-header)

# SSH into control plane
ssh root@$CONTROL_PLANE_IP

# On the droplet, run:
# Download and install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64

# Create systemd service
cat > /etc/systemd/system/prometheus.service <<EOF
[Unit]
Description=Prometheus
After=network.target

[Service]
User=root
ExecStart=/root/prometheus-2.45.0.linux-amd64/prometheus \
  --config.file=/root/prometheus-2.45.0.linux-amd64/prometheus.yml \
  --storage.tsdb.path=/root/prometheus-2.45.0.linux-amd64/data

[Install]
WantedBy=multi-user.target
EOF

# Start Prometheus
systemctl daemon-reload
systemctl start prometheus
systemctl enable prometheus

# Verify
systemctl status prometheus
```

### Install Node Exporter on Target Droplets

Run this on both web-app and api-server droplets:

```bash
# Get target IPs
WEB_APP_IP=$(doctl compute droplet get web-app --format PublicIPv4 --no-header)
API_SERVER_IP=$(doctl compute droplet get api-server --format PublicIPv4 --no-header)

# For each target droplet:
ssh root@$WEB_APP_IP  # or $API_SERVER_IP

# On the droplet, run:
# Download and install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
cd node_exporter-1.6.1.linux-amd64

# Create systemd service
cat > /etc/systemd/system/node_exporter.service <<EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=root
ExecStart=/root/node_exporter-1.6.1.linux-amd64/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Start Node Exporter
systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter

# Verify
systemctl status node_exporter
curl http://localhost:9100/metrics
```

### Configure Prometheus Targets

```bash
# On control plane, edit prometheus.yml
ssh root@$CONTROL_PLANE_IP

# Edit the config file
cat > /root/prometheus-2.45.0.linux-amd64/prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'web-app'
    static_configs:
      - targets: ['134.209.37.250:9100']

  - job_name: 'api-server'
    static_configs:
      - targets: ['174.138.62.125:9100']
EOF

# Replace <WEB_APP_IP> and <API_SERVER_IP> with actual IPs

# Restart Prometheus to apply configuration
systemctl restart prometheus

# Verify Prometheus is running
systemctl status prometheus
```

## Step 5: Set Up Gradient AI Agents

### Create Agents in DigitalOcean Console

1. Go to DigitalOcean Gradient AI Platform: https://cloud.digitalocean.com/ai
2. Create **four agents** for complete infrastructure lifecycle management:

**REACTIVE AGENTS (Self-Healing):**

**Monitor Agent:**

- Name: `rift-monitor`
- Description: "Detects infrastructure anomalies and creates incident reports"
- Model: Claude 3.5 Sonnet or GPT-4
- System Prompt: See `agent_prompts/monitor_prompt.txt`

**Diagnostic Agent:**

- Name: `rift-diagnostic`
- Description: "Diagnoses root causes using RAG knowledge base"
- Model: Claude 3.5 Sonnet or GPT-4
- System Prompt: See `agent_prompts/diagnostic_prompt.txt`
- Knowledge Base: Create and attach knowledge base with docs

**Remediation Agent:**

- Name: `rift-remediation`
- Description: "Executes safe infrastructure fixes via Terraform"
- Model: Claude 3.5 Sonnet or GPT-4
- System Prompt: See `agent_prompts/remediation_prompt.txt`

**PROACTIVE AGENT (Infrastructure Provisioning):**

**Provisioner Agent (NEW):**

- Name: `rift-provisioner`
- Description: "Creates infrastructure on demand from natural language requests"
- Model: Claude 3.5 Sonnet or GPT-4
- System Prompt: See `agent_prompts/provisioner_prompt.txt`
- Capabilities:
  - Interprets natural language infrastructure requests
  - Generates Terraform configurations automatically
  - Provides cost estimates before provisioning
  - Validates and applies infrastructure changes

3. Save all agent endpoints and API keys

### Create Knowledge Base

1. In Gradient AI Console, create a new Knowledge Base: `rift-knowledge`
2. Upload documents from `knowledge-base/` directory:
   - DigitalOcean documentation
   - Terraform best practices
   - Incident runbooks
   - Past incident examples
3. Enable auto-indexing
4. Save the Knowledge Base ID

## Step 6: Configure Environment Variables

Update `.env` file with your actual values:

```bash
# Edit .env file
nano .env

# Fill in:
DIGITALOCEAN_API_TOKEN=dop_v1_xxxxx

MONITOR_AGENT_ENDPOINT=https://api.digitalocean.com/v2/ai/agents/xxxxx
MONITOR_AGENT_KEY=xxxxx
MONITOR_AGENT_ID=xxxxx

DIAGNOSTIC_AGENT_ENDPOINT=https://api.digitalocean.com/v2/ai/agents/xxxxx
DIAGNOSTIC_AGENT_KEY=xxxxx
DIAGNOSTIC_AGENT_ID=xxxxx

REMEDIATION_AGENT_ENDPOINT=https://api.digitalocean.com/v2/ai/agents/xxxxx
REMEDIATION_AGENT_KEY=xxxxx
REMEDIATION_AGENT_ID=xxxxx

KNOWLEDGE_BASE_ID=xxxxx

DO_SPACES_ACCESS_KEY=xxxxx
DO_SPACES_SECRET_KEY=xxxxx

API_SECRET_KEY=$(openssl rand -hex 32)

CONTROL_PLANE_IP=<from step 3>
WEB_APP_IP=<from step 3>
API_SERVER_IP=<from step 3>
PROMETHEUS_IP=<control plane IP>
```

## Step 7: Verify Setup

```bash
# Test DigitalOcean API
doctl compute droplet list

# Test Prometheus
curl http://$CONTROL_PLANE_IP:9090/api/v1/targets

# Test Python environment
python -c "from utils.config import get_settings; print(get_settings())"
```

## Step 8: Create Sample Knowledge Base Content

Create these files in `knowledge-base/`:

```bash
# Create knowledge base files
mkdir -p knowledge-base
cd knowledge-base

# You'll create these in the next phase:
# - do-docs.md (DigitalOcean documentation)
# - runbooks.md (Incident response procedures)
# - past-incidents.json (Example incidents)
```

## Troubleshooting

### Droplet Creation Fails

- Check your DigitalOcean account limits
- Verify region availability: `doctl compute region list`
- Try different size: `doctl compute size list`

### Prometheus Not Accessible

- Check firewall: `ufw status`
- Verify service: `systemctl status prometheus`
- Check logs: `journalctl -u prometheus -f`

### Node Exporter Not Scraping

- Verify node_exporter is running: `systemctl status node_exporter`
- Test metrics endpoint: `curl localhost:9100/metrics`
- Check Prometheus config: `cat /root/prometheus-2.45.0.linux-amd64/prometheus.yml`

### Gradient AI Agent Not Responding

- Verify API token is valid
- Check agent status in DO console
- Test with curl: `curl -X POST $MONITOR_AGENT_ENDPOINT/query -H "Authorization: Bearer $MONITOR_AGENT_KEY"`

## Next Steps

Phase 1 is complete! You have:

- ✅ DigitalOcean droplets running
- ✅ Prometheus monitoring configured
- ✅ Gradient AI agents created
- ✅ Environment configured

Continue to **Phase 2: Monitor Agent Implementation**
