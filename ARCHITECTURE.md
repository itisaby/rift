# RIFT Platform Architecture

```mermaid
graph TB
    subgraph "User Interface"
        Frontend[Frontend - Next.js<br/>localhost:3000]
    end

    subgraph "Backend - FastAPI"
        API[API Server<br/>localhost:8000]
        Orchestrator[Orchestrator<br/>Project Coordinator]
        
        subgraph "AI Agents"
            Monitor[Monitor Agent<br/>30s checks]
            Diagnostic[Diagnostic Agent<br/>Root cause analysis]
            Remediation[Remediation Agent<br/>SSH execution]
            Provisioner[Provisioner Agent<br/>Terraform generation]
        end
        
        subgraph "MCP Clients"
            DOMCP[DigitalOcean MCP<br/>Droplet management]
            PromMCP[Prometheus MCP<br/>Metrics queries]
            TerraformMCP[Terraform MCP<br/>IaC execution]
        end
    end

    subgraph "Cloud Infrastructure - DigitalOcean"
        ControlPlane[Control Plane<br/>104.236.4.131<br/>Prometheus Server]
        WebApp[web-app<br/>134.209.37.250<br/>Node Exporter]
        APIServer[api-server<br/>174.138.62.125<br/>Node Exporter]
        Arnab[Arnab<br/>45.55.34.170<br/>Node Exporter]
    end

    subgraph "Monitoring Stack"
        Prometheus[Prometheus<br/>:9090<br/>Metrics storage]
        NodeExporter1[Node Exporter<br/>:9100]
        NodeExporter2[Node Exporter<br/>:9100]
        NodeExporter3[Node Exporter<br/>:9100]
    end

    subgraph "AI Models"
        Gradient[Gradient AI<br/>deepseek-r1<br/>Code generation]
    end

    subgraph "Automation"
        CloudInit[Cloud-Init<br/>Auto-install Node Exporter]
        SSHKey[SSH Key Distribution<br/>id_ed25519_do_rift]
        PrometheusReg[Prometheus Registration<br/>Auto-add targets]
    end

    %% User Flow
    Frontend -->|HTTP| API
    API --> Orchestrator
    
    %% Orchestrator to Agents
    Orchestrator --> Monitor
    Orchestrator --> Diagnostic
    Orchestrator --> Remediation
    Orchestrator --> Provisioner
    
    %% Agent to MCP
    Monitor --> PromMCP
    Monitor --> DOMCP
    Diagnostic --> PromMCP
    Remediation -->|SSH Commands| DOMCP
    Provisioner --> TerraformMCP
    Provisioner --> DOMCP
    
    %% MCP to Infrastructure
    DOMCP -->|API| WebApp
    DOMCP -->|API| APIServer
    DOMCP -->|API| Arnab
    PromMCP -->|HTTP| Prometheus
    TerraformMCP -->|Provision| ControlPlane
    
    %% Monitoring Flow
    Prometheus -->|Scrape| NodeExporter1
    Prometheus -->|Scrape| NodeExporter2
    Prometheus -->|Scrape| NodeExporter3
    NodeExporter1 -.->|Metrics| WebApp
    NodeExporter2 -.->|Metrics| APIServer
    NodeExporter3 -.->|Metrics| Arnab
    ControlPlane -->|Hosts| Prometheus
    
    %% AI Integration
    Provisioner -->|Generate IaC| Gradient
    Diagnostic -->|Analyze| Gradient
    Remediation -->|Generate Fix| Gradient
    
    %% Automation Flow
    Provisioner -.->|Inject| CloudInit
    Provisioner -.->|Inject| SSHKey
    Provisioner -.->|Trigger| PrometheusReg
    CloudInit -.->|Install| NodeExporter1
    CloudInit -.->|Install| NodeExporter2
    CloudInit -.->|Install| NodeExporter3
    PrometheusReg -.->|Add Target| Prometheus
    SSHKey -.->|Authorize| WebApp
    SSHKey -.->|Authorize| APIServer
    SSHKey -.->|Authorize| Arnab

    %% Incident Flow
    Monitor -->|Detect Issue| Orchestrator
    Orchestrator -->|Diagnose| Diagnostic
    Diagnostic -->|Create Plan| Remediation
    Remediation -->|Execute Fix| WebApp
    Remediation -->|Execute Fix| APIServer
    Remediation -->|Execute Fix| Arnab

    style Frontend fill:#e1f5ff
    style API fill:#fff4e1
    style Monitor fill:#ffe1e1
    style Diagnostic fill:#ffe1e1
    style Remediation fill:#ffe1e1
    style Provisioner fill:#ffe1e1
    style Prometheus fill:#e1ffe1
    style Gradient fill:#f0e1ff
    style CloudInit fill:#ffffcc
    style SSHKey fill:#ffffcc
    style PrometheusReg fill:#ffffcc
```

## Flow Explanation

### 1. **Provisioning Flow** (New VM Creation)
```
User → Frontend → API → Provisioner Agent → Gradient AI (Generate Terraform)
→ Terraform MCP → DigitalOcean API → New Droplet Created
→ Cloud-Init installs Node Exporter
→ SSH Key injected automatically
→ Prometheus Registration adds monitoring target
```

### 2. **Monitoring Flow** (Continuous)
```
Monitor Agent (every 30s) → PromMCP → Prometheus → Query Metrics
→ Check CPU/Memory/Disk for all droplets
→ If threshold exceeded → Trigger Incident
```

### 3. **Remediation Flow** (Autonomous)
```
Incident Detected → Diagnostic Agent → Analyze root cause via Prometheus
→ Remediation Agent → Generate fix commands via Gradient AI
→ Execute SSH commands on affected droplet
→ Verify recovery → Close incident
```

### 4. **Architecture Highlights**
- **Zero-Touch Provisioning**: New VMs automatically get monitoring + SSH access
- **Autonomous Healing**: Incidents detected and fixed without human intervention
- **Multi-Cloud Ready**: MCP pattern allows easy cloud provider abstraction
- **AI-Powered**: Gradient AI generates Terraform code and remediation commands
