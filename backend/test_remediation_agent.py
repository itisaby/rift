"""
Test script for Remediation Agent
Verifies the Remediation Agent can execute fixes safely
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from agents.remediation_agent import RemediationAgent
from agents.safety_validator import SafetyValidator
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.incident import (
    RemediationPlan,
    RemediationAction
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_remediation_agent():
    """Test Remediation Agent functionality"""

    # Load environment variables
    load_dotenv()

    # Initialize MCP clients
    logger.info("Initializing MCP clients...")

    do_mcp = DigitalOceanMCP(
        api_token=os.getenv("DIGITALOCEAN_API_TOKEN")
    )

    terraform_mcp = TerraformMCP(
        working_dir="/tmp/rift_terraform_remediation_test"
    )

    # Initialize Safety Validator
    logger.info("Initializing Safety Validator...")
    safety_validator = SafetyValidator(auto_approve_threshold=50.0)

    # Initialize Remediation Agent
    logger.info("Initializing Remediation Agent...")

    remediation_agent = RemediationAgent(
        agent_endpoint=os.getenv("REMEDIATION_AGENT_ENDPOINT"),
        agent_key=os.getenv("REMEDIATION_AGENT_KEY"),
        agent_id=os.getenv("REMEDIATION_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        safety_validator=safety_validator,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    try:
        # Test 1: Check agent health
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Checking Remediation Agent health")
        logger.info("="*60)

        health = await remediation_agent.check_health()
        logger.info(f"Agent health: {health}")

        # Test 2: Create a mock remediation plan
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Creating mock remediation plan")
        logger.info("="*60)

        plan = RemediationPlan(
            diagnosis_id="diag-test-123",
            incident_id="inc-test-456",
            action=RemediationAction.RESIZE_DROPLET,
            action_description="Resize droplet from s-1vcpu-1gb to s-2vcpu-2gb to handle increased CPU load",
            parameters={
                "droplet_id": "536356505",
                "current_size": "s-1vcpu-1gb",
                "new_size": "s-2vcpu-2gb",
                "resize_disk": False
            },
            safety_checks=[
                "Validate Terraform configuration",
                "Check estimated cost is within acceptable range",
                "Verify no destructive operations",
                "Ensure rollback plan is available"
            ],
            rollback_plan={
                "description": "Rollback to previous droplet size",
                "steps": [
                    "terraform state pull > rollback.tfstate",
                    "terraform apply -auto-approve rollback.tfstate"
                ]
            },
            requires_approval=False,
            estimated_cost=12.0,
            estimated_duration=90
        )

        logger.info(f"Created remediation plan: {plan.id}")
        logger.info(f"  Action: {plan.action.value}")
        logger.info(f"  Parameters: {plan.parameters}")
        logger.info(f"  Estimated Cost: ${plan.estimated_cost:.2f}")
        logger.info(f"  Requires Approval: {plan.requires_approval}")

        # Test 3: Validate plan safety
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Validating plan safety")
        logger.info("="*60)

        validation_result = await safety_validator.validate_plan(plan)

        logger.info(f"\nSafety Validation Results:")
        logger.info(f"  Is Safe: {validation_result.is_safe}")
        logger.info(f"  Requires Approval: {validation_result.requires_approval}")
        logger.info(f"\n  Passed Checks ({len(validation_result.passed_checks)}):")
        for check in validation_result.passed_checks:
            logger.info(f"    ✓ {check}")

        if validation_result.failed_checks:
            logger.info(f"\n  Failed Checks ({len(validation_result.failed_checks)}):")
            for check in validation_result.failed_checks:
                logger.info(f"    ✗ {check}")

        if validation_result.warnings:
            logger.info(f"\n  Warnings ({len(validation_result.warnings)}):")
            for warning in validation_result.warnings:
                logger.info(f"    ⚠️  {warning}")

        # Test 4: Generate Terraform configuration
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Generating Terraform configuration")
        logger.info("="*60)

        terraform_config = await remediation_agent.generate_terraform(
            action=plan.action,
            parameters=plan.parameters
        )

        logger.info(f"Generated Terraform configuration:")
        logger.info(f"  Length: {len(terraform_config)} bytes")
        logger.info(f"\n  Preview:")
        logger.info("  " + "-" * 56)
        for line in terraform_config.split('\n')[:15]:
            logger.info(f"  {line}")
        if len(terraform_config.split('\n')) > 15:
            logger.info("  ...")
        logger.info("  " + "-" * 56)

        # Test 5: Validate Terraform configuration
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Validating Terraform configuration")
        logger.info("="*60)

        tf_validation = await remediation_agent.validate_terraform(terraform_config)

        logger.info(f"Terraform Validation:")
        logger.info(f"  Valid: {tf_validation.valid}")

        if tf_validation.errors:
            logger.info(f"  Errors: {tf_validation.errors}")
        if tf_validation.warnings:
            logger.info(f"  Warnings: {tf_validation.warnings}")

        # Test 6: Test cost estimation
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Testing cost estimation")
        logger.info("="*60)

        cost_estimate = await safety_validator.estimate_cost(plan)

        logger.info(f"Cost Estimate:")
        logger.info(f"  One-time Cost: ${cost_estimate.one_time_cost:.2f}")
        logger.info(f"  Monthly Cost: ${cost_estimate.monthly_cost:.2f}")
        logger.info(f"  Total First Month: ${cost_estimate.total_first_month:.2f}")
        logger.info(f"\n  Breakdown:")
        for item, cost in cost_estimate.breakdown.items():
            logger.info(f"    {item}: ${cost:.2f}")

        # Test 7: Test destructive operation detection
        logger.info("\n" + "="*60)
        logger.info("TEST 7: Testing destructive operation detection")
        logger.info("="*60)

        test_plans = [
            RemediationPlan(
                diagnosis_id="test1",
                incident_id="test1",
                action=RemediationAction.RESIZE_DROPLET,
                action_description="Safe resize",
                parameters={},
                safety_checks=[],
                rollback_plan={"description": "rollback", "steps": ["step1"]}
            ),
            RemediationPlan(
                diagnosis_id="test2",
                incident_id="test2",
                action=RemediationAction.UPDATE_FIREWALL,
                action_description="Update firewall rules",
                parameters={"force_destroy": True},
                safety_checks=[],
                rollback_plan={"description": "rollback", "steps": ["step1"]}
            )
        ]

        for test_plan in test_plans:
            is_destructive = await safety_validator.check_destructive_ops(test_plan)
            logger.info(f"  {test_plan.action.value}: {'DESTRUCTIVE' if is_destructive else 'Safe'}")

        # Test 8: Test rollback verification
        logger.info("\n" + "="*60)
        logger.info("TEST 8: Testing rollback verification")
        logger.info("="*60)

        test_rollback_plans = [
            {
                "plan": RemediationPlan(
                    diagnosis_id="rb1",
                    incident_id="rb1",
                    action=RemediationAction.RESIZE_DROPLET,
                    action_description="Test",
                    parameters={},
                    safety_checks=[],
                    rollback_plan={"description": "Good rollback", "steps": ["step1", "step2"]}
                ),
                "name": "Valid rollback plan"
            },
            {
                "plan": RemediationPlan(
                    diagnosis_id="rb2",
                    incident_id="rb2",
                    action=RemediationAction.RESIZE_DROPLET,
                    action_description="Test",
                    parameters={},
                    safety_checks=[],
                    rollback_plan=None
                ),
                "name": "No rollback plan"
            }
        ]

        for test_case in test_rollback_plans:
            can_rollback = await safety_validator.verify_rollback_possible(test_case["plan"])
            logger.info(f"  {test_case['name']}: {'✓ Can rollback' if can_rollback else '✗ Cannot rollback'}")

        logger.info("\n" + "="*60)
        logger.info("ALL TESTS COMPLETED")
        logger.info("="*60)
        logger.info("\n⚠️  Note: Full execution test skipped to avoid modifying actual infrastructure")
        logger.info("    In production, execute_remediation() would apply the changes")

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise

    finally:
        # Cleanup
        logger.info("\nClosing connections...")
        await remediation_agent.close()
        await do_mcp.close()
        terraform_mcp.cleanup()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    logger.info("Starting Remediation Agent Tests")
    logger.info("="*60)

    try:
        asyncio.run(test_remediation_agent())
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        exit(1)
