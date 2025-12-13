# 🤖 Rift Backend

**The infrastructure fixer that never sleeps**

Autonomous Infrastructure Orchestrator powered by DigitalOcean Gradient AI + MCP

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env

# Required variables:
# - DIGITALOCEAN_API_TOKEN
# - MONITOR_AGENT_ENDPOINT, MONITOR_AGENT_KEY, MONITOR_AGENT_ID
# - DIAGNOSTIC_AGENT_ENDPOINT, DIAGNOSTIC_AGENT_KEY, DIAGNOSTIC_AGENT_ID
# - REMEDIATION_AGENT_ENDPOINT, REMEDIATION_AGENT_KEY, REMEDIATION_AGENT_ID
# - KNOWLEDGE_BASE_ID
# - API_SECRET_KEY
```

### 3. Set Up Infrastructure

See [SETUP.md](SETUP.md) for detailed infrastructure setup instructions.

### 4. Run the Application

```bash
# Development mode (auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
backend/
├── agents/              # AI agent implementations
│   ├── base_agent.py   # Base class for all agents
│   ├── monitor_agent.py      # Phase 2
│   ├── diagnostic_agent.py   # Phase 3
│   └── remediation_agent.py  # Phase 4
│
├── mcp_clients/        # MCP server clients
│   ├── do_mcp.py      # DigitalOcean MCP
│   ├── terraform_mcp.py     # Terraform MCP
│   └── prometheus_mcp.py    # Prometheus MCP
│
├── orchestrator/       # Agent coordination
│   └── coordinator.py  # Main orchestration logic
│
├── models/            # Data models
│   └── incident.py    # Incident, Diagnosis, Remediation models
│
├── utils/             # Utilities
│   ├── config.py      # Configuration management
│   └── logger.py      # Structured logging
│
├── terraform/         # Infrastructure as Code
│   ├── main.tf
│   └── modules/      # Terraform modules
│
├── demo/             # Demo scripts
│   └── failure_injection.py
│
├── tests/            # Test suite
│   ├── test_monitor.py
│   ├── test_diagnostic.py
│   └── agent_evaluations.py
│
├── knowledge-base/   # RAG knowledge base
│   ├── do-docs.md
│   ├── runbooks.md
│   └── past-incidents.json
│
├── logs/            # Application logs
│
├── main.py          # FastAPI application
├── requirements.txt
├── .env
└── README.md
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      FastAPI Application            │
│      (Orchestrator Layer)           │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
   ┌───▼────┐   ┌─────▼─────┐   ┌─────────▼────┐
   │Monitor │   │Diagnostic │   │Remediation   │
   │ Agent  │──▶│  Agent    │──▶│   Agent      │
   └───┬────┘   └─────┬─────┘   └──────┬───────┘
       │              │                 │
       │              │                 │
   ┌───▼──────────────▼─────────────────▼───┐
   │   DigitalOcean Gradient AI Platform    │
   │         (with RAG Knowledge Base)      │
   └───┬──────────────┬─────────────────┬───┘
       │              │                 │
   ┌───▼────┐   ┌─────▼─────┐   ┌─────▼──────┐
   │DO MCP  │   │Terraform  │   │Prometheus  │
   │Server  │   │   MCP     │   │    MCP     │
   └───┬────┘   └─────┬─────┘   └─────┬──────┘
       │              │                │
   ┌───▼──────────────▼────────────────▼───┐
   │   DigitalOcean Infrastructure         │
   │   (Droplets, Spaces, Monitoring)      │
   └────────────────────────────────────────┘
