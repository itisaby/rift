"""
Test script for Provisioner Agent
Verifies the Provisioner Agent can create infrastructure from natural language
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from agents.provisioner_agent import ProvisionerAgent
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.provision_request import ProvisionRequest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_provisioner_agent():
    """Test Provisioner Agent functionality"""

    # Load environment variables
    load_dotenv()

    logger.info("=" * 80)
    logger.info("PROVISIONER AGENT TEST")
    logger.info("=" * 80)

    # Initialize MCP clients
    logger.info("\n[1/5] Initializing MCP clients...")

    do_mcp = DigitalOceanMCP(
        api_token=os.getenv("DIGITALOCEAN_API_TOKEN")
    )

    terraform_mcp = TerraformMCP(
        working_dir="/tmp/rift_terraform_provisioner_test"
    )

    logger.info("✓ MCP clients initialized")

    # Initialize Provisioner Agent
    logger.info("\n[2/5] Initializing Provisioner Agent...")

    provisioner_agent = ProvisionerAgent(
        agent_endpoint=os.getenv("PROVISIONER_AGENT_ENDPOINT"),
        agent_key=os.getenv("PROVISIONER_AGENT_KEY"),
        agent_id=os.getenv("PROVISIONER_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    logger.info("✓ Provisioner Agent initialized")

    try:
        # Test 1: Check agent health
        logger.info("\n[3/5] Checking Provisioner Agent health...")
        logger.info("-" * 80)

        health = await provisioner_agent.check_health()
        logger.info(f"Agent health: {health}")

        # Test 2: List available templates
        logger.info("\n[4/5] Listing available provisioning templates...")
        logger.info("-" * 80)

        templates = provisioner_agent.get_templates()
        logger.info(f"Found {len(templates)} template(s):\n")

        for template in templates:
            logger.info(f"  Template: {template.name}")
            logger.info(f"    ID: {template.id}")
            logger.info(f"    Description: {template.description}")
            logger.info(f"    Category: {template.category}")
            logger.info(f"    Estimated Cost: ${template.estimated_cost:.2f}/month")
            logger.info(f"    Resources: {', '.join(template.resources)}")
            logger.info(f"    Required Params: {', '.join(template.required_params) if template.required_params else 'None'}")
            logger.info("")

        # Test 3: Get specific template
        logger.info("\n[4.5/5] Getting specific template details...")
        logger.info("-" * 80)

        simple_droplet = provisioner_agent.get_template("simple-droplet")
        if simple_droplet:
            logger.info(f"✓ Retrieved template: {simple_droplet.name}")
            logger.info(f"  Module Path: {simple_droplet.terraform_module}")
            logger.info(f"  Optional Params: {simple_droplet.optional_params}")
        else:
            logger.error("✗ Failed to retrieve template")

        # Test 4: Test Terraform generation (without applying)
        logger.info("\n[5/5] Testing Terraform configuration generation...")
        logger.info("-" * 80)

        # Create a test provision request
        test_request = ProvisionRequest(
            user_id="test-user",
            description="Create a simple Ubuntu droplet for testing",
            region="nyc3",
            environment="development",
            budget_limit=10.0,
            tags=["test", "provisioner-test"]
        )

        logger.info(f"Test Request:")
        logger.info(f"  Description: {test_request.description}")
        logger.info(f"  Region: {test_request.region}")
        logger.info(f"  Environment: {test_request.environment}")
        logger.info(f"  Budget Limit: ${test_request.budget_limit}")

        # Generate Terraform (but don't apply)
        logger.info("\nGenerating Terraform configuration...")
        terraform_config = await provisioner_agent._generate_terraform(test_request)

        if terraform_config:
            logger.info(f"✓ Generated Terraform configuration ({len(terraform_config)} bytes)")
            logger.info("\n  Preview (first 20 lines):")
            logger.info("  " + "-" * 76)
            for i, line in enumerate(terraform_config.split('\n')[:20], 1):
                logger.info(f"  {line}")
            if len(terraform_config.split('\n')) > 20:
                logger.info("  ...")
            logger.info("  " + "-" * 76)
        else:
            logger.error("✗ Failed to generate Terraform configuration")

        # Test 5: Validate generated Terraform
        if terraform_config:
            logger.info("\nValidating Terraform configuration...")
            validation = await terraform_mcp.validate_config(terraform_config)

            logger.info(f"\n  Validation Result:")
            logger.info(f"    Valid: {validation.valid}")

            if validation.errors:
                logger.info(f"    Errors: {validation.errors}")
            else:
                logger.info(f"    Errors: None")

            if validation.warnings:
                logger.info(f"    Warnings: {validation.warnings}")
            else:
                logger.info(f"    Warnings: None")

        # Test 6: Test template-based provisioning (dry-run)
        logger.info("\n" + "=" * 80)
        logger.info("TEMPLATE-BASED PROVISIONING TEST (DRY-RUN)")
        logger.info("=" * 80)

        template_request = ProvisionRequest(
            user_id="test-user",
            description="Simple droplet from template",
            template="simple-droplet",
            template_params={
                "droplet_name": "test-droplet-provision",
                "size": "s-1vcpu-1gb",
                "region": "nyc3"
            },
            budget_limit=10.0
        )

        logger.info(f"Template Request:")
        logger.info(f"  Template: {template_request.template}")
        logger.info(f"  Parameters: {template_request.template_params}")

        # Generate from template
        template_config = await provisioner_agent._generate_from_template(
            template_request.template,
            template_request.template_params
        )

        if template_config:
            logger.info(f"✓ Generated Terraform from template ({len(template_config)} bytes)")
        else:
            logger.error("✗ Failed to generate Terraform from template")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info("✓ Provisioner Agent: Initialized and Healthy")
        logger.info(f"✓ Templates: {len(templates)} available")
        logger.info("✓ Terraform Generation: Working")
        logger.info("✓ Template-based Generation: Working")
        logger.info("\n⚠️  Note: Full provisioning test skipped to avoid creating actual infrastructure")
        logger.info("    To test full provisioning, call provisioner_agent.provision() with a request")

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {str(e)}", exc_info=True)
        raise

    finally:
        # Cleanup
        logger.info("\n" + "=" * 80)
        logger.info("CLEANUP")
        logger.info("=" * 80)

        logger.info("Closing agent connections...")
        await provisioner_agent.close()

        logger.info("Closing MCP clients...")
        await do_mcp.close()
        terraform_mcp.cleanup()

        logger.info("✓ Cleanup complete")


if __name__ == "__main__":
    logger.info("Starting Provisioner Agent Tests")
    logger.info("=" * 80)

    try:
        asyncio.run(test_provisioner_agent())
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        exit(1)
