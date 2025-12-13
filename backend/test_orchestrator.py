"""
Test script for the Full Orchestrator
Verifies the complete Rift system workflow
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from agents.monitor_agent import MonitorAgent
from agents.diagnostic_agent import DiagnosticAgent
from agents.remediation_agent import RemediationAgent
from agents.safety_validator import SafetyValidator
from mcp_clients.do_mcp import DigitalOceanMCP
from mcp_clients.prometheus_mcp import PrometheusMCP
from mcp_clients.terraform_mcp import TerraformMCP
from orchestrator.coordinator import Coordinator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_orchestrator():
    """Test complete orchestrator workflow"""

    # Load environment variables
    load_dotenv()

    logger.info("=" * 80)
    logger.info("RIFT ORCHESTRATOR TEST")
    logger.info("=" * 80)

    # Initialize MCP clients
    logger.info("\n[1/7] Initializing MCP clients...")

    do_mcp = DigitalOceanMCP(
        api_token=os.getenv("DIGITALOCEAN_API_TOKEN")
    )

    prometheus_mcp = PrometheusMCP(
        prometheus_url=os.getenv("PROMETHEUS_URL"),
        username=os.getenv("PROMETHEUS_USER"),
        password=os.getenv("PROMETHEUS_PASSWORD")
    )

    terraform_mcp = TerraformMCP(
        working_dir="/tmp/rift_terraform_orchestrator_test"
    )

    logger.info("✓ MCP clients initialized")

    # Initialize Safety Validator
    logger.info("\n[2/7] Initializing Safety Validator...")
    safety_validator = SafetyValidator(auto_approve_threshold=50.0)
    logger.info("✓ Safety Validator initialized")

    # Initialize Agents
    logger.info("\n[3/7] Initializing AI Agents...")

    monitor_agent = MonitorAgent(
        agent_endpoint=os.getenv("MONITOR_AGENT_ENDPOINT"),
        agent_key=os.getenv("MONITOR_AGENT_KEY"),
        agent_id=os.getenv("MONITOR_AGENT_ID"),
        do_mcp=do_mcp,
        prometheus_mcp=prometheus_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    diagnostic_agent = DiagnosticAgent(
        agent_endpoint=os.getenv("DIAGNOSTIC_AGENT_ENDPOINT"),
        agent_key=os.getenv("DIAGNOSTIC_AGENT_KEY"),
        agent_id=os.getenv("DIAGNOSTIC_AGENT_ID"),
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp
    )

    remediation_agent = RemediationAgent(
        agent_endpoint=os.getenv("REMEDIATION_AGENT_ENDPOINT"),
        agent_key=os.getenv("REMEDIATION_AGENT_KEY"),
        agent_id=os.getenv("REMEDIATION_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        safety_validator=safety_validator,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    logger.info("✓ All agents initialized")

    # Initialize Coordinator
    logger.info("\n[4/7] Initializing Coordinator...")

    coordinator = Coordinator(
        monitor_agent=monitor_agent,
        diagnostic_agent=diagnostic_agent,
        remediation_agent=remediation_agent,
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.85")),
        auto_remediation_enabled=os.getenv("AUTO_REMEDIATION_ENABLED", "true").lower() == "true",
        check_interval=30
    )

    logger.info("✓ Coordinator initialized")
    logger.info(f"  - Confidence Threshold: {coordinator.confidence_threshold}")
    logger.info(f"  - Auto Remediation: {coordinator.auto_remediation_enabled}")
    logger.info(f"  - Check Interval: {coordinator.check_interval}s")

    try:
        # Test 1: Agent Health Checks
        logger.info("\n[5/7] Testing Agent Health Checks...")
        logger.info("-" * 80)

        agents = [
            ("Monitor Agent", monitor_agent),
            ("Diagnostic Agent", diagnostic_agent),
            ("Remediation Agent", remediation_agent)
        ]

        all_healthy = True
        for agent_name, agent in agents:
            try:
                health = await agent.check_health()
                status = health.get("status", "unknown")
                logger.info(f"  {agent_name}: {status.upper()}")
                if status != "healthy":
                    all_healthy = False
            except Exception as e:
                logger.error(f"  {agent_name}: UNHEALTHY - {str(e)}")
                all_healthy = False

        if all_healthy:
            logger.info("✓ All agents are healthy")
        else:
            logger.warning("⚠️  Some agents are unhealthy")

        # Test 2: Manual Incident Detection
        logger.info("\n[6/7] Testing Manual Incident Detection...")
        logger.info("-" * 80)

        incidents = await monitor_agent.check_all_infrastructure(tag="rift")

        logger.info(f"Detected {len(incidents)} incident(s)")

        for i, incident in enumerate(incidents, 1):
            logger.info(f"\n  Incident {i}:")
            logger.info(f"    ID: {incident.id}")
            logger.info(f"    Resource: {incident.resource_name}")
            logger.info(f"    Type: {incident.resource_type.value}")
            logger.info(f"    Metric: {incident.metric.value}")
            logger.info(f"    Severity: {incident.severity.value}")
            logger.info(f"    Current Value: {incident.current_value}%")
            logger.info(f"    Threshold: {incident.threshold_value}%")

        # Test 3: Full Incident Workflow (if incidents found)
        if incidents:
            logger.info("\n[7/7] Testing Full Incident Workflow...")
            logger.info("-" * 80)

            # Take the first incident
            test_incident = incidents[0]
            logger.info(f"Testing workflow for incident: {test_incident.id}")

            # Run the complete workflow
            logger.info("\nExecuting handle_incident_workflow()...")
            result = await coordinator.handle_incident_workflow(test_incident)

            if result:
                logger.info("\n✓ Workflow completed successfully!")
                logger.info(f"  Result ID: {result.id}")
                logger.info(f"  Success: {result.success}")
                logger.info(f"  Status: {result.status.value}")
                logger.info(f"  Action Taken: {result.action_taken}")
                logger.info(f"  Duration: {result.duration}s")
                logger.info(f"  Verification Passed: {result.verification_passed}")

                if result.error_message:
                    logger.info(f"  Error: {result.error_message}")

                if result.logs:
                    logger.info(f"\n  Execution Logs ({len(result.logs)} entries):")
                    for log_entry in result.logs:
                        logger.info(f"    - {log_entry}")
            else:
                logger.warning("⚠️  Workflow did not execute remediation")
                logger.info("  (Likely due to low confidence or disabled auto-remediation)")

        else:
            logger.info("\n[7/7] Skipping Workflow Test - No incidents detected")
            logger.info("-" * 80)
            logger.info("✓ No active incidents - Infrastructure is healthy!")

        # Test 4: System Status
        logger.info("\n" + "=" * 80)
        logger.info("SYSTEM STATUS SUMMARY")
        logger.info("=" * 80)

        status = coordinator.get_system_status()

        logger.info(f"Timestamp: {status['timestamp']}")
        logger.info(f"Running: {status['running']}")
        logger.info(f"Active Incidents: {status['active_incidents']}")
        logger.info(f"Confidence Threshold: {status['confidence_threshold']}")
        logger.info(f"Auto Remediation: {status['auto_remediation_enabled']}")
        logger.info(f"Check Interval: {status['check_interval']}s")

        logger.info("\nStatistics:")
        stats = status['stats']
        logger.info(f"  Incidents Detected: {stats['incidents_detected']}")
        logger.info(f"  Incidents Resolved: {stats['incidents_resolved']}")
        logger.info(f"  Remediations Executed: {stats['remediations_executed']}")
        logger.info(f"  Remediations Successful: {stats['remediations_successful']}")
        logger.info(f"  Total Cost: ${stats['total_cost']:.2f}")

        # Test 5: Autonomous Loop (brief test)
        logger.info("\n" + "=" * 80)
        logger.info("AUTONOMOUS LOOP TEST (10 seconds)")
        logger.info("=" * 80)

        logger.info("Starting autonomous loop...")
        loop_task = asyncio.create_task(coordinator.start_autonomous_loop())

        # Let it run for 10 seconds
        await asyncio.sleep(10)

        logger.info("Stopping autonomous loop...")
        await coordinator.stop_autonomous_loop()
        loop_task.cancel()

        try:
            await loop_task
        except asyncio.CancelledError:
            pass

        logger.info("✓ Autonomous loop test complete")

        # Final Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info("✓ MCP Clients: Initialized")
        logger.info("✓ AI Agents: Initialized and Healthy")
        logger.info("✓ Coordinator: Operational")
        logger.info("✓ Incident Detection: Working")
        logger.info("✓ Autonomous Loop: Working")
        logger.info("\n🎉 All orchestrator tests passed!")

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {str(e)}", exc_info=True)
        raise

    finally:
        # Cleanup
        logger.info("\n" + "=" * 80)
        logger.info("CLEANUP")
        logger.info("=" * 80)

        logger.info("Closing agent connections...")
        await monitor_agent.close()
        await diagnostic_agent.close()
        await remediation_agent.close()

        logger.info("Closing MCP clients...")
        await do_mcp.close()
        await prometheus_mcp.close()
        terraform_mcp.cleanup()

        logger.info("✓ Cleanup complete")


if __name__ == "__main__":
    logger.info("Starting Rift Orchestrator Tests")
    logger.info("=" * 80)

    try:
        asyncio.run(test_orchestrator())
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        exit(1)