```

---

## 🎯 Implementation Phases

### ✅ Phase 1: Foundation (CURRENT)
- [x] Project structure
- [x] Environment configuration
- [x] Data models
- [x] Logging utilities
- [x] FastAPI skeleton
- [ ] Infrastructure setup (see SETUP.md)

### 🚧 Phase 2: Monitor Agent
- [ ] Base agent class
- [ ] DigitalOcean MCP client
- [ ] Prometheus MCP client
- [ ] Monitor agent implementation
- [ ] Incident detection

### 🔜 Phase 3: Diagnostic Agent
- [ ] Terraform MCP client
- [ ] Knowledge base setup
- [ ] Diagnostic agent implementation
- [ ] RAG integration
- [ ] Confidence scoring

### 🔜 Phase 4: Remediation Agent
- [ ] Terraform modules
- [ ] Safety validator
- [ ] Remediation agent implementation
- [ ] Rollback capability

### 🔜 Phase 5: Orchestrator
- [ ] Agent coordinator
- [ ] WebSocket streaming
- [ ] Autonomous loop

### 🔜 Phase 6: Testing
- [ ] Agent evaluations
- [ ] Integration tests
- [ ] Performance tests

### 🔜 Phase 7: Demo
- [ ] Failure injection scripts
- [ ] Dashboard (optional)
- [ ] Demo script

---

## 🔌 API Endpoints

### Health & Status
- `GET /` - API root
- `GET /health` - Health check
- `GET /status` - System status
- `GET /agents/health` - Agent health

### Incident Management
- `POST /incidents/detect` - Trigger incident detection
- `POST /incidents/diagnose` - Diagnose incident
- `POST /incidents/remediate` - Execute remediation
- `GET /incidents/{id}` - Get incident details
- `GET /incidents` - List incidents

### Real-time
- `WS /ws/events` - WebSocket event stream

### Demo (if demo_mode=true)
- `POST /demo/inject-failure` - Inject test failures

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_monitor.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run agent evaluations
python tests/agent_evaluations.py
```

---

## 📊 Monitoring

### Application Logs
```bash
# Tail logs
tail -f logs/rift.log

# View structured logs
cat logs/rift.log | jq
```

### Metrics
- Prometheus: `http://<control-plane-ip>:9090`
- Application metrics: `http://localhost:8000/metrics`

---

## 🛠️ Development

### Code Style
```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

### Adding a New Agent
1. Create agent class in `agents/`
2. Inherit from `BaseAgent`
3. Implement required methods
4. Add agent to coordinator
5. Update environment config
6. Write tests

### Adding an MCP Client
1. Create client in `mcp_clients/`
2. Implement connection handling
3. Define function wrappers
4. Add error handling
5. Write tests

---

## 🔒 Security

- API authentication via `API_SECRET_KEY`
- CORS configured for frontend origins
- Environment variables for all secrets
- Safety checks for destructive operations
- Cost limits for auto-approval
- Terraform state encryption
- Audit logging for all changes

---

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**"Cannot connect to agent" errors**
```bash
# Check agent endpoints in .env
# Verify Gradient AI agents are running
# Test with curl
```

**Prometheus not accessible**
```bash
# Check firewall rules
# Verify Prometheus is running
# Check prometheus.yml configuration
```

See [SETUP.md](SETUP.md) for detailed troubleshooting.

---

## 📝 Environment Variables

See `.env` file for all configuration options. Key variables:

- `DIGITALOCEAN_API_TOKEN` - DO API token
- `MONITOR_AGENT_*` - Monitor agent configuration
- `DIAGNOSTIC_AGENT_*` - Diagnostic agent configuration
- `REMEDIATION_AGENT_*` - Remediation agent configuration
- `KNOWLEDGE_BASE_ID` - RAG knowledge base ID
- `PROMETHEUS_URL` - Prometheus endpoint
- `AUTO_REMEDIATION_ENABLED` - Enable autonomous fixes
- `CONFIDENCE_THRESHOLD` - Min confidence for auto-remediation
- `MAX_COST_AUTO_APPROVE` - Max cost for auto-approval

---

## 🎯 Hackathon Timeline

- **Hour 0-2**: ✅ Phase 1 - Foundation
- **Hour 2-4**: Phase 2 - Monitor Agent
- **Hour 4-8**: Phase 3 - Diagnostic Agent
- **Hour 8-12**: Phase 4 - Remediation Agent
- **Hour 12-16**: Phase 5 - Orchestrator
- **Hour 16-18**: Phase 6 - Testing
- **Hour 18-22**: Phase 7 - Demo Prep
- **Hour 22-24**: Buffer & Polish

---

## 📚 Resources

- [DigitalOcean API Docs](https://docs.digitalocean.com/reference/api/)
- [Gradient AI Platform](https://cloud.digitalocean.com/ai)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Terraform Documentation](https://www.terraform.io/docs)

---

## 🏆 Project Info

**Project Name:** Rift
**Tagline:** The infrastructure fixer that never sleeps
**Hackathon:** MLH + DigitalOcean AI Hackathon NYC
**Dates:** December 12-13, 2025
**Tech Stack:** Python, FastAPI, DigitalOcean Gradient AI, MCP, Terraform

---

## 📄 License

Built for MLH + DigitalOcean AI Hackathon 2025

---

**Let's build something amazing! 🚀**
