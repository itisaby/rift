"""
Rift - The infrastructure fixer that never sleeps
Autonomous Infrastructure Orchestrator powered by DigitalOcean Gradient AI + MCP

Author: Rift Team
Created for: MLH + DigitalOcean AI Hackathon NYC (December 12-13, 2025)
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime, UTC
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.incident import (
    Incident,
    Diagnosis,
    RemediationResult,
    SystemStatus,
    AgentHealth
)
from models.provision_request import (
    ProvisionRequest,
    ProvisionResult,
    ProvisionTemplate,
    BUILTIN_TEMPLATES
)
from models.project import (
    Project,
    CreateProjectRequest,
    UpdateProjectRequest,
    InfrastructureGraph
)
from utils.config import get_settings
from utils.logger import setup_logging, get_logger

# Import agents and coordinator
from agents.monitor_agent import MonitorAgent
from agents.diagnostic_agent import DiagnosticAgent
from agents.remediation_agent import RemediationAgent
from agents.provisioner_agent import ProvisionerAgent
from agents.safety_validator import SafetyValidator
from mcp_clients.do_mcp import DigitalOceanMCP
from mcp_clients.prometheus_mcp import PrometheusMCP
from mcp_clients.terraform_mcp import TerraformMCP
from orchestrator.coordinator import Coordinator
from services.project_service import ProjectService

# Initialize settings and logging
settings = get_settings()
setup_logging(
    log_level=settings.log_level,
    log_file="logs/rift.log"
)
logger = get_logger(__name__)


# Global state for agents and coordinator
async def initialize_system():
    """Initialize all agents and the coordinator"""
    logger.info("Initializing Rift system...")

    # Initialize MCP clients
    do_mcp = DigitalOceanMCP(api_token=os.getenv("DIGITALOCEAN_API_TOKEN"))
    prometheus_mcp = PrometheusMCP(
        prometheus_url=os.getenv("PROMETHEUS_URL"),
        username=os.getenv("PROMETHEUS_USER"),
        password=os.getenv("PROMETHEUS_PASSWORD")
    )
    terraform_mcp = TerraformMCP(working_dir="/tmp/rift_terraform")

    # Initialize safety validator
    safety_validator = SafetyValidator(
        auto_approve_threshold=float(os.getenv("MAX_COST_AUTO_APPROVE", "50.0"))
    )

    # Initialize agents
    monitor_agent = MonitorAgent(
        agent_endpoint=os.getenv("MONITOR_AGENT_ENDPOINT"),
        agent_key=os.getenv("MONITOR_AGENT_KEY"),
        agent_id=os.getenv("MONITOR_AGENT_ID"),
        do_mcp=do_mcp,
        prometheus_mcp=prometheus_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    diagnostic_agent = DiagnosticAgent(
        agent_endpoint=os.getenv("DIAGNOSTIC_AGENT_ENDPOINT"),
        agent_key=os.getenv("DIAGNOSTIC_AGENT_KEY"),
        agent_id=os.getenv("DIAGNOSTIC_AGENT_ID"),
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp
    )

    remediation_agent = RemediationAgent(
        agent_endpoint=os.getenv("REMEDIATION_AGENT_ENDPOINT"),
        agent_key=os.getenv("REMEDIATION_AGENT_KEY"),
        agent_id=os.getenv("REMEDIATION_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        safety_validator=safety_validator,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    provisioner_agent = ProvisionerAgent(
        agent_endpoint=os.getenv("PROVISIONER_AGENT_ENDPOINT"),
        agent_key=os.getenv("PROVISIONER_AGENT_KEY"),
        agent_id=os.getenv("PROVISIONER_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    # Initialize coordinator
    coordinator = Coordinator(
        monitor_agent=monitor_agent,
        diagnostic_agent=diagnostic_agent,
        remediation_agent=remediation_agent,
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.85")),
        auto_remediation_enabled=os.getenv("AUTO_REMEDIATION_ENABLED", "true").lower() == "true",
        check_interval=30
    )

    # Initialize project service
    project_service = ProjectService(storage_path="./data/projects")

    # Store in app state
    app.state.do_mcp = do_mcp
    app.state.prometheus_mcp = prometheus_mcp
    app.state.terraform_mcp = terraform_mcp
    app.state.monitor_agent = monitor_agent
    app.state.diagnostic_agent = diagnostic_agent
    app.state.remediation_agent = remediation_agent
    app.state.provisioner_agent = provisioner_agent
    app.state.coordinator = coordinator
    app.state.project_service = project_service
    app.state.connection_manager = ConnectionManager()

    logger.info("✓ Rift system initialized successfully")


async def cleanup_system():
    """Cleanup all agents and connections"""
    logger.info("Cleaning up Rift system...")

    if hasattr(app.state, 'monitor_agent'):
        await app.state.monitor_agent.close()
    if hasattr(app.state, 'diagnostic_agent'):
        await app.state.diagnostic_agent.close()
    if hasattr(app.state, 'remediation_agent'):
        await app.state.remediation_agent.close()
    if hasattr(app.state, 'provisioner_agent'):
        await app.state.provisioner_agent.close()
    if hasattr(app.state, 'do_mcp'):
        await app.state.do_mcp.close()
    if hasattr(app.state, 'prometheus_mcp'):
        await app.state.prometheus_mcp.close()
    if hasattr(app.state, 'terraform_mcp'):
        app.state.terraform_mcp.cleanup()

    logger.info("✓ Cleanup complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🤖 Rift starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Demo mode: {settings.demo_mode}")

    # Initialize agents and coordinator
    await initialize_system()

    # Start autonomous monitoring loop if enabled
    if settings.auto_remediation_enabled:
        logger.info("Starting autonomous monitoring loop...")
        app.state.monitoring_task = asyncio.create_task(app.state.coordinator.start_autonomous_loop())

    yield

    logger.info("🤖 Rift shutting down...")

    # Stop autonomous loop
    if hasattr(app.state, 'monitoring_task'):
        await app.state.coordinator.stop_autonomous_loop()
        app.state.monitoring_task.cancel()

    # Cleanup agents
    await cleanup_system()


# Create FastAPI application
app = FastAPI(
    title="Rift API",
    description="The infrastructure fixer that never sleeps - Autonomous Infrastructure Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Health & Status Endpoints
# ============================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Rift",
        "tagline": "The infrastructure fixer that never sleeps",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """
    Get overall system status
    """
    if not hasattr(app.state, 'coordinator'):
        raise HTTPException(status_code=503, detail="System not initialized")

    status_data = app.state.coordinator.get_system_status()

    # Get agent health
    agents = []
    for agent_name in ["monitor", "diagnostic", "remediation"]:
        agent = getattr(app.state, f"{agent_name}_agent", None)
        if agent:
            try:
                health = await agent.check_health()
                agents.append(AgentHealth(
                    agent_name=agent_name,
                    status=health.get("status", "unknown")
                ))
            except Exception:
                agents.append(AgentHealth(agent_name=agent_name, status="unhealthy"))

    return SystemStatus(
        agents=agents,
        active_incidents=status_data["active_incidents"],
        incidents_resolved_today=status_data["stats"]["incidents_resolved"],
        autonomous_mode=status_data["auto_remediation_enabled"]
    )


@app.get("/agents/health")
async def check_agents_health():
    """
    Check health of all AI agents
    """
    if not hasattr(app.state, 'coordinator'):
        raise HTTPException(status_code=503, detail="System not initialized")

    health_results = {}

    # Check Monitor Agent
    if hasattr(app.state, 'monitor_agent'):
        try:
            import time
            start = time.time()
            health = await app.state.monitor_agent.check_health()
            response_time = int((time.time() - start) * 1000)
            health_results["monitor"] = {
                "status": health.get("status", "unknown"),
                "response_time_ms": response_time
            }
        except Exception as e:
            health_results["monitor"] = {"status": "unhealthy", "error": str(e)}

    # Check Diagnostic Agent
    if hasattr(app.state, 'diagnostic_agent'):
        try:
            import time
            start = time.time()
            health = await app.state.diagnostic_agent.check_health()
            response_time = int((time.time() - start) * 1000)
            health_results["diagnostic"] = {
                "status": health.get("status", "unknown"),
                "response_time_ms": response_time
            }
        except Exception as e:
            health_results["diagnostic"] = {"status": "unhealthy", "error": str(e)}

    # Check Remediation Agent
    if hasattr(app.state, 'remediation_agent'):
        try:
            import time
            start = time.time()
            health = await app.state.remediation_agent.check_health()
            response_time = int((time.time() - start) * 1000)
            health_results["remediation"] = {
                "status": health.get("status", "unknown"),
                "response_time_ms": response_time
            }
        except Exception as e:
            health_results["remediation"] = {"status": "unhealthy", "error": str(e)}

    return health_results


# ============================================
# Incident Management Endpoints
# ============================================

@app.post("/incidents/detect", response_model=List[Incident])
async def detect_incidents():
    """
    Trigger incident detection
    Scans all monitored infrastructure for issues
    """
    if not hasattr(app.state, 'monitor_agent'):
        raise HTTPException(status_code=503, detail="Monitor Agent not initialized")

    logger.info("manual_detection_triggered", message="Manual incident detection triggered")

    try:
        incidents = await app.state.monitor_agent.check_all_infrastructure(tag="rift")

        # Broadcast via WebSocket
        await app.state.connection_manager.broadcast({
            "type": "incidents_detected",
            "count": len(incidents),
            "incidents": [inc.dict() for inc in incidents]
        })

        return incidents

    except Exception as e:
        logger.error("detection_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.post("/incidents/diagnose", response_model=Diagnosis)
async def diagnose_incident(incident_id: str):
    """
    Diagnose a specific incident
    Uses RAG to find root cause and recommendations
    """
    if not hasattr(app.state, 'diagnostic_agent'):
        raise HTTPException(status_code=503, detail="Diagnostic Agent not initialized")

    logger.info("manual_diagnosis_triggered", incident_id=incident_id)

    # Find the incident
    incident = app.state.coordinator.active_incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    try:
        diagnosis = await app.state.diagnostic_agent.diagnose_incident(incident)

        # Store diagnosis
        app.state.coordinator.diagnoses[incident_id] = diagnosis

        # Broadcast via WebSocket
        await app.state.connection_manager.broadcast({
            "type": "diagnosis_complete",
            "incident_id": incident_id,
            "diagnosis": diagnosis.dict()
        })

        return diagnosis

    except Exception as e:
        logger.error("diagnosis_failed", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@app.post("/incidents/remediate", response_model=RemediationResult)
async def remediate_incident(incident_id: str, auto_approve: bool = False):
    """
    Execute remediation for an incident
    Optionally auto-approve if within safety thresholds
    """
    if not hasattr(app.state, 'remediation_agent'):
        raise HTTPException(status_code=503, detail="Remediation Agent not initialized")

    logger.info("manual_remediation_triggered", incident_id=incident_id, auto_approve=auto_approve)

    # Find the diagnosis
    diagnosis = app.state.coordinator.diagnoses.get(incident_id)
    if not diagnosis:
        raise HTTPException(status_code=404, detail=f"No diagnosis found for incident {incident_id}")

    try:
        # Generate remediation plan
        plan = await app.state.diagnostic_agent.generate_remediation_plan(diagnosis)

        # Execute remediation
        result = await app.state.remediation_agent.execute_remediation(
            plan=plan,
            auto_approve=auto_approve
        )

        # Store result
        app.state.coordinator.results[incident_id] = result

        # Broadcast via WebSocket
        await app.state.connection_manager.broadcast({
            "type": "remediation_complete",
            "incident_id": incident_id,
            "result": result.dict()
        })

        return result

    except Exception as e:
        logger.error("remediation_failed", incident_id=incident_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Remediation failed: {str(e)}")


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get details of a specific incident"""
    if not hasattr(app.state, 'coordinator'):
        raise HTTPException(status_code=503, detail="System not initialized")

    # Check active incidents
    incident = app.state.coordinator.active_incidents.get(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Get associated diagnosis and result if available
    diagnosis = app.state.coordinator.diagnoses.get(incident_id)
    result = app.state.coordinator.results.get(incident_id)

    response = {
        "incident": incident.dict(),
        "diagnosis": diagnosis.dict() if diagnosis else None,
        "remediation_result": result.dict() if result else None
    }

    return response


@app.get("/incidents")
async def list_incidents(status: str = None, limit: int = 50):
    """List incidents with optional filtering"""
    if not hasattr(app.state, 'coordinator'):
        raise HTTPException(status_code=503, detail="System not initialized")

    # Get all active incidents
    incidents = list(app.state.coordinator.active_incidents.values())

    # Filter by status if provided
    if status:
        from models.incident import IncidentStatus
        try:
            filter_status = IncidentStatus(status)
            incidents = [inc for inc in incidents if inc.status == filter_status]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: {[s.value for s in IncidentStatus]}"
            )

    # Apply limit
    incidents = incidents[:limit]

    # Build response with additional metadata
    response_incidents = []
    for incident in incidents:
        incident_data = {
            "incident": incident.dict(),
            "has_diagnosis": incident.id in app.state.coordinator.diagnoses,
            "has_remediation": incident.id in app.state.coordinator.results
        }
        response_incidents.append(incident_data)

    return {
        "count": len(response_incidents),
        "incidents": response_incidents
    }

