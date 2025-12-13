"""
Terraform MCP Client
Interfaces with Terraform for infrastructure-as-code operations
"""

import asyncio
import json
import logging
import tempfile
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger("rift.mcp.terraform")


@dataclass
class ValidationResult:
    """Result of Terraform configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


@dataclass
class PlanResult:
    """Result of Terraform plan operation"""
    success: bool
    changes_count: int
    resources_to_add: int
    resources_to_change: int
    resources_to_destroy: int
    plan_output: str
    estimated_cost: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class ApplyResult:
    """Result of Terraform apply operation"""
    success: bool
    resources_created: int
    resources_updated: int
    resources_destroyed: int
    output_values: Dict[str, Any]
    duration_seconds: float
    error_message: Optional[str] = None


class TerraformMCP:
    """
    Client for interacting with Terraform.
    Provides methods for validating, planning, and applying infrastructure changes.
    """

    def __init__(
        self,
        working_dir: Optional[str] = None,
        terraform_binary: str = "terraform"
    ):
        """
        Initialize Terraform MCP client.

        Args:
            working_dir: Working directory for Terraform operations
            terraform_binary: Path to terraform binary (default: "terraform")
        """
        self.working_dir = working_dir or tempfile.mkdtemp(prefix="rift_terraform_")
        self.terraform_binary = terraform_binary

        # Ensure working directory exists
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Terraform MCP client initialized: {self.working_dir}")

    async def _run_command(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> tuple[int, str, str]:
        """
        Run a Terraform command asynchronously.

        Args:
            args: Command arguments
            cwd: Working directory (defaults to self.working_dir)
            env: Environment variables

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [self.terraform_binary] + args
        work_dir = cwd or self.working_dir

        logger.debug(f"Running terraform command: {' '.join(cmd)}")

        # Merge environment variables
        command_env = os.environ.copy()
        if env:
            command_env.update(env)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=command_env
            )

            stdout, stderr = await process.communicate()

            return (
                process.returncode,
                stdout.decode('utf-8'),
                stderr.decode('utf-8')
            )

        except Exception as e:
            logger.error(f"Failed to run terraform command: {str(e)}")
            raise

    async def init(self, backend_config: Optional[Dict[str, str]] = None) -> bool:
        """
        Initialize Terraform working directory.

        Args:
            backend_config: Optional backend configuration

        Returns:
            True if successful
        """
        try:
            args = ["init", "-no-color"]

            if backend_config:
                for key, value in backend_config.items():
                    args.extend(["-backend-config", f"{key}={value}"])

            returncode, stdout, stderr = await self._run_command(args)

            if returncode != 0:
                logger.error(f"Terraform init failed: {stderr}")
                return False

            logger.info("Terraform initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Terraform init error: {str(e)}")
            return False

    async def validate_config(self, config: str) -> ValidationResult:
        """
        Validate Terraform configuration.

        Args:
            config: Terraform configuration content

        Returns:
            ValidationResult with validation details
        """
        try:
            # Write config to a temporary file
            config_file = Path(self.working_dir) / "main.tf"
            config_file.write_text(config)

            # Initialize first
            await self.init()

            # Run validate
            returncode, stdout, stderr = await self._run_command(
                ["validate", "-json", "-no-color"]
            )

            # Parse JSON output
            try:
                result = json.loads(stdout)
                valid = result.get("valid", False)
                errors = [d.get("summary", "") for d in result.get("diagnostics", []) if d.get("severity") == "error"]
                warnings = [d.get("summary", "") for d in result.get("diagnostics", []) if d.get("severity") == "warning"]

                logger.info(f"Validation result: valid={valid}, errors={len(errors)}, warnings={len(warnings)}")

                return ValidationResult(
                    valid=valid,
                    errors=errors,
                    warnings=warnings,
                    metadata=result
                )

            except json.JSONDecodeError:
                # Fallback to simple validation
                valid = returncode == 0
                return ValidationResult(
                    valid=valid,
                    errors=[stderr] if not valid else [],
                    warnings=[],
                    metadata={"stdout": stdout, "stderr": stderr}
                )

        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return ValidationResult(
                valid=False,
                errors=[str(e)],
                warnings=[],
                metadata={}
            )

    async def plan(
        self,
        config: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> PlanResult:
        """
        Generate Terraform execution plan.

        Args:
            config: Terraform configuration content
            variables: Optional variables to pass to Terraform

        Returns:
            PlanResult with plan details
        """
        try:
            # Write config to file
            config_file = Path(self.working_dir) / "main.tf"
            config_file.write_text(config)

            # Write variables if provided
            if variables:
                var_file = Path(self.working_dir) / "terraform.tfvars.json"
                var_file.write_text(json.dumps(variables, indent=2))

            # Initialize
            await self.init()

            # Run plan
            args = ["plan", "-no-color", "-out=tfplan"]
            if variables:
                args.extend(["-var-file=terraform.tfvars.json"])

            returncode, stdout, stderr = await self._run_command(args)

            if returncode != 0:
                logger.error(f"Terraform plan failed: {stderr}")
                return PlanResult(
                    success=False,
                    changes_count=0,
                    resources_to_add=0,
                    resources_to_change=0,
                    resources_to_destroy=0,
                    plan_output=stderr,
                    metadata={"error": stderr}
                )

            # Parse plan output to count changes
            # Format: "Plan: X to add, Y to change, Z to destroy"
            add_count = 0
            change_count = 0
            destroy_count = 0

            for line in stdout.split('\n'):
                if 'Plan:' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        # Look for pattern: NUMBER to add,
                        if i > 0 and i + 1 < len(parts):
                            try:
                                if parts[i] == 'to' and parts[i + 1].startswith('add'):
                                    add_count = int(parts[i - 1])
                                elif parts[i] == 'to' and parts[i + 1].startswith('change'):
                                    change_count = int(parts[i - 1])
                                elif parts[i] == 'to' and parts[i + 1].startswith('destroy'):
                                    destroy_count = int(parts[i - 1])
                            except (ValueError, IndexError):
                                continue

            changes_count = add_count + change_count + destroy_count

            logger.info(f"Plan generated: {add_count} to add, {change_count} to change, {destroy_count} to destroy")

            return PlanResult(
                success=True,
                changes_count=changes_count,
                resources_to_add=add_count,
                resources_to_change=change_count,
                resources_to_destroy=destroy_count,
                plan_output=stdout,
                metadata={"stdout": stdout, "stderr": stderr}
            )

        except Exception as e:
            logger.error(f"Plan generation failed: {str(e)}")
            return PlanResult(
                success=False,
                changes_count=0,
                resources_to_add=0,
                resources_to_change=0,
                resources_to_destroy=0,
                plan_output=str(e),
                metadata={"error": str(e)}
            )

    async def apply(
        self,
        config: str,
        variables: Optional[Dict[str, Any]] = None,
        auto_approve: bool = False
    ) -> ApplyResult:
        """
        Apply Terraform configuration.

        Args:
            config: Terraform configuration content
            variables: Optional variables
            auto_approve: Whether to auto-approve changes

        Returns:
            ApplyResult with execution details
        """
        import time

        try:
            # Write config to file
            config_file = Path(self.working_dir) / "main.tf"
            config_file.write_text(config)

            # Write variables if provided
            if variables:
                var_file = Path(self.working_dir) / "terraform.tfvars.json"
                var_file.write_text(json.dumps(variables, indent=2))

            # Initialize
            await self.init()

            # Run apply
            args = ["apply", "-no-color"]
            if auto_approve:
                args.append("-auto-approve")
            if variables:
                args.extend(["-var-file=terraform.tfvars.json"])

            start_time = time.time()
            returncode, stdout, stderr = await self._run_command(args)
            duration = time.time() - start_time

            if returncode != 0:
                logger.error(f"Terraform apply failed: {stderr}")
                return ApplyResult(
                    success=False,
                    resources_created=0,
                    resources_updated=0,
                    resources_destroyed=0,
                    output_values={},
                    duration_seconds=duration,
                    error_message=stderr
                )

            # Parse output to count resources
            created = stdout.count("Creating...")
            updated = stdout.count("Modifying...")
            destroyed = stdout.count("Destroying...")

            # Get output values
            output_values = await self.get_outputs()

            logger.info(f"Apply completed: {created} created, {updated} updated, {destroyed} destroyed")

            return ApplyResult(
                success=True,
                resources_created=created,
                resources_updated=updated,
                resources_destroyed=destroyed,
                output_values=output_values,
                duration_seconds=duration
            )

        except Exception as e:
            logger.error(f"Apply failed: {str(e)}")
            return ApplyResult(
                success=False,
                resources_created=0,
                resources_updated=0,
                resources_destroyed=0,
                output_values={},
                duration_seconds=0,
                error_message=str(e)
            )

    async def get_outputs(self) -> Dict[str, Any]:
        """
        Get Terraform output values.

        Returns:
            Dictionary of output values
        """
        try:
            returncode, stdout, stderr = await self._run_command(
                ["output", "-json", "-no-color"]
            )

            if returncode != 0:
                logger.warning(f"Failed to get outputs: {stderr}")
                return {}

            outputs = json.loads(stdout)

            # Extract values from output format
            result = {}
            for key, value in outputs.items():
                if isinstance(value, dict) and "value" in value:
                    result[key] = value["value"]
                else:
                    result[key] = value

            return result

        except Exception as e:
            logger.error(f"Failed to get outputs: {str(e)}")
            return {}

    async def show_state(self, resource: Optional[str] = None) -> Dict[str, Any]:
        """
        Show current Terraform state.

        Args:
            resource: Optional specific resource to show

        Returns:
            State data as dictionary
        """
        try:
            args = ["show", "-json", "-no-color"]
            if resource:
                args.append(resource)

            returncode, stdout, stderr = await self._run_command(args)

            if returncode != 0:
                logger.error(f"Failed to show state: {stderr}")
                return {}

            state = json.loads(stdout)
            logger.debug(f"Retrieved state for resource: {resource or 'all'}")
            return state

        except Exception as e:
            logger.error(f"Failed to show state: {str(e)}")
            return {}

    async def destroy(self, auto_approve: bool = False) -> bool:
        """
        Destroy Terraform-managed infrastructure.

        Args:
            auto_approve: Whether to auto-approve destruction

        Returns:
            True if successful
        """
        try:
            args = ["destroy", "-no-color"]
            if auto_approve:
                args.append("-auto-approve")

            returncode, stdout, stderr = await self._run_command(args)

            if returncode != 0:
                logger.error(f"Terraform destroy failed: {stderr}")
                return False

            logger.info("Infrastructure destroyed successfully")
            return True

        except Exception as e:
            logger.error(f"Destroy failed: {str(e)}")
            return False

    def cleanup(self):
        """Clean up temporary Terraform working directory."""
        import shutil

        try:
            if self.working_dir and self.working_dir.startswith('/tmp/rift_terraform_'):
                shutil.rmtree(self.working_dir)
                logger.info(f"Cleaned up Terraform working directory: {self.working_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup working directory: {str(e)}")
