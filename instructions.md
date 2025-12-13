# 🌌 Rift - Complete Implementation Guide for Claude Code

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites & Setup](#prerequisites--setup)
4. [Implementation Phases](#implementation-phases)
5. [Component Specifications](#component-specifications)
6. [MCP Server Integration](#mcp-server-integration)
7. [Agent Implementation](#agent-implementation)
8. [Demo Preparation](#demo-preparation)
9. [Troubleshooting](#troubleshooting)
10. [Hackathon Timeline](#hackathon-timeline)

---

## 📌 Project Overview

**Project Name:** Rift 🌌  
**Tagline:** Rift through operational complexity  
**Full Description:** Autonomous Infrastructure Orchestrator powered by DigitalOcean Gradient AI + MCP  
**Goal:** Build a self-healing multi-agent system that monitors, diagnoses, and fixes infrastructure issues autonomously  
**Timeline:** 24 hours  
**Target:** MLH + DigitalOcean AI Hackathon NYC (December 12-13, 2025)

### Core Value Proposition

- **Problem:** DevOps engineers spend 40% of time on routine incidents, manual infrastructure fixes, and repetitive provisioning tasks
- **Solution:** AI agents that autonomously detect, diagnose, fix infrastructure issues AND provision new infrastructure on demand
- **Impact:** Reduce incident response time from hours to seconds, eliminate manual provisioning, minimize human intervention

### What Makes Rift Complete

Rift is a **complete AI-powered DevOps solution** with two core capabilities:

**1. REACTIVE (Self-Healing) - 3 Agents:**

- **Monitor Agent** - Detects infrastructure issues in real-time
- **Diagnostic Agent** - Analyzes root causes using RAG
- **Remediation Agent** - Fixes problems automatically via Terraform + MCP

**2. PROACTIVE (Infrastructure Provisioning) - 1 Agent:**

- **Provisioner Agent** - Creates infrastructure on demand
- Interprets natural language requests ("create staging environment")
- Generates and applies Terraform configurations automatically
- Provides instant infrastructure with cost estimates

**Result:** Complete infrastructure lifecycle management - from creation to healing - all autonomous.

### Rift Identity

**Logo:** 🌌 or ⚡

**Tagline Options:**

1. **"Rift through operational complexity"** ⭐ Primary
2. "Opening rifts, closing problems"
3. "Instant infrastructure, through the rift"
4. "Operations at rift speed"

**Elevator Pitch:**
_"Rift is an autonomous infrastructure orchestrator powered by DigitalOcean Gradient AI. It opens rifts to create infrastructure instantly, and closes rifts to fix problems automatically - all at machine speed."_

**Personality:**

- Powerful, instantaneous, unstoppable
- Tears through complexity
- Creates instant connections
- Sci-fi meets enterprise ops

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                  (Terminal / Simple Streamlit UI)               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ HTTP/WebSocket
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    ORCHESTRATOR LAYER                            │
│                    (FastAPI Application)                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  API Endpoints:                                        │    │
│  │  • POST /incidents/detect                              │    │
│  │  • POST /incidents/diagnose                            │    │
│  │  • POST /incidents/remediate                           │    │
│  │  • GET /status                                         │    │
│  │  • GET /agents/health                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Agent Coordinator:                                    │    │
│  │  • Routes requests to appropriate agents               │    │
│  │  • Manages agent state and communication               │    │
│  │  • Collects and aggregates results                     │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ Agent API Calls
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│              DIGITALOCEAN GRADIENT AI PLATFORM                   │
│                    (Multi-Agent System)                          │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐│
│  │  MONITOR AGENT   │  │ DIAGNOSTIC AGENT │  │ REMEDIATION   ││
│  │                  │─▶│                  │─▶│ AGENT         ││
│  │  • Droplet       │  │ • Root Cause     │  │ • Terraform   ││
│  │    Monitoring    │  │   Analysis       │  │   Execution   ││
│  │  • Metrics       │  │ • RAG Queries    │  │ • DO API      ││
│  │    Collection    │  │ • Confidence     │  │   Calls       ││
│  │  • Alert         │  │   Scoring        │  │ • Validation  ││
│  │    Detection     │  │                  │  │               ││
│  └──────┬───────────┘  └──────┬───────────┘  └───────┬───────┘│
│         │                     │                       │        │
│         └─────────────────────┼───────────────────────┘        │
│                               │                                │
│  ┌────────────────────────────▼────────────────────────────┐  │
│  │           KNOWLEDGE BASE (RAG)                           │  │
│  │                                                          │  │
│  │  Sources:                                                │  │
│  │  • DigitalOcean Documentation (auto-indexed)            │  │
│  │  • Terraform Best Practices                             │  │
│  │  • Incident Response Runbooks                           │  │
│  │  • Past Incident History (synthetic + real)             │  │
│  │  • Linux Troubleshooting Guides                         │  │
│  │                                                          │  │
│  │  Features:                                               │  │
│  │  • Auto-Indexing (keeps data fresh)                     │  │
│  │  • Semantic Search                                       │  │
│  │  • Citation Support                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           AGENT EVALUATION & OBSERVABILITY               │  │
│  │                                                          │  │
│  │  • Agent Evaluations (test scenarios)                   │  │
│  │  • Traceability (decision audit trails)                 │  │
│  │  • Agent Insights (cost & performance tracking)         │  │
│  │  • Conversation Logs (full interaction history)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ Function Calling
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    MCP SERVER LAYER                              │
│               (Model Context Protocol Integration)               │
│                                                                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ DigitalOcean   │  │  Terraform      │  │  Prometheus     │ │
│  │ MCP Server     │  │  MCP Server     │  │  MCP Server     │ │
│  │ (Official)     │  │  (HashiCorp)    │  │  (Custom)       │ │
│  │                │  │                 │  │                 │ │
│  │ Services:      │  │ Functions:      │  │ Functions:      │ │
│  │ • droplets     │  │ • validate      │  │ • query_metrics │ │
│  │ • kubernetes   │  │ • plan          │  │ • get_alerts    │ │
│  │ • databases    │  │ • apply         │  │ • check_health  │ │
│  │ • monitoring   │  │ • show_state    │  │                 │ │
│  │ • spaces       │  │ • registry      │  │                 │ │
│  │ • firewalls    │  │                 │  │                 │ │
│  └────────┬───────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼──────────────────┼──────────────────────┼──────────┘
            │                  │                      │
            │                  │                      │
            └──────────────────┼──────────────────────┘
                               │
                               │ API Calls
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                DIGITALOCEAN INFRASTRUCTURE                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Control Plane Droplet (Your Application)                │  │
│  │  • Size: s-2vcpu-4gb                                     │  │
│  │  • Runs: FastAPI, Orchestrator, MCP Clients             │  │
│  │  • IP: <control-plane-ip>                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Target Infrastructure (Demo Resources)                  │  │
│  │                                                          │  │
│  │  ┌────────────────┐  ┌────────────────┐                │  │
│  │  │ web-app        │  │ api-server     │                │  │
│  │  │ s-1vcpu-1gb    │  │ s-1vcpu-1gb    │                │  │
│  │  │ (monitored)    │  │ (monitored)    │                │  │
│  │  └────────────────┘  └────────────────┘                │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────┐                │  │
│  │  │ Prometheus Monitoring              │                │  │
│  │  │ s-1vcpu-1gb                        │                │  │
│  │  │ Scrapes: web-app, api-server      │                │  │
│  │  └────────────────────────────────────┘                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Storage & State                                         │  │
│  │                                                          │  │
│  │  • Spaces: Terraform state, logs, knowledge base files  │  │
│  │  • PostgreSQL (optional): Incident history, agent logs  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌─────────────┐
│   INCIDENT  │
│   OCCURS    │
│  (CPU 95%)  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  1. DETECTION PHASE                          │
│                                              │
│  Monitor Agent:                              │
│  ├─ Calls DO MCP: do-droplet-get-metrics    │
│  ├─ Calls Prometheus MCP: query_metrics     │
│  ├─ Analyzes data                           │
│  └─ Creates incident report                 │
│                                              │
│  Output: Incident{                           │
│    resource: "web-app",                      │
│    metric: "cpu_usage",                      │
│    value: 95,                                │
│    severity: "high"                          │
│  }                                           │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  2. DIAGNOSIS PHASE                          │
│                                              │
│  Diagnostic Agent:                           │
│  ├─ Receives incident                        │
│  ├─ Queries Knowledge Base (RAG)            │
│  │   "High CPU on droplet troubleshooting"  │
│  ├─ Calls Terraform MCP: show-state         │
│  │   (checks current configuration)          │
│  ├─ Analyzes historical incidents           │
│  └─ Generates diagnosis with confidence     │
│                                              │
│  Output: Diagnosis{                          │
│    root_cause: "Undersized droplet",        │
│    recommendation: "Scale up",               │
│    new_size: "s-2vcpu-2gb",                 │
│    confidence: 0.89,                         │
│    estimated_cost: "+$12/mo"                │
│  }                                           │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  3. REMEDIATION PHASE                        │
│                                              │
│  Remediation Agent:                          │
│  ├─ Receives diagnosis                       │
│  ├─ Generates Terraform config change       │
│  ├─ Calls Terraform MCP: validate-config    │
│  ├─ If valid:                                │
│  │   ├─ Calls Terraform MCP: plan           │
│  │   ├─ Reviews plan safety                 │
│  │   └─ Calls Terraform MCP: apply          │
│  ├─ Calls DO MCP: wait-for-droplet-ready    │
│  └─ Verifies fix with Monitor Agent         │
│                                              │
│  Output: Remediation{                        │
│    status: "success",                        │
│    action: "resized_droplet",               │
│    duration: "90s",                          │
│    cost: "$0.02"                            │
│  }                                           │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  4. VERIFICATION & LEARNING                  │
│                                              │
│  ├─ Monitor Agent confirms metrics normal    │
│  ├─ Traceability logs full decision chain   │
│  ├─ Knowledge Base updated with:            │
│  │   • Incident pattern                     │
│  │   • Successful resolution                │
│  │   • Optimal droplet sizing for workload  │
│  └─ Agent Insights tracks performance       │
│                                              │
│  Output: Learned Pattern{                    │
│    "web-app workload requires s-2vcpu-2gb"  │
│    "CPU >80% indicates scaling needed"      │
│  }                                           │
└──────────────────────────────────────────────┘
```

---

## 🔧 Prerequisites & Setup

### Essential Tools to Install

```bash
# 1. DigitalOcean CLI
brew install doctl  # macOS
# or download from: https://github.com/digitalocean/doctl/releases

# 2. Terraform
brew install terraform  # macOS
# or download from: https://www.terraform.io/downloads

# 3. Docker
# Follow: https://docs.docker.com/engine/install/

# 4. Python 3.11+
python3 --version  # Should be 3.11 or higher

# 5. Node.js (for DO MCP Server)
brew install node  # macOS
# or download from: https://nodejs.org/
```

### Project Structure

**IMPORTANT:** The project is split into two main directories:

```
rift/
│
├── frontend/                    # Next.js Application (Pre-built)
│   ├── app/
│   │   ├── page.tsx            # Main dashboard
│   │   ├── layout.tsx          # Root layout
│   │   ├── globals.css         # Global styles (dark punk theme)
│   │   └── api/                # API routes (optional)
│   │
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── StatusCard.tsx      # Agent status cards
│   │   ├── IncidentFeed.tsx    # Live incident stream
│   │   ├── AgentStatus.tsx     # Agent health monitor
│   │   ├── MetricsChart.tsx    # Real-time metrics
│   │   ├── TraceViewer.tsx     # Decision traceability
│   │   ├── Terminal.tsx        # Terminal-style output
│   │   └── QuickProvision.tsx  # NEW: Infrastructure provisioning panel
│   │
│   ├── lib/
│   │   ├── api.ts              # Backend API client
│   │   ├── websocket.ts        # WebSocket connection
│   │   └── utils.ts            # Utility functions
│   │
│   ├── public/
│   │   ├── rift-logo.svg
│   │   └── fonts/
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts      # Dark punk theme config
│   ├── next.config.js
│   └── .env.local
│
└── backend/                     # Python Backend (You'll build this)
    ├── agents/
    │   ├── __init__.py
    │   ├── base_agent.py
    │   ├── monitor_agent.py
    │   ├── diagnostic_agent.py
    │   ├── remediation_agent.py
    │   └── provisioner_agent.py    # NEW: Proactive provisioning
    │
    ├── mcp_clients/
    │   ├── __init__.py
    │   ├── do_mcp.py
    │   ├── terraform_mcp.py
    │   └── prometheus_mcp.py
    │
    ├── orchestrator/
    │   ├── __init__.py
    │   └── coordinator.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── incident.py
    │   └── provision_request.py    # NEW: Provisioning models
    │
    ├── terraform/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── modules/
    │       ├── droplet/            # NEW: Droplet provisioning module
    │       │   ├── main.tf
    │       │   ├── variables.tf
    │       │   └── outputs.tf
    │       ├── database/           # NEW: Database provisioning module
    │       │   ├── main.tf
    │       │   ├── variables.tf
    │       │   └── outputs.tf
    │       ├── loadbalancer/       # NEW: Load balancer module
    │       │   ├── main.tf
    │       │   ├── variables.tf
    │       │   └── outputs.tf
    │       └── complete-stack/     # NEW: Full stack template
    │           ├── main.tf
    │           ├── variables.tf
    │           └── outputs.tf
    │
    ├── demo/
    │   ├── failure_injection.py
    │   └── provision_demo.py       # NEW: Provisioning demos
    │
    ├── tests/
    │   ├── test_monitor.py
    │   ├── test_diagnostic.py
    │   └── agent_evaluations.py
    │
    ├── knowledge-base/
    │   ├── do-docs.md
    │   ├── runbooks.md
    │   └── past-incidents.json
    │
    ├── main.py                  # FastAPI backend
    ├── requirements.txt
    ├── .env
    └── README.md
```

### Directory Responsibilities

**Frontend (`rift/frontend/`):**

- Next.js 14+ with App Router
- Real-time dashboard with WebSocket updates
- **Dark Punk Professional Theme** - Cyberpunk aesthetics with professional polish
- TypeScript + Tailwind CSS
- shadcn/ui components
- Pre-built and ready to use (minimal configuration needed)

**Backend (`rift/backend/`):**

- Python FastAPI application
- AI agents (Monitor, Diagnostic, Remediation)
- MCP server integrations
- WebSocket server for real-time updates
- This is what you'll implement during the hackathon

---

## 🚀 Provisioner Agent (Proactive Infrastructure)

### Overview

The **Provisioner Agent** is Rift's proactive capability - it creates new infrastructure on demand based on natural language requests or predefined templates.

### Core Functionality

**What it does:**

- Interprets infrastructure requests in natural language
- Queries knowledge base for best practices and templates
- Generates Terraform configurations automatically
- Validates configs via Terraform MCP
- Provisions infrastructure with cost estimates
- Reports completion with access details

**Example Requests:**

- "Create a staging environment for our API"
- "Provision a test droplet with 2GB RAM"
- "Deploy a PostgreSQL database"
- "Set up a load balancer for the web tier"

### Architecture

```
User Request (Natural Language)
         ↓
┌────────────────────────────┐
│   PROVISIONER AGENT        │
│  (Gradient AI + RAG)       │
│                            │
│  1. Parse request          │
│  2. Query templates KB     │
│  3. Generate Terraform     │
│  4. Estimate costs         │
│  5. Validate config        │
└──────────┬─────────────────┘
           │
           ↓
┌──────────────────────────┐
│   TERRAFORM MCP          │
│                          │
│  • Validate              │
│  • Plan                  │
│  • Apply                 │
│  • Get outputs           │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│  DigitalOcean            │
│  Infrastructure Created  │
└──────────────────────────┘
```

### Implementation

#### 1. Provisioner Agent Class

````python
# agents/provisioner_agent.py

from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from models.provision_request import ProvisionRequest, ProvisionResult
import json

class ProvisionerAgent(BaseAgent):
    """
    Proactive infrastructure provisioning agent.
    Creates new infrastructure based on natural language requests.
    """

    def __init__(self, agent_id: str, api_key: str):
        super().__init__(agent_id, api_key, "Provisioner")

    async def provision(self, request: ProvisionRequest) -> ProvisionResult:
        """
        Main provisioning workflow.

        Args:
            request: ProvisionRequest with user's infrastructure needs

        Returns:
            ProvisionResult with created resources and access info
        """

        # Step 1: Parse and understand request
        prompt = self._build_provision_prompt(request)

        # Step 2: Query agent with RAG
        response = await self.query_agent(prompt)

        # Step 3: Extract Terraform config from response
        terraform_config = self._extract_terraform(response)

        # Step 4: Validate via MCP
        validation = await self._validate_terraform(terraform_config)

        if not validation["valid"]:
            return ProvisionResult(
                success=False,
                error=validation["errors"]
            )

        # Step 5: Estimate costs
        cost_estimate = await self._estimate_cost(terraform_config)

        # Step 6: Apply configuration
        result = await self._apply_terraform(terraform_config)

        return ProvisionResult(
            success=True,
            resources_created=result["resources"],
            access_info=result["outputs"],
            cost_estimate=cost_estimate,
            terraform_config=terraform_config
        )

    def _build_provision_prompt(self, request: ProvisionRequest) -> str:
        """Build prompt for provisioning request."""

        return f"""
        You are an expert infrastructure engineer. Generate Terraform configuration
        for DigitalOcean based on this request:

        Request: {request.description}

        Requirements:
        - Region: {request.region or "nyc3"}
        - Environment: {request.environment or "development"}
        - Budget: ${request.budget_limit or "unlimited"}

        Use the knowledge base to find:
        1. Best practices for this type of infrastructure
        2. Recommended sizes and configurations
        3. Security best practices
        4. Cost optimization strategies

        Generate complete, production-ready Terraform configuration.
        Include all necessary resources, variables, and outputs.

        Return ONLY valid HCL (Terraform) code, no explanations.
        """

    def _extract_terraform(self, response: str) -> str:
        """Extract Terraform config from agent response."""
        # Remove markdown code fences if present
        config = response.strip()
        if config.startswith("```"):
            # Remove ```hcl or ```terraform
            lines = config.split("\n")
            config = "\n".join(lines[1:-1])
        return config

    async def _validate_terraform(self, config: str) -> Dict[str, Any]:
        """Validate Terraform config via MCP."""
        # Use Terraform MCP server to validate
        # See Terraform MCP client implementation
        pass

    async def _estimate_cost(self, config: str) -> float:
        """Estimate monthly cost of infrastructure."""
        # Parse Terraform to extract resource types and sizes
        # Use DigitalOcean pricing API
        # Return estimated monthly cost
        pass

    async def _apply_terraform(self, config: str) -> Dict[str, Any]:
        """Apply Terraform configuration."""
        # Use Terraform MCP server to apply
        # Return created resources and outputs
        pass
````

#### 2. Provision Request Models

```python
# models/provision_request.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

class ProvisionRequest(BaseModel):
    """User request for infrastructure provisioning."""

    request_id: str = Field(..., description="Unique request ID")
    user_id: str = Field(..., description="User making request")
    description: str = Field(..., description="Natural language description")

    # Optional parameters
    region: Optional[str] = Field("nyc3", description="DigitalOcean region")
    environment: Optional[str] = Field("development", description="Environment type")
    budget_limit: Optional[float] = Field(None, description="Max monthly cost ($)")

    # Template-based provisioning
    template: Optional[str] = Field(None, description="Pre-built template name")
    template_params: Optional[Dict[str, Any]] = Field(None, description="Template parameters")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field("normal", description="Request priority")

class ProvisionResult(BaseModel):
    """Result of provisioning operation."""

    request_id: str = Field(..., description="Original request ID")
    success: bool = Field(..., description="Whether provisioning succeeded")

    # Success fields
    resources_created: Optional[List[Dict[str, Any]]] = Field(None)
    access_info: Optional[Dict[str, str]] = Field(None, description="Access URLs, IPs, etc")
    cost_estimate: Optional[float] = Field(None, description="Estimated monthly cost")
    terraform_config: Optional[str] = Field(None, description="Generated Terraform")

    # Error fields
    error: Optional[str] = Field(None, description="Error message if failed")

    # Metadata
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = Field(None)

class ProvisionTemplate(BaseModel):
    """Pre-built infrastructure template."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="What this template creates")
    terraform_module: str = Field(..., description="Path to Terraform module")
    required_params: List[str] = Field([], description="Required parameters")
    optional_params: Dict[str, Any] = Field({}, description="Optional parameters with defaults")
    estimated_cost: float = Field(..., description="Base monthly cost")
```

#### 3. Pre-built Terraform Modules

**Simple Droplet Module:**

```hcl
# terraform/modules/droplet/main.tf

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

resource "digitalocean_droplet" "instance" {
  name   = var.droplet_name
  region = var.region
  size   = var.size
  image  = var.image

  tags = concat(
    var.tags,
    ["managed-by-rift", "environment-${var.environment}"]
  )

  # User data for initialization
  user_data = var.user_data

  # SSH keys
  ssh_keys = var.ssh_key_ids

  # Enable monitoring
  monitoring = true

  # Enable backups if production
  backups = var.environment == "production" ? true : false
}

# Attach firewall if provided
resource "digitalocean_firewall" "droplet_firewall" {
  count = var.firewall_rules != null ? 1 : 0

  name = "${var.droplet_name}-firewall"

  droplet_ids = [digitalocean_droplet.instance.id]

  dynamic "inbound_rule" {
    for_each = var.firewall_rules.inbound
    content {
      protocol         = inbound_rule.value.protocol
      port_range       = inbound_rule.value.port_range
      source_addresses = inbound_rule.value.source_addresses
    }
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
```

```hcl
# terraform/modules/droplet/variables.tf

variable "droplet_name" {
  description = "Name of the droplet"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "size" {
  description = "Droplet size slug"
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "image" {
  description = "Droplet image"
  type        = string
  default     = "ubuntu-22-04-x64"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
}

variable "tags" {
  description = "Additional tags"
  type        = list(string)
  default     = []
}

variable "ssh_key_ids" {
  description = "SSH key IDs"
  type        = list(number)
  default     = []
}

variable "user_data" {
  description = "User data script"
  type        = string
  default     = ""
}

variable "firewall_rules" {
  description = "Firewall rules"
  type = object({
    inbound = list(object({
      protocol         = string
      port_range       = string
      source_addresses = list(string)
    }))
  })
  default = null
}
```

```hcl
# terraform/modules/droplet/outputs.tf

output "id" {
  description = "Droplet ID"
  value       = digitalocean_droplet.instance.id
}

output "ipv4_address" {
  description = "Public IPv4 address"
  value       = digitalocean_droplet.instance.ipv4_address
}

output "ipv4_address_private" {
  description = "Private IPv4 address"
  value       = digitalocean_droplet.instance.ipv4_address_private
}

output "name" {
  description = "Droplet name"
  value       = digitalocean_droplet.instance.name
}

output "urn" {
  description = "Droplet URN"
  value       = digitalocean_droplet.instance.urn
}
```

**Database Module:**

```hcl
# terraform/modules/database/main.tf

resource "digitalocean_database_cluster" "db" {
  name       = var.db_name
  engine     = var.engine
  version    = var.engine_version
  size       = var.size
  region     = var.region
  node_count = var.node_count

  tags = concat(
    var.tags,
    ["managed-by-rift", "environment-${var.environment}"]
  )

  # Enable automated backups
  maintenance_window {
    day  = "sunday"
    hour = "02:00:00"
  }
}

resource "digitalocean_database_firewall" "db_firewall" {
  cluster_id = digitalocean_database_cluster.db.id

  dynamic "rule" {
    for_each = var.allowed_droplet_ids
    content {
      type  = "droplet"
      value = rule.value
    }
  }
}
```

### API Endpoints for Provisioning

Add to FastAPI backend:

```python
# main.py additions

@app.post("/provision/create")
async def provision_infrastructure(request: ProvisionRequest):
    """
    Provision new infrastructure based on request.
    """
    try:
        # Use Provisioner Agent
        result = await provisioner_agent.provision(request)

        # Broadcast via WebSocket
        await websocket_manager.broadcast({
            "type": "provision_started",
            "request_id": request.request_id,
            "description": request.description
        })

        if result.success:
            await websocket_manager.broadcast({
                "type": "provision_complete",
                "request_id": request.request_id,
                "resources": result.resources_created,
                "cost": result.cost_estimate
            })

        return result

    except Exception as e:
        logger.error(f"Provisioning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provision/templates")
async def list_templates():
    """Get available provisioning templates."""
    return {
        "templates": [
            {
                "id": "simple-droplet",
                "name": "Simple Droplet",
                "description": "Single droplet with basic configuration",
                "estimated_cost": 6.00
            },
            {
                "id": "postgres-db",
                "name": "PostgreSQL Database",
                "description": "Managed PostgreSQL cluster",
                "estimated_cost": 15.00
            },
            {
                "id": "web-stack",
                "name": "Complete Web Stack",
                "description": "Load balancer + 2 app servers + database",
                "estimated_cost": 45.00
            }
        ]
    }

@app.post("/provision/template/{template_id}")
async def provision_from_template(template_id: str, params: Dict[str, Any]):
    """Provision infrastructure from pre-built template."""
    # Load template
    # Apply with provided params
    # Return result
    pass
```

### Knowledge Base for Provisioning

Add to knowledge base:

```markdown
# knowledge-base/provisioning-templates.md

## Infrastructure Templates

### Simple Droplet

**Use Case:** Test environments, single-instance applications
**Resources:**

- 1 Droplet (s-1vcpu-1gb)
- Basic firewall (HTTP, HTTPS, SSH)
  **Cost:** ~$6/month

### Web Application Stack

**Use Case:** Production web applications
**Resources:**

- 1 Load Balancer
- 2+ Droplets (s-2vcpu-4gb)
- 1 PostgreSQL Database (db-s-1vcpu-1gb)
- Firewall rules
  **Cost:** ~$45/month base

### Database Cluster

**Use Case:** Standalone databases
**Resources:**

- PostgreSQL/MySQL/Redis cluster
- Automated backups
- Firewall rules
  **Cost:** ~$15/month

## Best Practices

### Sizing Guidelines

- Development: s-1vcpu-1gb ($6/mo)
- Staging: s-2vcpu-2gb ($12/mo)
- Production: s-2vcpu-4gb+ ($24+/mo)

### Security

- Always enable monitoring
- Use firewalls for all resources
- Enable backups for production
- Use private networking when possible

### Cost Optimization

- Use appropriate sizes (don't over-provision)
- Enable backups only for production
- Use load balancers only when needed
- Consider reserved instances for stable workloads
```

---

## 🌌 Rift Branding & Terminology

### Core Concept

**Rift** = Powerful force that creates instant connections or tears through problems

Just like science fiction rifts:

- Create instant pathways through space
- Tear through barriers
- Make the impossible instant
- Connect distant points immediately

### Key Terminology

**Opening a Rift (Provisioning):**

- "Opening a rift"
- "Creating a portal"
- "Tearing open infrastructure"
- "Materializing resources"

**Closing a Rift (Healing):**

- "Closing the rift"
- "Sealing the breach"
- "Repairing the tear"
- "Restoring dimensions"

**Detecting a Rift (Monitoring):**

- "Rift detected"
- "Breach identified"
- "Dimensional anomaly"
- "System tear"

**Example Usage:**

```
❌ "Provisioning droplet..."
✅ "Opening rift..."

❌ "High CPU detected"
✅ "RIFT DETECTED: High CPU"

❌ "Issue resolved"
✅ "RIFT CLOSED: System restored"

❌ "Creating infrastructure"
✅ "Rift opened: Infrastructure materialized"
```

### Visual Identity

**Primary Logo:** 🌌 (galaxy/rift portal)  
**Alternative:** ⚡ (energy tear)  
**Accent:** 🔮 (dimensional portal)

**Rift Effects:**

```css
/* Rift glow effect */
box-shadow: 0 0 20px rgba(0, 255, 159, 0.4), 0 0 40px rgba(255, 0, 255, 0.2);

/* Rift pulse animation */
@keyframes rift-pulse {
  0%,
  100% {
    opacity: 1;
    box-shadow: 0 0 20px rgba(255, 0, 255, 0.6);
  }
  50% {
    opacity: 0.7;
    box-shadow: 0 0 40px rgba(255, 0, 255, 0.8);
  }
}
```

**Color Accents for Rift:**

- Rift Energy: `#ff00ff` (neon magenta)
- Portal Edge: `#00d4ff` (cyber blue)
- Rift Core: `#00ff9f` (neon green)

### UI Components with Rift Theme

**Status Indicators:**

```
🌌 Rift Active
⚡ Rift Opening
🔴 Rift Detected
✅ Rift Closed
```

**Dashboard Sections:**

```
┌─────────────────────────────────────────┐
│  🌌 RIFT                   [⚡] ACTIVE │
├─────────────────────────────────────────┤
│  Autonomous Infrastructure Orchestrator │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  🌌 OPEN A RIFT           [PROACTIVE]  │
├─────────────────────────────────────────┤
│  🖥️  Test Droplet          $6/mo       │
│      [⚡ Open Rift]                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  🔴 LIVE: RIFT ACTIVITY                 │
├─────────────────────────────────────────┤
│  14:30:45 | 🌌 RIFT OPENED: droplet-1  │
│  14:32:15 | 🔴 RIFT DETECTED: High CPU │
│  14:33:45 | ✅ RIFT CLOSED: Restored   │
└─────────────────────────────────────────┘
```

### Messaging Framework

**One-Liner:**

> "Rift through operational complexity"

**Elevator Pitch (30 seconds):**

> "Rift is an autonomous infrastructure orchestrator. Like science fiction rifts that create instant connections, Rift opens rifts to create infrastructure in 35 seconds and closes rifts to fix problems in 90 seconds. Four AI agents powered by DigitalOcean Gradient AI work together - all autonomous, all traceable."

**Extended Pitch (60 seconds):**

> "In science fiction, rifts are powerful - they create instant connections through space, tear through barriers, make the impossible instant. That's what Rift does for your operations. Four AI agents work together: Monitor detects rifts in your system, Diagnostic analyzes the breach, Remediation closes the rift, and Provisioner opens new rifts on demand. Built on DigitalOcean Gradient AI using Model Context Protocol, Rift operates completely autonomously - from provisioning to healing. 35 seconds to open a rift, 90 seconds to close one. Rift through operational complexity."

**Social Media (280 chars):**

> "Rift: Opens rifts to create infrastructure (35s), closes rifts to fix problems (90s). Four AI agents, 100% autonomous. Built on @digitalocean Gradient AI. Rift through operational complexity. 🌌⚡"

---

## 🎨 Frontend Design System (Dark Punk Professional Theme)

### Theme Philosophy

**"Professional Cyberpunk"** - The aesthetic of a high-tech operations center. Think: Blade Runner meets Bloomberg Terminal. Dark, sleek, with neon accents that convey urgency and precision.

### Color Palette

**Primary Colors:**

```css
--background: #0a0e17; /* Deep space black */
--surface: #111827; /* Card/panel background */
--surface-elevated: #1f2937; /* Elevated elements */

--primary: #00ff9f; /* Neon green (success/active) */
--secondary: #00d4ff; /* Cyber blue (info) */
--accent: #ff00ff; /* Neon magenta (alerts) */

--danger: #ff3366; /* Hot pink red (errors) */
--warning: #ffaa00; /* Electric amber (warnings) */
--success: #00ff9f; /* Neon green */

--text-primary: #e5e7eb; /* Almost white */
--text-secondary: #9ca3af; /* Muted gray */
--text-muted: #6b7280; /* Very muted */

--border: #1f2937; /* Subtle borders */
--border-bright: #374151; /* Highlighted borders */
```

**Gradient Accents:**

```css
--gradient-primary: linear-gradient(135deg, #00ff9f 0%, #00d4ff 100%);
--gradient-danger: linear-gradient(135deg, #ff3366 0%, #ff00ff 100%);
--glow-primary: 0 0 20px rgba(0, 255, 159, 0.3);
--glow-danger: 0 0 20px rgba(255, 51, 102, 0.3);
```

### Typography

**Fonts:**

- **Headers:** `"JetBrains Mono"` or `"Space Mono"` (monospace, technical)
- **Body:** `"Inter"` or `"DM Sans"` (clean, readable)
- **Code/Terminal:** `"Fira Code"` or `"Cascadia Code"` (with ligatures)

**Font Guidelines:**

- Headers: Monospace fonts for technical feel
- Body text: Clean sans-serif for readability
- Code blocks: Monospace with ligature support
- All caps for labels and important status

### Component Styles

**Cards/Panels:**

```tsx
// Dark surface with subtle border
className = "bg-[#111827] border border-[#1f2937] rounded-lg shadow-lg";

// Hover state - add glow
className =
  "hover:border-[#00ff9f] hover:shadow-[0_0_20px_rgba(0,255,159,0.1)]";
```

**Status Indicators:**

```tsx
// Active/Success - Neon green with pulse
<div className="h-2 w-2 rounded-full bg-[#00ff9f] animate-pulse" />

// Warning - Electric amber
<div className="h-2 w-2 rounded-full bg-[#ffaa00]" />

// Critical - Hot pink with faster pulse
<div className="h-2 w-2 rounded-full bg-[#ff3366] animate-pulse" />
```

**Terminal/Console Style:**

```tsx
<div className="bg-black border border-[#00ff9f] rounded p-4 font-mono text-[#00ff9f]">
  <div className="flex gap-2">
    <span className="text-[#00ff9f]">●</span>
    <span>14:32:15 | Rift detected high CPU (95%)</span>
  </div>
</div>
```

### UI Components Checklist

**Must Have (Core Demo):**

- [ ] Status cards for 4 agents (Monitor, Diagnostic, Remediation, Provisioner)
- [ ] Real-time incident feed (terminal style)
- [ ] System metrics dashboard (CPU, Memory, Disk)
- [ ] Live update indicator (WebSocket connection status)
- [ ] Quick Provision panel (NEW - infrastructure on demand)

**Nice to Have (If Time):**

- [ ] Trace viewer (decision path visualization)
- [ ] Event timeline with filtering
- [ ] Agent performance charts
- [ ] Alert notifications
- [ ] Provisioning history/log

**Skip (Not Critical):**

- [ ] Settings panel
- [ ] Historical data views
- [ ] User management
- [ ] Mobile responsiveness
- [ ] Complex provisioning forms

### Design Principles for Hackathon

1. **Focus on Real-time** - Everything should update live during demo
2. **High Contrast** - Dark background with bright accents (easy to see on projector)
3. **Big and Bold** - Large fonts, clear indicators (visible from back of room)
4. **Terminal Aesthetic** - Monospace fonts, console-style output (appeals to developers)
5. **Minimal Animation** - Subtle pulse effects only, no distractions
6. **Professional First** - Clean layout, proper spacing, polished feel

### Component Code Examples

#### QuickProvision Panel (NEW)

```tsx
// components/QuickProvision.tsx

"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ProvisionTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  estimatedCost: number;
}

const templates: ProvisionTemplate[] = [
  {
    id: "simple-droplet",
    name: "Test Droplet",
    description: "1 vCPU, 1GB RAM",
    icon: "🖥️",
    estimatedCost: 6,
  },
  {
    id: "postgres-db",
    name: "PostgreSQL",
    description: "Managed database",
    icon: "💾",
    estimatedCost: 15,
  },
  {
    id: "web-stack",
    name: "Web Stack",
    description: "LB + 2 servers + DB",
    icon: "🌐",
    estimatedCost: 45,
  },
];

export function QuickProvision() {
  const [provisioning, setProvisioning] = useState<string | null>(null);
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  const handleProvision = async (templateId: string) => {
    setProvisioning(templateId);

    try {
      const response = await fetch("/api/provision/template/" + templateId, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (response.ok) {
        setCompleted((prev) => new Set(prev).add(templateId));
      }
    } catch (error) {
      console.error("Provisioning failed:", error);
    } finally {
      setProvisioning(null);
    }
  };

  return (
    <Card className="bg-[#111827] border-[#1f2937] p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[#00ff9f] font-mono uppercase tracking-wider text-lg">
          🚀 Quick Provision
        </h3>
        <Badge variant="outline" className="border-[#00d4ff] text-[#00d4ff]">
          PROACTIVE
        </Badge>
      </div>

      <p className="text-[#9ca3af] text-sm mb-6">
        Provision infrastructure on demand
      </p>

      <div className="space-y-3">
        {templates.map((template) => (
          <div
            key={template.id}
            className="bg-[#0a0e17] border border-[#1f2937] rounded-lg p-4 hover:border-[#00ff9f] transition-all"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{template.icon}</span>
                <div>
                  <div className="text-[#e5e7eb] font-medium">
                    {template.name}
                  </div>
                  <div className="text-[#6b7280] text-sm">
                    {template.description}
                  </div>
                </div>
              </div>
              <div className="text-[#00d4ff] text-sm font-mono">
                ${template.estimatedCost}/mo
              </div>
            </div>

            <Button
              onClick={() => handleProvision(template.id)}
              disabled={
                provisioning === template.id || completed.has(template.id)
              }
              className={`
                w-full mt-2 font-mono uppercase text-xs
                ${
                  completed.has(template.id)
                    ? "bg-[#00ff9f] text-black"
                    : "bg-gradient-to-r from-[#00ff9f] to-[#00d4ff] text-black"
                }
                ${provisioning === template.id ? "animate-pulse" : ""}
              `}
            >
              {provisioning === template.id && "⚙️ Provisioning..."}
              {completed.has(template.id) && "✅ Provisioned"}
              {!provisioning &&
                !completed.has(template.id) &&
                `🚀 Provision ${template.name}`}
            </Button>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-[#1f2937]">
        <div className="flex items-center justify-between text-sm">
          <span className="text-[#6b7280]">Total provisioned:</span>
          <span className="text-[#00ff9f] font-mono">
            {completed.size} resources
          </span>
        </div>
      </div>
    </Card>
  );
}
```

#### Status Card with Provisioner Agent

```tsx
// Update StatusCard.tsx to include Provisioner Agent

const agents = [
  { name: "Monitor", status: "active", color: "#00ff9f" },
  { name: "Diagnostic", status: "active", color: "#00d4ff" },
  { name: "Remediation", status: "active", color: "#00ff9f" },
  { name: "Provisioner", status: "active", color: "#ff00ff" }, // NEW!
];
```

### Pre-built Frontend Setup

The frontend directory comes with:

- ✅ Next.js 14 with App Router configured
- ✅ Tailwind CSS with dark punk theme
- ✅ shadcn/ui components installed
- ✅ WebSocket client configured
- ✅ API client with proper error handling
- ✅ Responsive layout (desktop-focused)

**You only need to:**

1. Update API endpoint in `.env.local`
2. Run `npm install`
3. Run `npm run dev`
4. Frontend will connect to your FastAPI backend

---

## 📦 Implementation Phases

### Phase 1: Foundation (Hours 0-2)

**Goal:** Set up DigitalOcean infrastructure and MCP servers

**Claude Code Instructions:**

1. **Create DigitalOcean resources**

   ```bash
   # In terminal, run:
   doctl compute droplet create control-plane --image ubuntu-24-04-x64 --size s-2vcpu-4gb --region nyc3
   doctl compute droplet create web-app --image ubuntu-24-04-x64 --size s-1vcpu-1gb --region nyc3
   doctl compute droplet create api-server --image ubuntu-24-04-x64 --size s-1vcpu-1gb --region nyc3
   doctl spaces create rift-tfstate --region nyc3
   ```

2. **Create `.env` file**

   ```
   File: .env

   Add these environment variables:
   - DIGITALOCEAN_API_TOKEN
   - MONITOR_AGENT_ENDPOINT
   - MONITOR_AGENT_KEY
   - DIAGNOSTIC_AGENT_ENDPOINT
   - DIAGNOSTIC_AGENT_KEY
   - REMEDIATION_AGENT_ENDPOINT
   - REMEDIATION_AGENT_KEY
   - PROMETHEUS_URL=http://localhost:9090
   ```

3. **Create `requirements.txt`**

   ```
   File: requirements.txt

   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   python-dotenv==1.0.0
   httpx==0.25.1
   pydantic==2.5.0
   aiohttp==3.9.0
   prometheus-client==0.19.0
   python-terraform==0.10.1
   streamlit==1.28.0
   ```

4. **Install Prometheus on droplets**
   - SSH into each droplet
   - Install node_exporter
   - Configure Prometheus on control-plane

---

### Phase 2: Monitor Agent (Hours 2-4)

**Goal:** Build agent that detects infrastructure issues

**Claude Code Instructions:**

1. **Create base agent class**

   ```
   File: agents/base_agent.py

   Create a BaseAgent class with:
   - __init__(agent_name, endpoint, access_key, knowledge_base_ids)
   - async call_agent(prompt, context) -> Dict
   - async call_function(function_name, parameters) -> Dict
   - Error handling with retries
   - Logging of all interactions
   ```

2. **Create DigitalOcean MCP client**

   ```
   File: mcp_clients/do_mcp.py

   Implement DigitalOceanMCP class with methods:
   - async list_droplets() -> List[Droplet]
   - async get_droplet_metrics(droplet_id) -> MetricsData
   - async get_droplet_details(droplet_id) -> DropletDetails
   - async resize_droplet(droplet_id, new_size) -> ResizeResult
   - async reboot_droplet(droplet_id) -> RebootResult

   Use the official DO MCP Server at: https://github.com/digitalocean/mcp-server
   ```

3. **Create Prometheus MCP client**

   ```
   File: mcp_clients/prometheus_mcp.py

   Implement PrometheusClient with methods:
   - async query_instant(query) -> QueryResult
   - async query_range(query, start, end, step) -> RangeResult
   - async get_alerts() -> List[Alert]
   - async check_threshold(metric, threshold) -> bool

   Common queries to support:
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O
   ```

4. **Implement Monitor Agent**

   ```
   File: agents/monitor_agent.py

   Create MonitorAgent(BaseAgent) with:
   - async check_droplet_health(droplet_id) -> HealthStatus
   - async check_all_infrastructure() -> List[Incident]
   - async classify_severity(metric, value) -> str
   - async create_incident(findings) -> Incident

   Integration:
   - Use DO MCP to get droplet list
   - Use Prometheus MCP to get metrics
   - Use Gradient AI agent to detect anomalies
   - Generate structured Incident objects
   ```

5. **Create data models**

   ```
   File: models/incident.py

   Define Pydantic models:
   - Incident (id, timestamp, resource, metric, value, severity)
   - Diagnosis (root_cause, confidence, recommendations)
   - RemediationPlan (actions, terraform_config, rollback)
   - RemediationResult (status, duration, cost)
   ```

---

### Phase 3: Diagnostic Agent (Hours 4-8)

**Goal:** Build agent that diagnoses root causes using RAG

**Claude Code Instructions:**

1. **Set up Knowledge Base in Gradient AI**

   - Go to Gradient AI Platform console
   - Create Knowledge Base
   - Upload documents from knowledge-base/ folder
   - Enable auto-indexing
   - Note the Knowledge Base ID

2. **Create Terraform MCP client**

   ```
   File: mcp_clients/terraform_mcp.py

   Implement TerraformMCP class with:
   - async validate_config(config) -> ValidationResult
   - async plan(config) -> PlanResult
   - async apply(config, auto_approve) -> ApplyResult
   - async show_state(resource) -> StateData
   - async get_provider_docs(provider) -> Docs

   Use HashiCorp's official Terraform MCP Server:
   docker run -i --rm hashicorp/terraform-mcp-server
   ```

3. **Implement Diagnostic Agent**

   ```
   File: agents/diagnostic_agent.py

   Create DiagnosticAgent(BaseAgent) with:
   - async diagnose_incident(incident) -> Diagnosis
   - async query_knowledge_base(query) -> List[KnowledgeEntry]
   - async analyze_infrastructure_state(resource) -> StateAnalysis
   - async calculate_confidence(evidence) -> float
   - async generate_remediation_plan(diagnosis) -> RemediationPlan

   RAG Integration:
   - Query knowledge base for similar incidents
   - Search for troubleshooting steps
   - Find best practices for resolution
   - Combine with current state analysis
   ```

4. **Add confidence scoring**

   ```
   Implement confidence calculation based on:
   - Number of similar past incidents
   - Quality of knowledge base matches
   - Current infrastructure state validation
   - Historical success rate of proposed solution

   Formula:
   confidence = (0.4 * kb_match_score) +
                (0.3 * state_validation_score) +
                (0.3 * historical_success_rate)
   ```

---

### Phase 4: Remediation Agent (Hours 8-12)

**Goal:** Build agent that executes fixes safely

**Claude Code Instructions:**

1. **Create Terraform modules**

   ```
   Directory: terraform/modules/

   Create modules for:
   - resize_droplet/ (scale up/down droplets)
   - add_volume/ (increase disk space)
   - update_firewall/ (security fixes)
   - restart_service/ (service recovery)

   Each module should have:
   - main.tf (resource definitions)
   - variables.tf (input variables)
   - outputs.tf (return values)
   ```

2. **Implement safety validator**

   ```
   File: agents/safety_validator.py

   Create SafetyValidator class with:
   - async validate_plan(plan) -> ValidationResult
   - async check_destructive_ops(plan) -> bool
   - async estimate_cost(plan) -> CostEstimate
   - async verify_rollback_possible(plan) -> bool

   Safety rules:
   - Require approval for: delete, destroy, terminate
   - Cost threshold: $50 (require approval above)
   - Always validate before applying
   - Ensure rollback plan exists
   ```

3. **Implement Remediation Agent**

   ```
   File: agents/remediation_agent.py

   Create RemediationAgent(BaseAgent) with:
   - async execute_remediation(plan) -> RemediationResult
   - async generate_terraform(action, params) -> str
   - async validate_terraform(config) -> ValidationResult
   - async apply_changes(config, auto_approve) -> ApplyResult
   - async verify_fix(incident_id) -> bool
   - async rollback(plan) -> RollbackResult

   Workflow:
   1. Generate Terraform config
   2. Validate via Terraform MCP
   3. Check safety rules
   4. Execute dry-run (plan)
   5. If safe, apply changes
   6. Verify fix with Monitor Agent
   7. Update knowledge base
   ```

4. **Add rollback capability**

   ```
   Implement automatic rollback if:
   - Applied changes don't fix issue
   - New issues are introduced
   - Health checks fail after change
   - User manually triggers rollback

   Store previous state before each change
   ```

---

### Phase 5: Orchestrator (Hours 12-16)

**Goal:** Coordinate all agents and provide API

**Claude Code Instructions:**

1. **Create FastAPI application**

   ```
   File: main.py

   Create FastAPI app with endpoints:

   # main.py
   """
   Rift - The infrastructure fixer that never sleeps
   Autonomous Infrastructure Orchestrator
   Powered by DigitalOcean Gradient AI + MCP
   """

   @app.post("/incidents/detect")
   async def detect_incidents() -> List[Incident]

   @app.post("/incidents/diagnose")
   async def diagnose_incident(incident_id: str) -> Diagnosis

   @app.post("/incidents/remediate")
   async def remediate_incident(incident_id: str, auto_approve: bool = False) -> RemediationResult

   @app.get("/status")
   async def get_system_status() -> SystemStatus

   @app.get("/agents/health")
   async def check_agents_health() -> AgentHealthStatus

   @app.websocket("/ws/events")
   async def websocket_events(websocket: WebSocket)

   Add:
   - CORS middleware
   - Error handling
   - Logging middleware
   - Authentication (simple token)
   ```

2. **Create Agent Coordinator**

   ```
   File: orchestrator/coordinator.py

   Create Coordinator class with:
   - async start_autonomous_loop()
   - async handle_incident_workflow(incident)
   - async route_to_agent(agent_type, request)
   - async aggregate_results(results)
   - async update_knowledge_base(incident, diagnosis, result)

   Main Loop:
   while True:
       incidents = await monitor_agent.check_all_infrastructure()
       for incident in incidents:
           diagnosis = await diagnostic_agent.diagnose(incident)
           if diagnosis.confidence > 0.85:
               result = await remediation_agent.execute(diagnosis)
               await verify_and_learn(incident, diagnosis, result)
       await asyncio.sleep(30)
   ```

3. **Add logging and traceability**

   ```
   File: utils/logger.py

   Implement structured logging:
   - JSON format
   - Include trace_id for request tracking
   - Log all agent decisions with reasoning
   - Store in file and optionally database

   Log structure:
   {
     "timestamp": "ISO-8601",
     "level": "INFO",
     "event_type": "incident_detected",
     "trace_id": "uuid",
     "agent": "monitor",
     "details": {...}
   }
   ```

4. **Add WebSocket for real-time updates**

   ```
   Implement WebSocket endpoint that:
   - Broadcasts incidents as they're detected
   - Sends diagnosis updates
   - Streams remediation progress
   - Pushes agent health status

   Use for live demo visualization
   ```

---

### Phase 6: Testing (Hours 16-18)

**Goal:** Ensure reliability with comprehensive testing

**Claude Code Instructions:**

1. **Create Agent Evaluations**

   ```
   File: tests/agent_evaluations.py

   Define test scenarios:

   SCENARIOS = [
       {
           "name": "high_cpu_scenario",
           "input": {"cpu_usage": 95, "resource": "web-app"},
           "expected_diagnosis": "undersized_droplet",
           "expected_action": "resize",
           "expected_confidence": 0.85
       },
       {
           "name": "disk_full_scenario",
           "input": {"disk_usage": 92, "resource": "api-server"},
           "expected_diagnosis": "disk_cleanup_needed",
           "expected_action": "clean_logs"
       },
       # Add 8-10 more scenarios
   ]

   For each scenario:
   - Run through full workflow
   - Measure accuracy
   - Track response time
   - Calculate cost
   - Generate report
   ```

2. **Integration tests**

   ```
   File: tests/test_integration.py

   Test:
   - MCP server connectivity
   - Agent API responses
   - End-to-end incident workflow
   - Rollback functionality
   - Error handling
   ```

3. **Performance tests**

   ```
   File: tests/test_performance.py

   Measure:
   - Agent response times
   - Concurrent incident handling
   - API latency
   - Token usage per incident
   - Infrastructure costs
   ```

---

### Phase 7: Demo Preparation (Hours 18-22)

**Goal:** Create impressive, reliable demo

**Claude Code Instructions:**

1. **Create failure injection scripts**

   ```
   File: demo/failure_injection.py

   Implement functions:

   def inject_cpu_spike(droplet_ip, duration=300):
       """Stress CPU using stress-ng"""
       ssh_run(droplet_ip, f"stress-ng --cpu 8 --timeout {duration}s &")

   def inject_disk_fill(droplet_ip, size_mb=5000):
       """Fill disk with dummy file"""
       ssh_run(droplet_ip, f"dd if=/dev/zero of=/tmp/bigfile bs=1M count={size_mb}")

   def kill_service(droplet_ip, service_name):
       """Stop a service"""
       ssh_run(droplet_ip, f"systemctl stop {service_name}")

   def inject_memory_leak(droplet_ip):
       """Simulate memory leak"""
       ssh_run(droplet_ip, "stress-ng --vm 1 --vm-bytes 90% --timeout 300s &")
   ```

2. **Create simple dashboard (optional)**

   ```
   File: dashboard/app.py

   Use Streamlit to create:
   - System status overview
   - Active incidents list
   - Real-time agent logs
   - Metrics charts
   - Remediation history

   Keep it simple - terminal output is fine too!
   ```

3. **Record backup demo video**

   ```
   Use OBS or QuickTime to record:
   1. Normal system operation
   2. Failure injection
   3. Agent detection and diagnosis
   4. Automatic remediation
   5. Verification and results

   Have this ready in case live demo fails
   ```

---

## 🎭 Demo Script (Exact Steps)

### Pre-Demo Setup (5 minutes before)

```bash
# ============================================
# BACKEND: Start FastAPI Server
# ============================================
# Terminal 1: Backend API
cd ~/hackathon/rift/backend
source venv/bin/activate
python main.py
# Should start on http://localhost:8000

# ============================================
# FRONTEND: Start Next.js Dashboard
# ============================================
# Terminal 2: Frontend
cd ~/hackathon/rift/frontend
npm run dev
# Should start on http://localhost:3000

# ============================================
# MONITORING: Watch Logs
# ============================================
# Terminal 3: Backend logs (optional)
cd ~/hackathon/rift/backend
tail -f logs/rift.log

# ============================================
# DEMO CONTROLS: Failure Injection
# ============================================
# Terminal 4: Demo commands
cd ~/hackathon/rift/backend/demo

# Verify everything is running
curl http://localhost:8000/agents/health
curl http://localhost:3000  # Should return Next.js page

# Open browser
open http://localhost:3000  # macOS
# or
xdg-open http://localhost:3000  # Linux
```

### Demo Flow (7 minutes) - WITH DASHBOARD

**[0:00-0:30] Hook + Dashboard Intro**

```
YOU: "In science fiction, rifts are powerful.
     They create instant connections through space.
     They tear through barriers.
     They make the impossible... instant.

     This is Rift."

[Open browser to http://localhost:3000]
[Show the dark punk dashboard with all 4 agents active]

YOU: "Rift does two things:
     Opens rifts to create infrastructure.
     Closes rifts to fix problems.

     All autonomous. All instant.
     Watch."
```

**[0:30-1:30] Demonstrate PROACTIVE (Provisioning)**

```
[Point to QuickProvision panel on dashboard]

YOU: "Let's start with the proactive side.
     Watch Rift create infrastructure on demand."

[Click "Provision Test Droplet" button]

[Dashboard shows in real-time:]
  "14:30:01 | 🔧 Opening rift..."
  "14:30:05 | 📋 Generated Terraform configuration"
  "14:30:10 | ✅ Configuration validated"
  "14:30:15 | 🚀 🚀 Materializing infrastructure..."
  "14:30:45 | ✅ RIFT OPENED: test-droplet-1 ready"
  "          | 🔗 IP: 192.168.1.100"
  "          | 💰 Cost: $6/month"

YOU: "35 seconds. From request to running infrastructure.
     Natural language to Terraform to deployed droplet.
     That's the power of opening a rift."
```

**[1:30-4:30] Demonstrate REACTIVE (Self-Healing)**

```bash
# Run in terminal (judges don't see this)
python failure_injection.py --inject cpu --target web-app
```

```
[Switch focus back to dashboard]

YOU: "Now closing a rift. Let me tear open a problem."

[Dashboard comes alive:]
- Monitor Agent status: "⚠ DETECTING..."
- Incident feed scrolls:
  "14:32:15 | 🔴 ALERT: RIFT DETECTED: High CPU (95%)"
  "14:32:18 | 🔍 Diagnosing root cause..."

[CPU metric bar turns red]

YOU: "Detected in 3 seconds. Now watch it diagnose and fix."

[Diagnostic Agent activates:]
  "14:32:22 | 💡 Root cause: Undersized droplet"
  "14:32:22 | 📋 Recommended: Resize to s-2vcpu-4gb"
  "14:32:22 | 💰 Cost impact: +$12/month"

[Remediation Agent executes:]
  "14:32:25 | 🔧 Executing: Terraform resize"
  "14:32:30 | ⚙️  Applying infrastructure changes..."
  "14:33:45 | ✅ RIFT CLOSED: System restored successfully"

[CPU drops to 42%, turns green]
[All agents return to "Active"]

YOU: "90 seconds total. Completely autonomous.
     No human intervention. No downtime."
```

**[4:30-5:30] Show Traceability**

```
[Click on resolved incident in feed]
[Opens trace viewer]

YOU: "This is what makes Rift special - full traceability.

[Point to trace view showing:]
- Input: System metrics, alert data
- RAG retrieval: Similar past incidents, DO docs, best practices
- Decision logic: Cost-benefit analysis, confidence scores
- Action taken: Exact Terraform configuration used
- Validation: Success metrics, cost impact

"Every AI decision is auditable. Not a black box.
You can see exactly why Rift made each choice."
```

**[5:30-6:30] The Complete Picture**

```
[Return to main dashboard showing healthy state]

YOU: "That's Rift.

[Point to each agent as you say it]

Four AI agents working together:
• Monitor Agent - Detects rifts in the system
• Diagnostic Agent - Analyzes the breach
• Remediation Agent - Closes the rift
• Provisioner Agent - Opens new rifts on demand

All powered by DigitalOcean Gradient AI.
All using the Model Context Protocol.

Opening rifts to create.
Closing rifts to heal.
All autonomous."
```

**[6:30-7:00] Closing**

```
YOU: "This is the future of operations.

Key numbers:
✅ 35 seconds to open a rift (provision)
✅ 90 seconds to close a rift (heal)
✅ 100% autonomous
✅ Full traceability

Rift through operational complexity.

Questions?"

[Confident smile, powerful pause]
```

---

## 🔧 Troubleshooting

### Common Issues

**Gradient AI Agent Not Responding**

```bash
# Check agent status in console
# Verify credentials in .env
# Test with curl:
curl -X POST $MONITOR_AGENT_ENDPOINT/query \
  -H "Authorization: Bearer $MONITOR_AGENT_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

**MCP Server Connection Failed**

```bash
# Restart DO MCP Server
cd mcp-server && npm start

# Restart Terraform MCP
docker restart terraform-mcp
```

**Demo Fails Live**

- Play backup video
- Explain what "would have happened"
- Show architecture and code instead
- Judges appreciate honesty

---

## ⏱️ Hackathon Timeline Checklist

### Hour 0-2: Foundation ✅

- [ ] Create DO droplets
- [ ] Set up Prometheus
- [ ] Initialize 4 Gradient AI agents (Monitor, Diagnostic, Remediation, Provisioner)
- [ ] Test MCP servers
- [ ] Create project structure

### Hour 2-4: Monitor Agent ✅

- [ ] Implement monitor_agent.py
- [ ] Create DO MCP client
- [ ] Create Prometheus MCP client
- [ ] Test incident detection

### Hour 4-8: Diagnostic Agent ✅

- [ ] Implement diagnostic_agent.py
- [ ] Create Terraform MCP client
- [ ] Upload docs to Knowledge Base
- [ ] Test RAG queries

### Hour 8-12: Remediation Agent ✅

- [ ] Implement remediation_agent.py
- [ ] Create Terraform modules for remediation
- [ ] Implement safety checks
- [ ] Test infrastructure changes

### Hour 12-16: Orchestrator + Provisioner Agent ✅ (UPDATED)

- [ ] Create FastAPI app
- [ ] Implement coordinator
- [ ] Add WebSocket support
- [ ] **NEW: Implement provisioner_agent.py (2 hours)**
- [ ] **NEW: Create provisioning Terraform modules (simple droplet, database)**
- [ ] **NEW: Add provisioning API endpoints**
- [ ] End-to-end testing

### Hour 16-18: Testing & Frontend Integration ✅

- [ ] Agent evaluations (all 4 agents)
- [ ] Integration tests
- [ ] **NEW: Test provisioning flow**
- [ ] **NEW: Integrate QuickProvision component in frontend**
- [ ] Fix bugs
- [ ] Optimize prompts

### Hour 18-20: Demo Prep ✅

- [ ] Failure injection scripts
- [ ] **NEW: Provisioning demo script**
- [ ] Test complete demo 5x times (reactive + proactive)
- [ ] Record backup video
- [ ] Record backup video
- [ ] Prepare presentation

### Hour 20-22: Polish ✅

- [ ] Clean code
- [ ] Write README
- [ ] Practice pitch

### Hour 22-24: Buffer ✅

- [ ] Final testing
- [ ] Sleep 2-3 hours
- [ ] Morning verification

---

## 🎯 Success Metrics

### Must Have

- [ ] All 3 agents operational
- [ ] Live demo succeeds
- [ ] <60s incident resolution
- [ ] Clear traceability shown
- [ ] 0 critical bugs

### Nice to Have

- [ ] Agent Evaluations dashboard
- [ ] Multiple failure scenarios
- [ ] Cost tracking
- [ ] Simple UI

### Placement Goals

- 🎯 Realistic: Top 5
- 🚀 Stretch: Top 3
- 🏆 Ambitious: 1st Place

---

## 💡 Key Reminders for Claude Code

### When You Ask Me to Code:

1. **Be Specific About Files**
   - "Create agents/monitor_agent.py with MonitorAgent class"
   - "Add async check_droplet_health method to MonitorAgent"
2. **Provide Context**

   - "This agent needs to call DigitalOcean MCP server"
   - "Use the BaseAgent class we created earlier"

3. **Ask for Integration Points**

   - "How does this connect to Gradient AI?"
   - "What MCP functions does this need?"

4. **Request Error Handling**

   - "Add try-except for API failures"
   - "Implement retry logic with exponential backoff"

5. **Ask for Tests**
   - "Create test cases for this function"
   - "Add integration test for agent workflow"

### Code Style to Request:

- "Use async/await throughout"
- "Add type hints to all functions"
- "Include docstrings"
- "Follow PEP 8"
- "Use Pydantic for data validation"

### When Behind Schedule:

- "Simplify this to MVP version"
- "Skip the nice-to-have features"
- "Focus on demo-ready code"

---

## 🚨 Emergency Fallback Plans

**If Gradient AI has issues:**

- Use OpenAI API with function calling
- Keep same structure, swap endpoint

**If MCP servers don't work:**

- Use direct API calls to DO and Terraform CLI
- Mention designed for MCP in presentation

**If demo breaks:**

- Play backup video
- Walk through code instead
- Show architecture diagrams

**If completely behind:**

- Build 1 agent (Monitor only)
- 1 failure scenario
- Manual remediation trigger
- Focus on architecture

---

## 📝 Final Pre-Hackathon Checklist

- [ ] DigitalOcean account with credits
- [ ] Gradient AI Platform access
- [ ] All CLIs installed and tested
- [ ] MCP servers tested locally
- [ ] Knowledge base documents prepared
- [ ] Code templates ready
- [ ] .env file template created
- [ ] Demo script memorized
- [ ] Backup video planned
- [ ] Laptop fully charged
- [ ] Charger packed
- [ ] Water + snacks
- [ ] Confident mindset! 💪

---

## 🎉 You Got This!

**Remember:**

- Working demo > Perfect code
- Story matters as much as tech
- Judges are humans, be engaging
- Have backup plans
- Most importantly: Have fun and learn!

**This is ambitious but achievable.** Your DevOps + AI background makes you perfect for this. Trust the process, follow the timeline, and you'll create something impressive.

**Good luck at the hackathon! 🚀🏆**

---

_Document Version: 1.0_  
_Created: December 10, 2025_  
_For: MLH + DigitalOcean AI Hackathon NYC (Dec 12-13, 2025)_
