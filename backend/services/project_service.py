"""
Project Management Service
Handles project/workspace operations and multi-cloud coordination
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

from models.project import (
    Project,
    CreateProjectRequest,
    UpdateProjectRequest,
    CloudProvider,
    ProjectStatus,
    InfrastructureGraph,
    InfrastructureNode,
    InfrastructureEdge
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ProjectService:
    """Service for managing projects and workspaces"""
    
    def __init__(self, storage_path: str = "./data/projects"):
        """Initialize project service"""
        self.storage_path = storage_path
        self.projects: Dict[str, Project] = {}
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing projects
        self._load_projects()
        
        logger.info("ProjectService initialized", storage_path=storage_path)
    
    def _load_projects(self):
        """Load projects from disk"""
        try:
            project_file = os.path.join(self.storage_path, "projects.json")
            if os.path.exists(project_file):
                with open(project_file, 'r') as f:
                    data = json.load(f)
                    for proj_data in data:
                        project = Project(**proj_data)
                        self.projects[project.project_id] = project
                logger.info(f"Loaded {len(self.projects)} projects")
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
    
    def _save_projects(self):
        """Save projects to disk"""
        try:
            project_file = os.path.join(self.storage_path, "projects.json")
            with open(project_file, 'w') as f:
                data = [proj.model_dump() for proj in self.projects.values()]
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(self.projects)} projects")
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    async def create_project(self, request: CreateProjectRequest) -> Project:
        """Create a new project"""
        
        # Generate project ID
        project_id = f"proj-{int(datetime.utcnow().timestamp())}"
        
        # Create project
        project = Project(
            project_id=project_id,
            name=request.name,
            description=request.description,
            user_id=request.user_id,
            cloud_providers=request.cloud_providers,
            tags=request.tags or [],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store project
        self.projects[project_id] = project
        self._save_projects()
        
        logger.info(
            "project_created",
            project_id=project_id,
            name=request.name,
            user_id=request.user_id
        )
        
        return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return self.projects.get(project_id)
    
    async def list_projects(self, user_id: Optional[str] = None) -> List[Project]:
        """List all projects, optionally filtered by user"""
        projects = list(self.projects.values())
        
        if user_id:
            projects = [p for p in projects if p.user_id == user_id]
        
        return projects
    
    async def update_project(
        self,
        project_id: str,
        request: UpdateProjectRequest
    ) -> Optional[Project]:
        """Update project settings"""
        
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Update fields
        if request.name is not None:
            project.name = request.name
        if request.description is not None:
            project.description = request.description
        if request.monitoring_enabled is not None:
            project.monitoring_enabled = request.monitoring_enabled
        if request.auto_remediation is not None:
            project.auto_remediation = request.auto_remediation
        if request.status is not None:
            project.status = request.status
        if request.tags is not None:
            project.tags = request.tags
        
        project.updated_at = datetime.utcnow()
        
        self._save_projects()
        
        logger.info("project_updated", project_id=project_id)
        
        return project
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        
        if project_id not in self.projects:
            return False
        
        del self.projects[project_id]
        self._save_projects()
        
        logger.info("project_deleted", project_id=project_id)
        
        return True
    
    async def add_resource(
        self,
        project_id: str,
        resource: Dict[str, Any]
    ) -> Optional[Project]:
        """Add a resource to project"""
        
        project = self.projects.get(project_id)
        if not project:
            return None
        
        project.resources.append(resource)
        project.total_resources = len(project.resources)
        project.updated_at = datetime.utcnow()
        
        self._save_projects()
        
        logger.info(
            "resource_added",
            project_id=project_id,
            resource_id=resource.get("id")
        )
        
        return project
    
    async def get_infrastructure_graph(
        self,
        project_id: str
    ) -> Optional[InfrastructureGraph]:
        """Generate infrastructure topology graph"""
        
        project = self.projects.get(project_id)
        if not project:
            return None
        
        nodes = []
        edges = []
        
        # Convert resources to nodes
        for i, resource in enumerate(project.resources):
            # Ensure created_at is always a datetime
            created_at = resource.get("created_at")
            if not created_at:
                created_at = datetime.utcnow()
            elif isinstance(created_at, str):
                # Parse ISO format string to datetime
                from datetime import datetime as dt
                try:
                    created_at = dt.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.utcnow()
            
            node = InfrastructureNode(
                id=resource.get("id", f"resource-{i}"),
                name=resource.get("name", f"Resource {i}"),
                type=resource.get("type", "unknown"),
                provider=CloudProvider(resource.get("provider", "digitalocean")),
                status=resource.get("status", "active"),
                region=resource.get("region", "unknown"),
                created_at=created_at,
                cost_per_month=resource.get("cost_per_month"),
                metrics=resource.get("metrics"),
                tags=resource.get("tags", []),
                x=float(i % 5) * 150,  # Simple grid layout
                y=float(i // 5) * 150
            )
            nodes.append(node)
            
            # Create edges based on dependencies
            if "dependencies" in resource:
                for dep in resource["dependencies"]:
                    edges.append(InfrastructureEdge(
                        source=resource.get("id"),
                        target=dep,
                        relationship="depends_on"
                    ))
        
        graph = InfrastructureGraph(
            project_id=project_id,
            nodes=nodes,
            edges=edges,
            generated_at=datetime.utcnow()
        )
        
        return graph
    
    async def update_project_stats(self, project_id: str):
        """Update project statistics"""
        
        project = self.projects.get(project_id)
        if not project:
            return
        
        # Calculate total cost
        total_cost = sum(
            r.get("cost_per_month", 0)
            for r in project.resources
        )
        
        project.total_cost = total_cost
        project.updated_at = datetime.utcnow()
        
        self._save_projects()
