"""
Project/Workspace Models for Rift
Models for managing user projects and workspaces
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    DIGITALOCEAN = "digitalocean"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ProjectStatus(str, Enum):
    """Status of a project"""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CloudCredentials(BaseModel):
    """Cloud provider credentials"""
    provider: CloudProvider
    credentials: Dict[str, str] = Field(..., description="Provider-specific credentials")
    region: Optional[str] = Field(None, description="Default region")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "digitalocean",
                "credentials": {
                    "api_token": "dop_v1_xxxxx"
                },
                "region": "nyc3"
            }
        }


class Project(BaseModel):
    """User project/workspace"""
    
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    user_id: str = Field(..., description="Owner user ID")
    
    # Cloud configuration
    cloud_providers: List[CloudCredentials] = Field(
        default_factory=list,
        description="Configured cloud providers"
    )
    
    # Infrastructure state
    resources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Provisioned resources"
    )
    
    # Monitoring configuration
    monitoring_enabled: bool = Field(True, description="Enable monitoring")
    auto_remediation: bool = Field(True, description="Enable auto-remediation")
    
    # Metadata
    status: ProjectStatus = Field(ProjectStatus.ACTIVE, description="Project status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list, description="Project tags")
    
    # Statistics
    total_resources: int = Field(0, description="Total resource count")
    active_incidents: int = Field(0, description="Current active incidents")
    total_cost: float = Field(0.0, description="Estimated monthly cost")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj-123",
                "name": "Production Web App",
                "description": "Main production environment",
                "user_id": "user-456",
                "cloud_providers": [
                    {
                        "provider": "digitalocean",
                        "credentials": {"api_token": "dop_v1_xxxxx"},
                        "region": "nyc3"
                    }
                ],
                "monitoring_enabled": True,
                "auto_remediation": True,
                "status": "active"
            }
        }


class CreateProjectRequest(BaseModel):
    """Request to create a new project"""
    
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    user_id: str = Field(..., description="Owner user ID")
    cloud_providers: List[CloudCredentials] = Field(..., description="Cloud providers to configure")
    tags: Optional[List[str]] = Field(default_factory=list)


class UpdateProjectRequest(BaseModel):
    """Request to update project settings"""
    
    name: Optional[str] = None
    description: Optional[str] = None
    monitoring_enabled: Optional[bool] = None
    auto_remediation: Optional[bool] = None
    status: Optional[ProjectStatus] = None
    tags: Optional[List[str]] = None


class InfrastructureNode(BaseModel):
    """Node in infrastructure graph"""
    
    id: str = Field(..., description="Resource ID")
    name: str = Field(..., description="Resource name")
    type: str = Field(..., description="Resource type (droplet, database, etc)")
    provider: CloudProvider = Field(..., description="Cloud provider")
    status: str = Field(..., description="Resource status")
    region: str = Field(..., description="Resource region")
    
    # Visualization data
    x: Optional[float] = Field(None, description="X position in graph")
    y: Optional[float] = Field(None, description="Y position in graph")
    
    # Metadata
    created_at: datetime
    cost_per_month: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)


class InfrastructureEdge(BaseModel):
    """Connection between infrastructure nodes"""
    
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relationship: str = Field(..., description="Relationship type (connects_to, depends_on, etc)")


class InfrastructureGraph(BaseModel):
    """Complete infrastructure topology graph"""
    
    project_id: str
    nodes: List[InfrastructureNode]
    edges: List[InfrastructureEdge]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
