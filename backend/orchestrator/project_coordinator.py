"""
Enhanced Coordinator with Project Support
Extends the base coordinator to work with projects
"""

from typing import Optional
from orchestrator.coordinator import Coordinator
from services.project_service import ProjectService
from utils.logger import get_logger

logger = get_logger(__name__)


class ProjectAwareCoordinator(Coordinator):
    """
    Extended coordinator that tracks incidents per project
    """
    
    def __init__(self, project_service: ProjectService, *args, **kwargs):
        """Initialize with project service"""
        super().__init__(*args, **kwargs)
        self.project_service = project_service
        logger.info("ProjectAwareCoordinator initialized")
    
    async def handle_incident_for_project(self, project_id: str, incident_id: str):
        """
        Handle an incident and update project stats
        
        Args:
            project_id: Project ID
            incident_id: Incident ID
        """
        # Get the incident
        incident = self.active_incidents.get(incident_id)
        if not incident:
            logger.warning(f"Incident {incident_id} not found")
            return
        
        # Update project with incident
        project = await self.project_service.get_project(project_id)
        if project:
            project.active_incidents = len([
                i for i in self.active_incidents.values()
                if i.resource_name in [r.get("name") for r in project.resources]
            ])
            await self.project_service._save_projects()
            logger.info(f"Updated project {project_id} incident count: {project.active_incidents}")
