"""
Test script for Monitor Agent
Verifies the Monitor Agent can detect infrastructure issues
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from agents.monitor_agent import MonitorAgent
from mcp_clients.do_mcp import DigitalOceanMCP
from mcp_clients.prometheus_mcp import PrometheusMCP
from models.incident import MetricType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_monitor_agent():
    """Test Monitor Agent functionality"""

    # Load environment variables
    load_dotenv()

    # Initialize MCP clients
    logger.info("Initializing MCP clients...")

    do_mcp = DigitalOceanMCP(
        api_token=os.getenv("DIGITALOCEAN_API_TOKEN")
    )

    prometheus_mcp = PrometheusMCP(
        prometheus_url=os.getenv("PROMETHEUS_URL"),
        username=os.getenv("PROMETHEUS_USER"),
        password=os.getenv("PROMETHEUS_PASSWORD")
    )

    # Initialize Monitor Agent
    logger.info("Initializing Monitor Agent...")

    monitor_agent = MonitorAgent(
        agent_endpoint=os.getenv("MONITOR_AGENT_ENDPOINT"),
        agent_key=os.getenv("MONITOR_AGENT_KEY"),
        agent_id=os.getenv("MONITOR_AGENT_ID"),
        do_mcp=do_mcp,
        prometheus_mcp=prometheus_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )

    try:
        # Test 1: Check agent health
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Checking Monitor Agent health")
        logger.info("="*60)

        health = await monitor_agent.check_health()
        logger.info(f"Agent health: {health}")

        # Test 2: Check Prometheus health
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Checking Prometheus connectivity")
        logger.info("="*60)

        prom_healthy = await prometheus_mcp.check_health()
        logger.info(f"Prometheus healthy: {prom_healthy}")

        # Test 3: List droplets
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Listing DigitalOcean droplets")
        logger.info("="*60)

        droplets = await do_mcp.list_droplets(tag="rift")
        logger.info(f"Found {len(droplets)} droplets with 'rift' tag:")
        for droplet in droplets:
            logger.info(f"  - {droplet['name']} (ID: {droplet['id']}, Status: {droplet['status']})")

        # Test 4: Get metrics for first droplet
        if droplets:
            logger.info("\n" + "="*60)
            logger.info("TEST 4: Getting metrics for first droplet")
            logger.info("="*60)

            droplet = droplets[0]
            droplet_name = droplet['name']
            instance = f"{droplet_name}:9100"

            logger.info(f"Getting metrics for {instance}...")

            try:
                metrics = await prometheus_mcp.get_all_metrics(instance)
                logger.info(f"Metrics for {droplet_name}:")
                logger.info(f"  CPU Usage: {metrics.get('cpu_usage'):.2f}%" if metrics.get('cpu_usage') else "  CPU Usage: N/A")
                logger.info(f"  Memory Usage: {metrics.get('memory_usage'):.2f}%" if metrics.get('memory_usage') else "  Memory Usage: N/A")
                logger.info(f"  Disk Usage: {metrics.get('disk_usage'):.2f}%" if metrics.get('disk_usage') else "  Disk Usage: N/A")
            except Exception as e:
                logger.warning(f"Failed to get metrics (this is normal if Node Exporter isn't installed): {str(e)}")

        # Test 5: Check infrastructure health
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Running full infrastructure health check")
        logger.info("="*60)

        try:
            incidents = await monitor_agent.check_all_infrastructure(tag="rift")

            if incidents:
                logger.warning(f"DETECTED {len(incidents)} INCIDENT(S):")
                for incident in incidents:
                    logger.warning(f"\n  Incident ID: {incident.id}")
                    logger.warning(f"  Resource: {incident.resource_name} ({incident.resource_id})")
                    logger.warning(f"  Metric: {incident.metric.value}")
                    logger.warning(f"  Value: {incident.current_value:.2f}% (threshold: {incident.threshold_value:.2f}%)")
                    logger.warning(f"  Severity: {incident.severity.value.upper()}")
                    logger.warning(f"  Description: {incident.description}")
            else:
                logger.info("✅ No incidents detected - all systems healthy!")

        except Exception as e:
            logger.warning(f"Infrastructure check failed (expected if Node Exporters not installed): {str(e)}")

        # Test 6: Test severity classification
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Testing severity classification")
        logger.info("="*60)

        test_cases = [
            (MetricType.CPU_USAGE, 85.0, 80.0, "Slightly over threshold"),
            (MetricType.CPU_USAGE, 95.0, 80.0, "Significantly over threshold"),
            (MetricType.MEMORY_USAGE, 98.0, 85.0, "Near max capacity"),
            (MetricType.DISK_USAGE, 92.0, 90.0, "Just over threshold"),
        ]

        for metric, current, threshold, description in test_cases:
            severity = await monitor_agent.classify_severity(metric, current, threshold)
            logger.info(f"  {description}: {metric.value} @ {current}% → {severity.value.upper()}")

        logger.info("\n" + "="*60)
        logger.info("ALL TESTS COMPLETED")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise

    finally:
        # Cleanup
        logger.info("\nClosing connections...")
        await monitor_agent.close()
        await do_mcp.close()
        await prometheus_mcp.close()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    logger.info("Starting Monitor Agent Tests")
    logger.info("="*60)

    try:
        asyncio.run(test_monitor_agent())
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Tests failed: {str(e)}")
        exit(1)
