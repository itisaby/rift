"""
Drift Detection Service for Rift
Detects infrastructure drift (resources deleted outside Rift) and auto-reconciles.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("rift.services.drift_detector")

TERRAFORM_DATA_DIR = os.path.join(".", "data", "terraform")


@dataclass
class DriftResult:
    project_id: str
    has_drift: bool
    resources_to_add: int = 0
    plan_output: str = ""
    error: Optional[str] = None


@dataclass
class ReconcileResult:
    project_id: str
    success: bool
    resources_created: int = 0
    error: Optional[str] = None


class DriftDetector:
    """Detects and reconciles infrastructure drift for projects managed by Rift."""

    def __init__(self, mcp_manager, project_service):
        self.mcp_manager = mcp_manager
        self.project_service = project_service

    async def check_all_projects(self) -> List[DriftResult]:
        """Check all active projects with resources for drift."""
        results = []
        try:
            projects = await self.project_service.list_projects()
        except Exception as e:
            logger.error(f"Failed to list projects for drift check: {e}")
            return results

        for project in projects:
            pid = project.project_id
            tf_dir = os.path.join(TERRAFORM_DATA_DIR, pid)
            # Use terraform state file as source of truth — project.resources may be empty
            # if resource saving failed, but state file is always written by terraform apply
            state_path = Path(tf_dir) / "terraform.tfstate"
            if not state_path.exists():
                continue
            # Skip empty state files (no managed resources)
            try:
                state = json.loads(state_path.read_text())
                if not state.get("resources"):
                    continue
            except (json.JSONDecodeError, OSError):
                continue
            try:
                result = await self.check_project(pid)
                results.append(result)
            except Exception as e:
                logger.error(f"Drift check failed for project {pid}: {e}")
                results.append(DriftResult(project_id=pid, has_drift=False, error=str(e)))

        return results

    async def check_project(self, project_id: str) -> DriftResult:
        """Run terraform plan on a project's saved config to detect drift."""
        tf_dir = os.path.join(TERRAFORM_DATA_DIR, project_id)
        config_path = Path(tf_dir) / "main.tf"
        vars_path = Path(tf_dir) / "terraform.tfvars.json"

        if not config_path.exists():
            return DriftResult(project_id=project_id, has_drift=False, error="No saved config")

        config = config_path.read_text()
        variables = None
        if vars_path.exists():
            try:
                variables = json.loads(vars_path.read_text())
            except json.JSONDecodeError:
                pass

        plan_args = {
            "config": config,
            "working_dir": tf_dir,
        }
        if variables:
            plan_args["variables"] = variables

        plan_result = await self.mcp_manager.call("terraform", "terraform_plan", plan_args)

        if not plan_result.get("success"):
            return DriftResult(
                project_id=project_id,
                has_drift=False,
                error=plan_result.get("plan_output", "Plan failed"),
            )

        resources_to_add = plan_result.get("resources_to_add", 0)
        has_drift = resources_to_add > 0

        if has_drift:
            logger.warning(
                f"Drift detected for project {project_id}: {resources_to_add} resource(s) to re-create"
            )

        return DriftResult(
            project_id=project_id,
            has_drift=has_drift,
            resources_to_add=resources_to_add,
            plan_output=plan_result.get("plan_output", ""),
        )

    async def reconcile(self, project_id: str) -> ReconcileResult:
        """Re-apply saved config to restore missing resources."""
        tf_dir = os.path.join(TERRAFORM_DATA_DIR, project_id)
        config_path = Path(tf_dir) / "main.tf"
        vars_path = Path(tf_dir) / "terraform.tfvars.json"

        if not config_path.exists():
            return ReconcileResult(project_id=project_id, success=False, error="No saved config")

        config = config_path.read_text()
        variables = None
        if vars_path.exists():
            try:
                variables = json.loads(vars_path.read_text())
            except json.JSONDecodeError:
                pass

        apply_args = {
            "config": config,
            "auto_approve": True,
            "working_dir": tf_dir,
        }
        if variables:
            apply_args["variables"] = variables

        apply_result = await self.mcp_manager.call("terraform", "terraform_apply", apply_args)

        success = apply_result.get("success", False)
        resources_created = apply_result.get("resources_created", 0)

        if success:
            logger.info(f"Reconciled project {project_id}: {resources_created} resource(s) re-created")
        else:
            logger.error(f"Reconciliation failed for project {project_id}: {apply_result.get('error_message', '')}")

        return ReconcileResult(
            project_id=project_id,
            success=success,
            resources_created=resources_created,
            error=apply_result.get("error_message") if not success else None,
        )
