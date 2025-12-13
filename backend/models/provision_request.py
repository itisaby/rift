"""
Provision Request Models for Rift
Models for infrastructure provisioning requests and results
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class ProvisionStatus(str, Enum):
    """Status of a provisioning request"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    APPLYING = "applying"
    COMPLETED = "completed"
    FAILED = "failed"


class ProvisionRequest(BaseModel):
    """User request for infrastructure provisioning."""

    request_id: str = Field(default_factory=lambda: f"prov-{datetime.utcnow().timestamp()}", description="Unique request ID")
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
    tags: List[str] = Field(default_factory=list, description="Tags to apply to resources")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "description": "Create a web server with PostgreSQL database",
                "region": "nyc3",
                "environment": "production",
                "budget_limit": 50.0,
                "tags": ["web-app", "production"]
            }
        }


class ProvisionResult(BaseModel):
    """Result of provisioning operation."""

    request_id: str = Field(..., description="Original request ID")
    status: ProvisionStatus = Field(..., description="Provisioning status")
    success: bool = Field(..., description="Whether provisioning succeeded")

    # Success fields
    resources_created: Optional[List[Dict[str, Any]]] = Field(None, description="List of created resources")
    access_info: Optional[Dict[str, str]] = Field(None, description="Access URLs, IPs, credentials")
    cost_estimate: Optional[float] = Field(None, description="Estimated monthly cost")
    terraform_config: Optional[str] = Field(None, description="Generated Terraform configuration")
    terraform_outputs: Optional[Dict[str, Any]] = Field(None, description="Terraform output values")

    # Error fields
    error: Optional[str] = Field(None, description="Error message if failed")
    validation_errors: Optional[List[str]] = Field(None, description="Validation errors")

    # Execution details
    logs: List[str] = Field(default_factory=list, description="Execution logs")

    # Metadata
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = Field(None, description="Total execution time")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "prov-1234567890",
                "status": "completed",
                "success": True,
                "resources_created": [
                    {"type": "droplet", "id": "123456", "name": "web-server-1"}
                ],
                "access_info": {
                    "ssh": "ssh root@192.168.1.1",
                    "url": "http://192.168.1.1"
                },
                "cost_estimate": 12.0,
                "duration_seconds": 45.3
            }
        }


class ProvisionTemplate(BaseModel):
    """Pre-built infrastructure template."""

    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="What this template creates")
    terraform_module: str = Field(..., description="Path to Terraform module")

    # Parameters
    required_params: List[str] = Field(default_factory=list, description="Required parameters")
    optional_params: Dict[str, Any] = Field(default_factory=dict, description="Optional parameters with defaults")

    # Cost and resources
    estimated_cost: float = Field(..., description="Base monthly cost (USD)")
    resources: List[str] = Field(default_factory=list, description="List of resources created")

    # Metadata
    category: str = Field("general", description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "simple-droplet",
                "name": "Simple Droplet",
                "description": "Single Ubuntu droplet with basic firewall",
                "terraform_module": "modules/droplet",
                "required_params": ["droplet_name"],
                "optional_params": {"size": "s-1vcpu-1gb", "region": "nyc3"},
                "estimated_cost": 6.0,
                "resources": ["droplet", "firewall"],
                "category": "compute",
                "tags": ["basic", "droplet"]
            }
        }


# Pre-defined templates
BUILTIN_TEMPLATES = [
    ProvisionTemplate(
        id="simple-droplet",
        name="Simple Droplet",
        description="Single Ubuntu droplet with basic firewall (HTTP, HTTPS, SSH)",
        terraform_module="modules/droplet",
        required_params=["droplet_name"],
        optional_params={
            "size": "s-1vcpu-1gb",
            "region": "nyc3",
            "image": "ubuntu-22-04-x64",
            "environment": "development"
        },
        estimated_cost=6.0,
        resources=["droplet", "firewall"],
        category="compute",
        tags=["basic", "droplet", "web"]
    ),
    ProvisionTemplate(
        id="postgres-db",
        name="PostgreSQL Database",
        description="Managed PostgreSQL database cluster with automated backups",
        terraform_module="modules/database",
        required_params=["db_name"],
        optional_params={
            "engine": "pg",
            "engine_version": "15",
            "size": "db-s-1vcpu-1gb",
            "region": "nyc3",
            "node_count": 1
        },
        estimated_cost=15.0,
        resources=["database_cluster", "database_firewall"],
        category="database",
        tags=["postgresql", "database", "managed"]
    ),
    ProvisionTemplate(
        id="web-stack",
        name="Complete Web Stack",
        description="Load balancer + 2 app servers + PostgreSQL database for production web apps",
        terraform_module="modules/web_stack",
        required_params=["stack_name"],
        optional_params={
            "app_server_count": 2,
            "app_server_size": "s-2vcpu-4gb",
            "db_size": "db-s-1vcpu-1gb",
            "region": "nyc3"
        },
        estimated_cost=45.0,
        resources=["load_balancer", "droplets", "database_cluster", "firewalls"],
        category="stack",
        tags=["production", "web-app", "full-stack"]
    ),
    ProvisionTemplate(
        id="redis-cache",
        name="Redis Cache",
        description="Managed Redis cluster for caching and session storage",
        terraform_module="modules/database",
        required_params=["db_name"],
        optional_params={
            "engine": "redis",
            "engine_version": "7",
            "size": "db-s-1vcpu-1gb",
            "region": "nyc3",
            "node_count": 1
        },
        estimated_cost=15.0,
        resources=["redis_cluster", "database_firewall"],
        category="database",
        tags=["redis", "cache", "managed"]
    ),
    ProvisionTemplate(
        id="kubernetes-cluster",
        name="Kubernetes Cluster",
        description="Managed Kubernetes cluster with auto-scaling node pools",
        terraform_module="modules/kubernetes",
        required_params=["cluster_name"],
        optional_params={
            "region": "nyc3",
            "node_size": "s-2vcpu-4gb",
            "node_count": 3,
            "auto_scale": True,
            "min_nodes": 1,
            "max_nodes": 5
        },
        estimated_cost=36.0,
        resources=["kubernetes_cluster", "node_pool"],
        category="kubernetes",
        tags=["kubernetes", "k8s", "container", "orchestration"]
    )
]
