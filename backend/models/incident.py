"""
Rift Data Models
Defines the core data structures for incidents, diagnoses, and remediations
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident lifecycle status"""
    DETECTED = "detected"
    DIAGNOSING = "diagnosing"
    DIAGNOSED = "diagnosed"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"
    FAILED = "failed"


class MetricType(str, Enum):
    """Types of monitored metrics"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IN = "network_in"
    NETWORK_OUT = "network_out"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"


class ResourceType(str, Enum):
    """Infrastructure resource types"""
    DROPLET = "droplet"
    DATABASE = "database"
    KUBERNETES = "kubernetes"
    LOAD_BALANCER = "load_balancer"
    SPACE = "space"
    FIREWALL = "firewall"


class Incident(BaseModel):
    """
    Represents a detected infrastructure incident
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resource_id: str = Field(..., description="ID of the affected resource")
    resource_name: str = Field(..., description="Name of the affected resource")
    resource_type: ResourceType
    metric: MetricType
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold that was exceeded")
    severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.DETECTED
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "inc-12345",
                "timestamp": "2025-12-10T14:30:00Z",
                "resource_id": "droplet-67890",
                "resource_name": "web-app",
                "resource_type": "droplet",
                "metric": "cpu_usage",
                "current_value": 95.5,
                "threshold_value": 80.0,
                "severity": "high",
                "status": "detected",
                "description": "CPU usage exceeded threshold on web-app droplet"
            }
        }


class KnowledgeEntry(BaseModel):
    """RAG knowledge base entry"""
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """
    Represents the diagnostic analysis of an incident
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    root_cause: str = Field(..., description="Identified root cause")
    root_cause_category: str = Field(..., description="Category of root cause")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="AI reasoning for diagnosis")
    knowledge_base_matches: List[KnowledgeEntry] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    estimated_cost: Optional[float] = Field(None, description="Estimated remediation cost in USD")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "diag-12345",
                "incident_id": "inc-12345",
                "timestamp": "2025-12-10T14:30:30Z",
                "root_cause": "Undersized droplet for current workload",
                "root_cause_category": "capacity",
                "confidence": 0.89,
                "reasoning": "CPU consistently above 90% with no memory pressure. Current droplet size s-1vcpu-1gb insufficient for traffic patterns.",
                "recommendations": ["Scale up to s-2vcpu-2gb", "Enable auto-scaling"],
                "estimated_cost": 12.0,
                "estimated_duration": 90
            }
        }


class RemediationAction(str, Enum):
    """Types of remediation actions"""
    RESIZE_DROPLET = "resize_droplet"
    ADD_VOLUME = "add_volume"
    RESTART_SERVICE = "restart_service"
    UPDATE_FIREWALL = "update_firewall"
    CLEAN_DISK = "clean_disk"
    SCALE_KUBERNETES = "scale_kubernetes"
    UPDATE_LOAD_BALANCER = "update_load_balancer"


class RemediationPlan(BaseModel):
    """
    Represents a planned remediation
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    diagnosis_id: str
    incident_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: RemediationAction
    action_description: str
    terraform_config: Optional[str] = Field(None, description="Terraform configuration if applicable")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    safety_checks: List[str] = Field(default_factory=list)
    rollback_plan: Optional[Dict[str, Any]] = Field(None)
    requires_approval: bool = False
    estimated_cost: Optional[float] = None
    estimated_duration: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "plan-12345",
                "diagnosis_id": "diag-12345",
                "incident_id": "inc-12345",
                "action": "resize_droplet",
                "action_description": "Resize web-app droplet from s-1vcpu-1gb to s-2vcpu-2gb",
                "parameters": {
                    "droplet_id": "droplet-67890",
                    "current_size": "s-1vcpu-1gb",
                    "new_size": "s-2vcpu-2gb"
                },
                "requires_approval": False,
                "estimated_cost": 12.0
            }
        }


class RemediationStatus(str, Enum):
    """Remediation execution status"""
    PENDING = "pending"
    VALIDATING = "validating"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RemediationResult(BaseModel):
    """
    Represents the result of a remediation execution
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    incident_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: RemediationStatus
    success: bool
    action_taken: str
    duration: int = Field(..., description="Duration in seconds")
    actual_cost: Optional[float] = Field(None, description="Actual cost in USD")
    verification_passed: bool = False
    error_message: Optional[str] = None
    rollback_executed: bool = False
    logs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "result-12345",
                "plan_id": "plan-12345",
                "incident_id": "inc-12345",
                "status": "success",
                "success": True,
                "action_taken": "Resized droplet web-app to s-2vcpu-2gb",
                "duration": 90,
                "actual_cost": 0.02,
                "verification_passed": True
            }
        }


class AgentHealth(BaseModel):
    """Health status of an AI agent"""
    agent_name: str
    status: str  # "healthy", "degraded", "down"
    last_check: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class SystemStatus(BaseModel):
    """Overall system status"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agents: List[AgentHealth]
    active_incidents: int
    incidents_resolved_today: int
    average_resolution_time: Optional[float] = None
    total_cost_today: Optional[float] = None
    autonomous_mode: bool
