"""
Safety Validator for Rift
Validates remediation plans for safety before execution
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from models.incident import RemediationPlan, RemediationAction

logger = logging.getLogger("rift.safety_validator")


@dataclass
class ValidationResult:
    """Result of safety validation"""
    is_safe: bool
    passed_checks: List[str]
    failed_checks: List[str]
    warnings: List[str]
    requires_approval: bool
    metadata: Dict[str, Any]


@dataclass
class CostEstimate:
    """Cost estimate for a remediation"""
    one_time_cost: float
    monthly_cost: float
    total_first_month: float
    breakdown: Dict[str, float]


class SafetyValidator:
    """
    Validates remediation plans for safety before execution.

    Safety Rules:
    - Require approval for: delete, destroy, terminate operations
    - Cost threshold: $50 (require approval above)
    - Always validate Terraform configuration
    - Ensure rollback plan exists
    - No destructive operations on production without approval
    """

    # Cost threshold for automatic approval (USD)
    COST_THRESHOLD = 50.0

    # Destructive operations that require approval
    DESTRUCTIVE_OPERATIONS = {
        "delete",
        "destroy",
        "terminate",
        "drop",
        "remove"
    }

    def __init__(self, auto_approve_threshold: float = COST_THRESHOLD):
        """
        Initialize Safety Validator.

        Args:
            auto_approve_threshold: Maximum cost for automatic approval (USD)
        """
        self.auto_approve_threshold = auto_approve_threshold
        logger.info(f"Safety Validator initialized (auto-approve threshold: ${auto_approve_threshold})")

    async def validate_plan(self, plan: RemediationPlan) -> ValidationResult:
        """
        Validate a remediation plan for safety.

        Args:
            plan: The remediation plan to validate

        Returns:
            ValidationResult with safety assessment
        """
        logger.info(f"Validating remediation plan {plan.id}")

        passed_checks = []
        failed_checks = []
        warnings = []

        # Check 1: Validate rollback plan exists
        if await self.verify_rollback_possible(plan):
            passed_checks.append("Rollback plan exists and is valid")
        else:
            failed_checks.append("No valid rollback plan found")
            warnings.append("Execution without rollback capability is risky")

        # Check 2: Check for destructive operations
        is_destructive = await self.check_destructive_ops(plan)
        if is_destructive:
            warnings.append(f"Plan contains destructive operation: {plan.action.value}")
            requires_approval = True
        else:
            passed_checks.append("No destructive operations detected")
            requires_approval = plan.requires_approval

        # Check 3: Validate cost estimate
        if plan.estimated_cost is not None:
            cost_check = await self.estimate_cost(plan)

            if cost_check.total_first_month <= self.auto_approve_threshold:
                passed_checks.append(f"Cost within auto-approve threshold: ${cost_check.total_first_month:.2f} <= ${self.auto_approve_threshold:.2f}")
            else:
                warnings.append(f"Cost exceeds auto-approve threshold: ${cost_check.total_first_month:.2f} > ${self.auto_approve_threshold:.2f}")
                requires_approval = True
        else:
            warnings.append("No cost estimate provided")

        # Check 4: Validate safety checks are defined
        if plan.safety_checks and len(plan.safety_checks) > 0:
            passed_checks.append(f"Safety checks defined ({len(plan.safety_checks)} checks)")
        else:
            failed_checks.append("No safety checks defined in plan")

        # Check 5: Validate parameters are complete
        required_params = self._get_required_params(plan.action)
        missing_params = [p for p in required_params if p not in plan.parameters]

        if not missing_params:
            passed_checks.append("All required parameters present")
        else:
            failed_checks.append(f"Missing required parameters: {', '.join(missing_params)}")

        # Check 6: Validate Terraform configuration if provided
        if plan.terraform_config:
            if self._validate_terraform_syntax(plan.terraform_config):
                passed_checks.append("Terraform configuration syntax valid")
            else:
                failed_checks.append("Invalid Terraform configuration syntax")
        else:
            warnings.append("No Terraform configuration provided")

        # Determine if plan is safe
        is_safe = len(failed_checks) == 0

        logger.info(f"Validation complete: safe={is_safe}, passed={len(passed_checks)}, failed={len(failed_checks)}, warnings={len(warnings)}")

        return ValidationResult(
            is_safe=is_safe,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            requires_approval=requires_approval,
            metadata={
                "plan_id": plan.id,
                "action": plan.action.value,
                "estimated_cost": plan.estimated_cost
            }
        )

    async def check_destructive_ops(self, plan: RemediationPlan) -> bool:
        """
        Check if a plan contains destructive operations.

        Args:
            plan: The remediation plan to check

        Returns:
            True if plan contains destructive operations
        """
        # Check action type
        action_name = plan.action.value.lower()

        for destructive_keyword in self.DESTRUCTIVE_OPERATIONS:
            if destructive_keyword in action_name:
                logger.warning(f"Destructive operation detected: {action_name} contains '{destructive_keyword}'")
                return True

        # Check Terraform config for destructive operations
        if plan.terraform_config:
            config_lower = plan.terraform_config.lower()
            for keyword in self.DESTRUCTIVE_OPERATIONS:
                if keyword in config_lower:
                    logger.warning(f"Destructive keyword '{keyword}' found in Terraform config")
                    return True

        # Check parameters for force flags
        if plan.parameters:
            force_params = [k for k in plan.parameters.keys() if 'force' in k.lower() or 'destroy' in k.lower()]
            if force_params:
                logger.warning(f"Force/destroy parameters detected: {force_params}")
                return True

        return False

    async def estimate_cost(self, plan: RemediationPlan) -> CostEstimate:
        """
        Estimate the cost of executing a remediation plan.

        Args:
            plan: The remediation plan to estimate

        Returns:
            CostEstimate with breakdown
        """
        # Use plan's estimated cost if available, otherwise calculate
        if plan.estimated_cost is not None:
            monthly_cost = plan.estimated_cost
        else:
            monthly_cost = self._calculate_cost(plan)

        # One-time costs (e.g., data transfer, snapshots)
        one_time_cost = self._calculate_one_time_cost(plan)

        # Total first month
        total_first_month = one_time_cost + monthly_cost

        # Breakdown
        breakdown = {
            "monthly_recurring": monthly_cost,
            "one_time_setup": one_time_cost
        }

        # Add action-specific breakdown
        if plan.action == RemediationAction.RESIZE_DROPLET:
            breakdown["droplet_size_upgrade"] = monthly_cost
        elif plan.action == RemediationAction.ADD_VOLUME:
            breakdown["volume_storage"] = monthly_cost
        elif plan.action == RemediationAction.UPDATE_FIREWALL:
            breakdown["firewall_rules"] = 0.0  # Firewalls are free

        logger.info(f"Cost estimate: ${total_first_month:.2f} total (${one_time_cost:.2f} one-time + ${monthly_cost:.2f}/month)")

        return CostEstimate(
            one_time_cost=one_time_cost,
            monthly_cost=monthly_cost,
            total_first_month=total_first_month,
            breakdown=breakdown
        )

    async def verify_rollback_possible(self, plan: RemediationPlan) -> bool:
        """
        Verify that rollback is possible for a plan.

        Args:
            plan: The remediation plan to check

        Returns:
            True if rollback is possible
        """
        # Check if rollback plan exists
        if not plan.rollback_plan:
            logger.warning("No rollback plan defined")
            return False

        # Check if rollback plan has required fields
        if not isinstance(plan.rollback_plan, dict):
            logger.warning("Invalid rollback plan format")
            return False

        required_fields = ["description", "steps"]
        missing_fields = [f for f in required_fields if f not in plan.rollback_plan]

        if missing_fields:
            logger.warning(f"Rollback plan missing fields: {missing_fields}")
            return False

        # Check if rollback steps are defined
        steps = plan.rollback_plan.get("steps", [])
        if not steps or len(steps) == 0:
            logger.warning("Rollback plan has no steps defined")
            return False

        logger.debug(f"Rollback plan verified: {len(steps)} steps defined")
        return True

    def _get_required_params(self, action: RemediationAction) -> List[str]:
        """Get list of required parameters for an action."""

        param_map = {
            RemediationAction.RESIZE_DROPLET: ["droplet_id", "new_size"],
            RemediationAction.ADD_VOLUME: ["volume_name", "size_gb", "region"],
            RemediationAction.UPDATE_FIREWALL: ["firewall_id", "rules"],
            RemediationAction.RESTART_SERVICE: ["droplet_id", "service_name"],
            RemediationAction.CLEAN_DISK: ["droplet_id", "path"],
            RemediationAction.SCALE_KUBERNETES: ["cluster_id", "node_count"],
            RemediationAction.UPDATE_LOAD_BALANCER: ["lb_id", "configuration"]
        }

        return param_map.get(action, [])

    def _validate_terraform_syntax(self, config: str) -> bool:
        """Basic Terraform syntax validation."""

        if not config or len(config.strip()) == 0:
            return False

        # Check for basic Terraform structure
        has_resource = "resource" in config or "data" in config or "module" in config
        has_opening_brace = "{" in config
        has_closing_brace = "}" in config

        # Count braces
        opening_count = config.count("{")
        closing_count = config.count("}")

        balanced_braces = opening_count == closing_count

        return has_resource and has_opening_brace and has_closing_brace and balanced_braces

    def _calculate_cost(self, plan: RemediationPlan) -> float:
        """Calculate monthly cost for a plan."""

        # DigitalOcean pricing estimates (approximate)
        if plan.action == RemediationAction.RESIZE_DROPLET:
            # Estimate based on typical size upgrade
            # s-1vcpu-1gb ($6) -> s-2vcpu-2gb ($18) = $12 diff
            return 12.0

        elif plan.action == RemediationAction.ADD_VOLUME:
            # $0.10/GB per month
            size_gb = plan.parameters.get("size_gb", 100)
            return size_gb * 0.10

        elif plan.action == RemediationAction.UPDATE_FIREWALL:
            # Firewalls are free
            return 0.0

        elif plan.action == RemediationAction.SCALE_KUBERNETES:
            # Node pricing varies, estimate $12 per additional node
            return 12.0

        elif plan.action == RemediationAction.UPDATE_LOAD_BALANCER:
            # Load balancers are $12/month
            return 12.0

        else:
            # No recurring cost for service restarts, disk cleanup
            return 0.0

    def _calculate_one_time_cost(self, plan: RemediationPlan) -> float:
        """Calculate one-time costs for a plan."""

        # Most operations have no one-time cost
        # Data transfer, snapshots, etc. would add one-time costs
        return 0.0
