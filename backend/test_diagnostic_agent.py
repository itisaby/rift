"""
Test script for Diagnostic Agent
Verifies the Diagnostic Agent can diagnose incidents and generate remediation plans
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from agents.diagnostic_agent import DiagnosticAgent
from mcp_clients.do_mcp import DigitalOceanMCP
from mcp_clients.terraform_mcp import TerraformMCP
from models.incident import (
    Incident,
    MetricType,
    ResourceType,
    SeverityLevel,
    IncidentStatus
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_diagnostic_agent():
    """Test Diagnostic Agent functionality"""

    # Load environment variables
    load_dotenv()

    # Initialize MCP clients
    logger.info("Initializing MCP clients...")

    do_mcp = DigitalOceanMCP(
        api_token=os.getenv("DIGITALOCEAN_API_TOKEN")
    )

    terraform_mcp = TerraformMCP(
        working_dir="/tmp/rift_terraform_test"
    )

    # Initialize Diagnostic Agent
    logger.info("Initializing Diagnostic Agent...")

    diagnostic_agent = DiagnosticAgent(
        agent_endpoint=os.getenv("DIAGNOSTIC_AGENT_ENDPOINT"),
        agent_key=os.getenv("DIAGNOSTIC_AGENT_KEY"),
        agent_id=os.getenv("DIAGNOSTIC_AGENT_ID"),
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp
    )

    try:
        # Test 1: Check agent health
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Checking Diagnostic Agent health")
        logger.info("="*60)

        health = await diagnostic_agent.check_health()
        logger.info(f"Agent health: {health}")

        # Test 2: Create a mock incident
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Creating mock incident")
        logger.info("="*60)

        # Get a real droplet for testing
        droplets = await do_mcp.list_droplets(tag="rift")
        if not droplets:
            logger.warning("No droplets found with 'rift' tag. Using mock data.")
            droplet_id = "123456"
            droplet_name = "test-droplet"
        else:
            droplet = droplets[0]
            droplet_id = str(droplet['id'])
            droplet_name = droplet['name']

        # Create a high CPU usage incident
        incident = Incident(
            resource_id=droplet_id,
            resource_name=droplet_name,
            resource_type=ResourceType.DROPLET,
            metric=MetricType.CPU_USAGE,
            current_value=95.5,
            threshold_value=80.0,
            severity=SeverityLevel.HIGH,
            status=IncidentStatus.DETECTED,
            description=f"CPU usage exceeded threshold on {droplet_name} droplet: 95.50% (threshold: 80.00%)",
            metadata={
                "droplet_size": "s-1vcpu-1gb",
                "droplet_region": "nyc3",
                "detection_method": "prometheus_metrics"
            }
        )

        logger.info(f"Created incident: {incident.id}")
        logger.info(f"  Resource: {incident.resource_name}")
        logger.info(f"  Metric: {incident.metric.value}")
        logger.info(f"  Current: {incident.current_value}%")
        logger.info(f"  Threshold: {incident.threshold_value}%")
        logger.info(f"  Severity: {incident.severity.value}")

        # Test 3: Query knowledge base
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Querying knowledge base")
        logger.info("="*60)

        kb_entries = await diagnostic_agent.query_knowledge_base(
            "high CPU usage troubleshooting droplet resize"
        )

        logger.info(f"Retrieved {len(kb_entries)} knowledge base entries:")
        for i, entry in enumerate(kb_entries, 1):
            logger.info(f"\n  Entry {i}:")
            logger.info(f"  Source: {entry.source}")
            logger.info(f"  Relevance: {entry.relevance_score:.2f}")
            logger.info(f"  Content preview: {entry.content[:200]}...")

        # Test 4: Diagnose the incident
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Diagnosing incident")
        logger.info("="*60)

        diagnosis = await diagnostic_agent.diagnose_incident(incident)

        logger.info(f"\nDiagnosis Results:")
        logger.info(f"  Diagnosis ID: {diagnosis.id}")
        logger.info(f"  Root Cause: {diagnosis.root_cause}")
        logger.info(f"  Category: {diagnosis.root_cause_category}")
        logger.info(f"  Confidence: {diagnosis.confidence:.2f} ({diagnosis.confidence * 100:.0f}%)")
        logger.info(f"  Reasoning: {diagnosis.reasoning[:200]}...")
        logger.info(f"\n  Recommendations:")
        for i, rec in enumerate(diagnosis.recommendations, 1):
            logger.info(f"    {i}. {rec}")
        logger.info(f"\n  Estimated Cost: ${diagnosis.estimated_cost:.2f}" if diagnosis.estimated_cost else "  Estimated Cost: N/A")
        logger.info(f"  Estimated Duration: {diagnosis.estimated_duration}s" if diagnosis.estimated_duration else "  Estimated Duration: N/A")
        logger.info(f"  KB Matches: {len(diagnosis.knowledge_base_matches)}")

        # Test 5: Generate remediation plan
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Generating remediation plan")
        logger.info("="*60)

        plan = await diagnostic_agent.generate_remediation_plan(diagnosis)

        logger.info(f"\nRemediation Plan:")
        logger.info(f"  Plan ID: {plan.id}")
        logger.info(f"  Action: {plan.action.value}")
        logger.info(f"  Description: {plan.action_description[:200]}...")
        logger.info(f"  Requires Approval: {plan.requires_approval}")
        logger.info(f"  Estimated Cost: ${plan.estimated_cost:.2f}" if plan.estimated_cost else "  Estimated Cost: N/A")
        logger.info(f"  Estimated Duration: {plan.estimated_duration}s" if plan.estimated_duration else "  Estimated Duration: N/A")
        logger.info(f"\n  Parameters:")
        for key, value in plan.parameters.items():
            logger.info(f"    {key}: {value}")
        logger.info(f"\n  Safety Checks:")
        for check in plan.safety_checks:
            logger.info(f"    - {check}")

        # Test 6: Test confidence scoring with different scenarios
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Testing confidence scoring")
        logger.info("="*60)

        test_scenarios = [
            {
                "name": "High confidence (good KB matches, complete state)",
                "kb_matches": kb_entries,
                "state_analysis": {"resource_type": "droplet", "current_size": "s-1vcpu-1gb", "affected_metric": "cpu"},
                "diagnosis_text": "This is definitely a capacity issue. The droplet is clearly undersized."
            },
            {
                "name": "Medium confidence (no KB matches, complete state)",
                "kb_matches": [],
                "state_analysis": {"resource_type": "droplet", "current_size": "s-1vcpu-1gb", "affected_metric": "cpu"},
                "diagnosis_text": "This might be a capacity issue. Further investigation needed."
            },
            {
                "name": "Low confidence (no KB matches, incomplete state)",
                "kb_matches": [],
                "state_analysis": {"resource_type": "droplet"},
                "diagnosis_text": "Unclear what the issue might be. Possibly related to usage patterns."
            }
        ]

        for scenario in test_scenarios:
            confidence = await diagnostic_agent.calculate_confidence(
                kb_matches=scenario["kb_matches"],
                state_analysis=scenario["state_analysis"],
                diagnosis_text=scenario["diagnosis_text"]
            )
            logger.info(f"  {scenario['name']}: {confidence:.2f} ({confidence * 100:.0f}%)")

        logger.info("\n" + "="*60)
        logger.info("ALL TESTS COMPLETED")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise

    finally:
        # Cleanup
        logger.info("\nClosing connections...")
        await diagnostic_agent.close()
        await do_mcp.close()
        terraform_mcp.cleanup()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    logger.info("Starting Diagnostic Agent Tests")
    logger.info("="*60)

    try:
        asyncio.run(test_diagnostic_agent())
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        exit(1)
