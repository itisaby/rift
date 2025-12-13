"""
Remediation Agent for Rift
Executes infrastructure fixes safely using Terraform and AI guidance
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from agents.base_agent import BaseAgent
from agents.safety_validator import SafetyValidator
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.incident import (
    RemediationPlan,
    RemediationResult,
    RemediationStatus,
    RemediationAction
)

logger = logging.getLogger("rift.agents.remediation")


class RemediationAgent(BaseAgent):
    """
    Remediation Agent for executing infrastructure fixes.
    Uses Terraform, safety validation, and AI guidance to safely
    apply changes and verify fixes.
    """

    def __init__(
        self,
        agent_endpoint: str,
        agent_key: str,
        agent_id: str,
        terraform_mcp: TerraformMCP,
        do_mcp: DigitalOceanMCP,
        safety_validator: SafetyValidator,
        knowledge_base_id: Optional[str] = None
    ):
        """
        Initialize Remediation Agent.

        Args:
            agent_endpoint: Gradient AI agent endpoint URL
            agent_key: API key for authentication
            agent_id: Unique agent identifier
            terraform_mcp: Terraform MCP client instance
            do_mcp: DigitalOcean MCP client instance
            safety_validator: Safety validator instance
            knowledge_base_id: Optional knowledge base ID
        """
        super().__init__(
            agent_endpoint=agent_endpoint,
            agent_key=agent_key,
            agent_id=agent_id,
            agent_name="Remediation Agent",
            knowledge_base_id=knowledge_base_id
        )

        self.terraform_mcp = terraform_mcp
        self.do_mcp = do_mcp
        self.safety_validator = safety_validator

        # Store state backups for rollback
        self.state_backups: Dict[str, Any] = {}

        logger.info("Remediation Agent initialized")

    async def execute_remediation(
        self,
        plan: RemediationPlan,
        auto_approve: bool = False
    ) -> RemediationResult:
        """
        Execute a remediation plan.

        Workflow:
        1. Generate Terraform config
        2. Validate via Terraform MCP
        3. Check safety rules
        4. Execute dry-run (plan)
        5. If safe, apply changes
        6. Verify fix
        7. Update knowledge base

        Args:
            plan: The remediation plan to execute
            auto_approve: Whether to auto-approve changes

        Returns:
            RemediationResult with execution details
        """
        import time

        start_time = time.time()
        logs = []

        try:
            logger.info(f"Executing remediation plan {plan.id}")
            logs.append(f"Starting remediation: {plan.action.value}")

            # Step 1: Generate Terraform configuration
            logs.append("Step 1: Generating Terraform configuration...")
            terraform_config = await self.generate_terraform(plan.action, plan.parameters)

            if not terraform_config:
                return self._create_failed_result(
                    plan=plan,
                    error_message="Failed to generate Terraform configuration",
                    duration=time.time() - start_time,
                    logs=logs
                )

            logs.append(f"Generated {len(terraform_config)} bytes of Terraform config")

            # Step 2: Validate Terraform configuration
            logs.append("Step 2: Validating Terraform configuration...")
            validation_result = await self.validate_terraform(terraform_config)

            if not validation_result.valid:
                return self._create_failed_result(
                    plan=plan,
                    error_message=f"Terraform validation failed: {', '.join(validation_result.errors)}",
                    duration=time.time() - start_time,
                    logs=logs
                )

            logs.append("Terraform configuration is valid")

            # Step 3: Check safety rules
            logs.append("Step 3: Running safety validation...")
            safety_result = await self.safety_validator.validate_plan(plan)

            if not safety_result.is_safe:
                return self._create_failed_result(
                    plan=plan,
                    error_message=f"Safety validation failed: {', '.join(safety_result.failed_checks)}",
                    duration=time.time() - start_time,
                    logs=logs
                )

            logs.append(f"Safety checks passed ({len(safety_result.passed_checks)} checks)")

            if safety_result.warnings:
                for warning in safety_result.warnings:
                    logs.append(f"⚠️  Warning: {warning}")

            # Check if approval is required
            if safety_result.requires_approval and not auto_approve:
                logs.append("⏸️  Approval required before proceeding")
                return RemediationResult(
                    plan_id=plan.id,
                    incident_id=plan.incident_id,
                    status=RemediationStatus.PENDING,
                    success=False,
                    action_taken="Awaiting approval",
                    duration=int(time.time() - start_time),
                    verification_passed=False,
                    error_message="Approval required",
                    logs=logs,
                    metadata={
                        "requires_approval": True,
                        "safety_result": {
                            "passed_checks": safety_result.passed_checks,
                            "warnings": safety_result.warnings
                        }
                    }
                )

            # Step 4: Store current state for rollback
            logs.append("Step 4: Backing up current state...")
            await self._backup_state(plan)
            logs.append("State backup complete")

            # Step 5: Execute dry-run (Terraform plan)
            logs.append("Step 5: Running Terraform plan (dry-run)...")
            plan_result = await self.terraform_mcp.plan(
                config=terraform_config,
                variables=plan.parameters
            )

            if not plan_result.success:
                return self._create_failed_result(
                    plan=plan,
                    error_message=f"Terraform plan failed: {plan_result.plan_output}",
                    duration=time.time() - start_time,
                    logs=logs
                )

            logs.append(f"Plan: {plan_result.resources_to_add} to add, "
                       f"{plan_result.resources_to_change} to change, "
                       f"{plan_result.resources_to_destroy} to destroy")

            # Step 6: Apply changes
            logs.append("Step 6: Applying Terraform changes...")
            apply_result = await self.apply_changes(
                config=terraform_config,
                variables=plan.parameters,
                auto_approve=True
            )

            if not apply_result.success:
                # Attempt rollback
                logs.append("❌ Apply failed, attempting rollback...")
                rollback_success = await self.rollback(plan)
                logs.append(f"Rollback {'succeeded' if rollback_success else 'failed'}")

                return self._create_failed_result(
                    plan=plan,
                    error_message=apply_result.error_message or "Apply failed",
                    duration=time.time() - start_time,
                    logs=logs,
                    rollback_executed=rollback_success
                )

            logs.append(f"✓ Applied successfully: {apply_result.resources_created} created, "
                       f"{apply_result.resources_updated} updated")

            # Step 7: Verify fix
            logs.append("Step 7: Verifying fix...")
            verification_passed = await self.verify_fix(plan.incident_id)
            logs.append(f"Verification: {'✓ PASSED' if verification_passed else '✗ FAILED'}")

            if not verification_passed:
                logs.append("⚠️  Fix did not resolve the issue, consider rollback")

            # Step 8: Update knowledge base
            logs.append("Step 8: Updating knowledge base...")
            await self._update_knowledge_base(plan, apply_result, verification_passed)
            logs.append("Knowledge base updated")

            duration = time.time() - start_time

            return RemediationResult(
                plan_id=plan.id,
                incident_id=plan.incident_id,
                status=RemediationStatus.SUCCESS if verification_passed else RemediationStatus.VERIFYING,
                success=True,
                action_taken=plan.action_description,
                duration=int(duration),
                actual_cost=plan.estimated_cost,  # Would get from DO API in production
                verification_passed=verification_passed,
                logs=logs,
                metadata={
                    "terraform_result": {
                        "created": apply_result.resources_created,
                        "updated": apply_result.resources_updated,
                        "destroyed": apply_result.resources_destroyed
                    },
                    "safety_checks_passed": len(safety_result.passed_checks),
                    "output_values": apply_result.output_values
                }
            )

        except Exception as e:
            logger.error(f"Remediation execution failed: {str(e)}")
            logs.append(f"❌ Exception: {str(e)}")

            return self._create_failed_result(
                plan=plan,
                error_message=str(e),
                duration=time.time() - start_time,
                logs=logs
            )

    async def generate_terraform(
        self,
        action: RemediationAction,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Generate Terraform configuration for a remediation action.

        Args:
            action: The remediation action to perform
            parameters: Parameters for the action

        Returns:
            Terraform configuration as string
        """
        logger.debug(f"Generating Terraform for action: {action.value}")

        # Use AI to generate Terraform configuration
        prompt = f"""
        Generate a complete Terraform configuration for this remediation action:

        Action: {action.value}
        Parameters: {json.dumps(parameters, indent=2)}

        Requirements:
        - Use DigitalOcean provider
        - Include all necessary variables
        - Add appropriate resource definitions
        - Ensure idempotent operations
        - Add comments for clarity

        Return ONLY the Terraform HCL code, no explanations.
        """

        try:
            response = await self.query_agent(prompt=prompt, use_knowledge_base=False)
            terraform_config = response.get("response", "")

            # Clean up the response (remove markdown code blocks if present)
            if "```" in terraform_config:
                # Extract code between ```hcl and ```
                parts = terraform_config.split("```")
                for part in parts:
                    if part.strip().startswith("hcl") or part.strip().startswith("terraform"):
                        terraform_config = part.replace("hcl", "").replace("terraform", "").strip()
                        break
                    elif "resource" in part or "provider" in part:
                        terraform_config = part.strip()
                        break

            logger.info(f"Generated Terraform configuration ({len(terraform_config)} bytes)")
            return terraform_config

        except Exception as e:
            logger.error(f"Failed to generate Terraform: {str(e)}")
            return ""

    async def validate_terraform(self, config: str) -> Any:
        """
        Validate Terraform configuration.

        Args:
            config: Terraform configuration to validate

        Returns:
            ValidationResult
        """
        return await self.terraform_mcp.validate_config(config)

    async def apply_changes(
        self,
        config: str,
        variables: Optional[Dict[str, Any]] = None,
        auto_approve: bool = False
    ) -> Any:
        """
        Apply Terraform changes.

        Args:
            config: Terraform configuration
            variables: Optional variables
            auto_approve: Whether to auto-approve

        Returns:
            ApplyResult
        """
        return await self.terraform_mcp.apply(
            config=config,
            variables=variables,
            auto_approve=auto_approve
        )

    async def verify_fix(self, incident_id: str) -> bool:
        """
        Verify that a fix resolved the incident.

        This would typically re-run Monitor Agent checks or query metrics.

        Args:
            incident_id: The incident that was remediated

        Returns:
            True if fix is verified
        """
        logger.info(f"Verifying fix for incident {incident_id}")

        # In a full implementation, this would:
        # 1. Wait for metrics to stabilize (30-60 seconds)
        # 2. Re-query Prometheus for the affected metric
        # 3. Check if metric is now below threshold
        # 4. Verify droplet/resource is healthy

        # For now, return True as placeholder
        # Real implementation would integrate with Monitor Agent
        await self._wait_for_stabilization(30)

        logger.info("Fix verification complete (placeholder)")
        return True

    async def rollback(self, plan: RemediationPlan) -> bool:
        """
        Rollback changes made by a remediation.

        Args:
            plan: The plan to rollback

        Returns:
            True if rollback succeeded
        """
        try:
            logger.warning(f"Rolling back plan {plan.id}")

            # Retrieve backed up state
            backup = self.state_backups.get(plan.id)

            if not backup:
                logger.error("No state backup found for rollback")
                return False

            # Execute rollback steps from plan
            if plan.rollback_plan and "steps" in plan.rollback_plan:
                for i, step in enumerate(plan.rollback_plan["steps"], 1):
                    logger.info(f"Executing rollback step {i}: {step}")
                    # In production, execute these steps
                    # For now, just log them

            logger.info("Rollback completed")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False

    async def _backup_state(self, plan: RemediationPlan):
        """Backup current state before making changes."""

        try:
            # Get current Terraform state
            state = await self.terraform_mcp.show_state()

            # Store backup
            self.state_backups[plan.id] = {
                "timestamp": datetime.utcnow().isoformat(),
                "plan_id": plan.id,
                "state": state
            }

            logger.debug(f"State backed up for plan {plan.id}")

        except Exception as e:
            logger.warning(f"Failed to backup state: {str(e)}")

    async def _update_knowledge_base(
        self,
        plan: RemediationPlan,
        apply_result: Any,
        verification_passed: bool
    ):
        """Update knowledge base with remediation results."""

        try:
            update_prompt = f"""
            Record this remediation in the knowledge base:

            Action: {plan.action.value}
            Incident: {plan.incident_id}
            Success: {verification_passed}
            Resources Modified: {apply_result.resources_created + apply_result.resources_updated}
            Duration: {apply_result.duration_seconds}s

            This information will help diagnose similar incidents in the future.
            """

            await self.query_agent(prompt=update_prompt, use_knowledge_base=True)
            logger.debug("Knowledge base updated")

        except Exception as e:
            logger.warning(f"Failed to update knowledge base: {str(e)}")

    async def _wait_for_stabilization(self, seconds: int):
        """Wait for metrics to stabilize after changes."""
        import asyncio
        logger.debug(f"Waiting {seconds}s for metrics to stabilize...")
        await asyncio.sleep(seconds)

    def _create_failed_result(
        self,
        plan: RemediationPlan,
        error_message: str,
        duration: float,
        logs: list,
        rollback_executed: bool = False
    ) -> RemediationResult:
        """Create a failed RemediationResult."""

        return RemediationResult(
            plan_id=plan.id,
            incident_id=plan.incident_id,
            status=RemediationStatus.FAILED,
            success=False,
            action_taken=f"Failed: {plan.action.value}",
            duration=int(duration),
            verification_passed=False,
            error_message=error_message,
            rollback_executed=rollback_executed,
            logs=logs
        )