# ============================================
# Provisioning Endpoints
# ============================================

@app.post("/provision/create", response_model=ProvisionResult)
async def provision_infrastructure(request: ProvisionRequest, project_id: str = None):
    """
    Provision new infrastructure based on natural language request or template.

    This endpoint creates new infrastructure resources (droplets, databases, etc.)
    based on a user's description or a pre-built template.
    
    Args:
        request: ProvisionRequest with infrastructure requirements
        project_id: Optional project ID to associate resources with
    """
    if not hasattr(app.state, 'provisioner_agent'):
        raise HTTPException(status_code=503, detail="Provisioner Agent not initialized")

    logger.info("provision_request_received", request_id=request.request_id,
                description=request.description, project_id=project_id)

    try:
        # Broadcast start event
        await app.state.connection_manager.broadcast({
            "type": "provision_started",
            "request_id": request.request_id,
            "description": request.description,
            "template": request.template,
            "project_id": project_id
        })

        # Execute provisioning
        result = await app.state.provisioner_agent.provision(request)

        # If provisioning succeeded and project_id provided, add resources to project
        if result.success and project_id and hasattr(app.state, 'project_service'):
            for resource in result.resources_created or []:
                resource_data = {
                    "id": resource.get("id"),
                    "name": resource.get("name"),
                    "type": resource.get("type", "unknown"),
                    "provider": "digitalocean",
                    "status": "active",
                    "region": request.region or "nyc3",
                    "cost_per_month": result.cost_estimate / len(result.resources_created) if result.resources_created else 0,
                    "created_at": resource.get("created_at"),
                    "tags": request.tags or [],
                    "dependencies": resource.get("dependencies", [])
                }
                await app.state.project_service.add_resource(project_id, resource_data)
            
            # Update project stats
            await app.state.project_service.update_project_stats(project_id)
            
            logger.info("resources_added_to_project", project_id=project_id,
                       resource_count=len(result.resources_created or []))

        # Broadcast completion event
        if result.success:
            await app.state.connection_manager.broadcast({
                "type": "provision_complete",
                "request_id": request.request_id,
                "project_id": project_id,
                "resources": result.resources_created,
                "cost": result.cost_estimate,
                "access_info": result.access_info
            })
        else:
            await app.state.connection_manager.broadcast({
                "type": "provision_failed",
                "request_id": request.request_id,
                "error": result.error
            })

        return result

    except Exception as e:
        logger.error("provision_failed", request_id=request.request_id, error=str(e))
        await app.state.connection_manager.broadcast({
            "type": "provision_failed",
            "request_id": request.request_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")


@app.get("/provision/templates", response_model=List[ProvisionTemplate])
async def list_templates():
    """
    Get list of available provisioning templates.

    Templates are pre-configured infrastructure patterns that can be
    quickly deployed with minimal parameters.
    """
    if not hasattr(app.state, 'provisioner_agent'):
        raise HTTPException(status_code=503, detail="Provisioner Agent not initialized")

    templates = app.state.provisioner_agent.get_templates()
    return templates


@app.get("/provision/templates/{template_id}", response_model=ProvisionTemplate)
async def get_template(template_id: str):
    """Get details of a specific provisioning template."""
    if not hasattr(app.state, 'provisioner_agent'):
        raise HTTPException(status_code=503, detail="Provisioner Agent not initialized")

    template = app.state.provisioner_agent.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    return template


@app.post("/provision/template/{template_id}", response_model=ProvisionResult)
async def provision_from_template(
    template_id: str,
    user_id: str,
    params: dict = None
):
    """
    Provision infrastructure from a pre-built template.

    This is a convenience endpoint that creates a ProvisionRequest
    from a template and executes it.
    """
    if not hasattr(app.state, 'provisioner_agent'):
        raise HTTPException(status_code=503, detail="Provisioner Agent not initialized")

    # Get template to validate it exists
    template = app.state.provisioner_agent.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    # Create provision request from template
    request = ProvisionRequest(
        user_id=user_id,
        description=template.description,
        template=template_id,
        template_params=params or {}
    )

    logger.info("template_provision_request", template_id=template_id,
                request_id=request.request_id)

    try:
        # Execute provisioning
        result = await app.state.provisioner_agent.provision(request)

        # Broadcast events
        if result.success:
            await app.state.connection_manager.broadcast({
                "type": "provision_complete",
                "request_id": request.request_id,
                "template": template_id,
                "resources": result.resources_created
            })

        return result

    except Exception as e:
        logger.error("template_provision_failed", template_id=template_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")


# ============================================
# WebSocket for Real-time Updates
# ============================================

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")


manager = ConnectionManager()


# ============================================
# Project/Workspace Management Endpoints
# ============================================

@app.post("/projects", response_model=Project)
async def create_project(request: CreateProjectRequest):
    """Create a new project/workspace"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    try:
        project = await app.state.project_service.create_project(request)
        return project
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects", response_model=List[Project])
async def list_projects(user_id: str = None):
    """List all projects, optionally filtered by user"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    try:
        projects = await app.state.project_service.list_projects(user_id=user_id)
        return projects
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    project = await app.state.project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@app.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update project settings"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    project = await app.state.project_service.update_project(project_id, request)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    success = await app.state.project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}


@app.post("/projects/{project_id}/sync-resources")
async def sync_project_resources(project_id: str):
    """Sync resources from cloud provider to project"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    if not hasattr(app.state, 'do_mcp'):
        raise HTTPException(status_code=503, detail="DigitalOcean MCP not initialized")
    
    try:
        project = await app.state.project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Find droplets with project tags
        project_tags = project.tags + ["frontend-provisioned"]  # Include common tags
        droplets = []
        
        for tag in project_tags:
            try:
                tagged_droplets = await app.state.do_mcp.list_droplets(tag=tag)
                droplets.extend(tagged_droplets)
            except:
                pass
        
        # Remove duplicates
        seen_ids = set()
        unique_droplets = []
        for droplet in droplets:
            droplet_id = droplet.get("id")
            if droplet_id and droplet_id not in seen_ids:
                seen_ids.add(droplet_id)
                unique_droplets.append(droplet)
        
        # Clear existing resources and add synced ones
        project.resources = []
        
        for droplet in unique_droplets:
            networks = droplet.get("networks", {}).get("v4", [])
            public_ip = None
            for network in networks:
                if network.get("type") == "public":
                    public_ip = network.get("ip_address")
                    break
            
            resource_data = {
                "id": str(droplet.get("id")),
                "name": droplet.get("name"),
                "type": "droplet",
                "provider": "digitalocean",
                "status": droplet.get("status", "active"),
                "region": droplet.get("region", {}).get("slug", "unknown"),
                "cost_per_month": 0,  # Could calculate from size
                "created_at": droplet.get("created_at"),
                "tags": droplet.get("tags", []),
                "dependencies": [],
                "ipv4_address": public_ip
            }
            await app.state.project_service.add_resource(project_id, resource_data)
        
        await app.state.project_service.update_project_stats(project_id)
        
        logger.info("resources_synced", project_id=project_id, count=len(unique_droplets))
        
        return {
            "message": f"Synced {len(unique_droplets)} resource(s)",
            "resources": unique_droplets
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync resources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@app.get("/projects/{project_id}/infrastructure", response_model=InfrastructureGraph)
async def get_infrastructure_graph(project_id: str):
    """Get infrastructure topology graph for visualization"""
    if not hasattr(app.state, 'project_service'):
        raise HTTPException(status_code=503, detail="Project service not initialized")
    
    graph = await app.state.project_service.get_infrastructure_graph(project_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return graph


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming
    Sends incident updates, agent status, etc.
    """
    connection_manager = app.state.connection_manager if hasattr(app.state, 'connection_manager') else manager
    await connection_manager.connect(websocket)
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connection established",
            "timestamp": datetime.now(UTC).isoformat()
        })

        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo for now
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


# ============================================
# Demo & Testing Endpoints
# ============================================

@app.post("/demo/inject-failure")
async def inject_failure(
    failure_type: str,
    target: str,
    duration: int = 300
):
    """
    Demo endpoint: Inject a failure for testing

    Creates a simulated incident for demonstration purposes
    """
    if not settings.demo_mode:
        raise HTTPException(
            status_code=403,
            detail="Demo mode is disabled"
        )

    logger.info(f"Injecting {failure_type} failure on {target} for {duration}s")

    # Create a simulated incident based on failure type
    from models.incident import Incident, MetricType, ResourceType, SeverityLevel
    import uuid
    from datetime import datetime, UTC

    # Map failure types to metrics
    failure_metric_map = {
        "cpu": MetricType.CPU_USAGE,
        "memory": MetricType.MEMORY_USAGE,
        "disk": MetricType.DISK_USAGE,
        "network": MetricType.NETWORK_IN,
        "error": MetricType.ERROR_RATE,
        "latency": MetricType.RESPONSE_TIME
    }

    # Map failure types to simulated values
    failure_values = {
        "cpu": (95.0, 80.0),  # (current, threshold)
        "memory": (92.0, 85.0),
        "disk": (94.0, 90.0),
        "network": (1000000.0, 500000.0),
        "error": (15.0, 5.0),
        "latency": (5000.0, 1000.0)
    }

    metric = failure_metric_map.get(failure_type.lower(), MetricType.CPU_USAGE)
    current_value, threshold = failure_values.get(failure_type.lower(), (95.0, 80.0))

    # Create simulated incident
    incident = Incident(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(UTC),
        resource_id=f"demo-{target}",
        resource_name=target,
        resource_type=ResourceType.DROPLET,
        metric=metric,
        current_value=current_value,
        threshold_value=threshold,
        severity=SeverityLevel.HIGH,
        status="DETECTED",
        description=f"Demo {failure_type} failure injected on {target}",
        metadata={
            "demo": True,
            "injected_at": datetime.now(UTC).isoformat(),
            "duration": duration,
            "failure_type": failure_type
        }
    )

    # Add to coordinator's incident tracking
    if coordinator:
        coordinator.active_incidents[incident.id] = incident
        coordinator.statistics["total_incidents"] += 1

        # Broadcast via WebSocket
        await connection_manager.broadcast({
            "type": "incident_detected",
            "incident": {
                "id": incident.id,
                "resource_name": incident.resource_name,
                "metric": incident.metric,
                "severity": incident.severity,
                "timestamp": incident.timestamp.isoformat()
            }
        })

    return {
        "success": True,
        "message": f"Injected {failure_type} failure on {target}",
        "incident_id": incident.id,
        "duration": duration,
        "incident": {
            "id": incident.id,
            "resource_name": incident.resource_name,
            "metric": incident.metric,
            "current_value": incident.current_value,
            "threshold_value": incident.threshold_value,
            "severity": incident.severity,
            "status": incident.status
        }
    }


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


# ============================================
# Startup
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
