"""
Monitor Agent for Rift
Detects infrastructure anomalies and creates incident reports
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from agents.base_agent import BaseAgent
from mcp_clients.do_mcp import DigitalOceanMCP
from mcp_clients.prometheus_mcp import PrometheusMCP
from models.incident import (
    Incident,
    SeverityLevel,
    MetricType,
    ResourceType,
    IncidentStatus
)

logger = logging.getLogger("rift.agents.monitor")


class MonitorAgent(BaseAgent):
    """
    Monitor Agent for detecting infrastructure issues.
    Combines DigitalOcean droplet info with Prometheus metrics
    to detect anomalies and create incident reports.
    """

    # Default thresholds for metrics
    DEFAULT_THRESHOLDS = {
        MetricType.CPU_USAGE: 80.0,
        MetricType.MEMORY_USAGE: 85.0,
        MetricType.DISK_USAGE: 90.0
    }

    def __init__(
        self,
        agent_endpoint: str,
        agent_key: str,
        agent_id: str,
        do_mcp: DigitalOceanMCP,
        prometheus_mcp: PrometheusMCP,
        knowledge_base_id: Optional[str] = None,
        thresholds: Optional[Dict[MetricType, float]] = None
    ):
        """
        Initialize Monitor Agent.

        Args:
            agent_endpoint: Gradient AI agent endpoint URL
            agent_key: API key for authentication
            agent_id: Unique agent identifier
            do_mcp: DigitalOcean MCP client instance
            prometheus_mcp: Prometheus MCP client instance
            knowledge_base_id: Optional knowledge base ID for RAG
            thresholds: Optional custom thresholds for metrics
        """
        super().__init__(
            agent_endpoint=agent_endpoint,
            agent_key=agent_key,
            agent_id=agent_id,
            agent_name="Monitor Agent",
            knowledge_base_id=knowledge_base_id
        )

        self.do_mcp = do_mcp
        self.prometheus_mcp = prometheus_mcp
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS

        logger.info("Monitor Agent initialized with thresholds: %s", self.thresholds)

    async def check_droplet_health(
        self,
        droplet_id: int
    ) -> Optional[List[Incident]]:
        """
        Check health of a specific droplet.

        Args:
            droplet_id: Droplet ID to check

        Returns:
            List of incidents detected, or None if no issues found
        """
        try:
            # Get droplet info from DigitalOcean
            droplet = await self.do_mcp.get_droplet(droplet_id)
            droplet_name = droplet.get("name")
            # Use PUBLIC IP address - Prometheus is configured with public IPs
            # Find the public IP (type="public") from v4 networks
            v4_networks = droplet.get("networks", {}).get("v4", [])
            droplet_ip = None
            for network in v4_networks:
                if network.get("type") == "public":
                    droplet_ip = network.get("ip_address")
                    break
            
            if not droplet_ip:
                # Fallback to first IP if no public IP found
                droplet_ip = v4_networks[0].get("ip_address") if v4_networks else "unknown"
            
            instance = f"{droplet_ip}:9100"  # Node Exporter port

            logger.info(f"Checking health of droplet {droplet_id} ({droplet_name}, {droplet_ip})")

            # Get metrics from Prometheus
            metrics = await self.prometheus_mcp.get_all_metrics(instance)

            incidents = []

            # Check CPU usage
            cpu_usage = metrics.get("cpu_usage")
            if cpu_usage is not None and cpu_usage >= self.thresholds[MetricType.CPU_USAGE]:
                incident = await self._create_incident_from_metric(
                    resource_id=str(droplet_id),
                    resource_name=droplet_name,
                    metric=MetricType.CPU_USAGE,
                    current_value=cpu_usage,
                    threshold_value=self.thresholds[MetricType.CPU_USAGE],
                    droplet=droplet
                )
                incidents.append(incident)

            # Check memory usage
            memory_usage = metrics.get("memory_usage")
            if memory_usage is not None and memory_usage >= self.thresholds[MetricType.MEMORY_USAGE]:
                incident = await self._create_incident_from_metric(
                    resource_id=str(droplet_id),
                    resource_name=droplet_name,
                    metric=MetricType.MEMORY_USAGE,
                    current_value=memory_usage,
                    threshold_value=self.thresholds[MetricType.MEMORY_USAGE],
                    droplet=droplet
                )
                incidents.append(incident)

            # Check disk usage
            disk_usage = metrics.get("disk_usage")
            if disk_usage is not None and disk_usage >= self.thresholds[MetricType.DISK_USAGE]:
                incident = await self._create_incident_from_metric(
                    resource_id=str(droplet_id),
                    resource_name=droplet_name,
                    metric=MetricType.DISK_USAGE,
                    current_value=disk_usage,
                    threshold_value=self.thresholds[MetricType.DISK_USAGE],
                    droplet=droplet
                )
                incidents.append(incident)

            if incidents:
                logger.warning(f"Detected {len(incidents)} incident(s) on droplet {droplet_name}")
                return incidents
            else:
                logger.info(f"No issues detected on droplet {droplet_name}")
                return None

        except Exception as e:
            logger.error(f"Failed to check droplet {droplet_id} health: {str(e)}")
            raise

    async def check_all_infrastructure(
        self,
        tag: Optional[str] = "rift"
    ) -> List[Incident]:
        """
        Check health of all infrastructure resources.

        Args:
            tag: Optional tag to filter droplets (default: "rift")

        Returns:
            List of all detected incidents
        """
        try:
            logger.info(f"Checking all infrastructure (tag: {tag})")

            # Get all droplets with the specified tag
            droplets = await self.do_mcp.list_droplets(tag=tag)
            logger.info(f"Found {len(droplets)} droplets to monitor")

            all_incidents = []

            # Check each droplet
            for droplet in droplets:
                droplet_id = droplet.get("id")
                droplet_name = droplet.get("name")

                try:
                    incidents = await self.check_droplet_health(droplet_id)
                    if incidents:
                        all_incidents.extend(incidents)
                except Exception as e:
                    logger.error(f"Failed to check {droplet_name}: {str(e)}")
                    # Continue checking other droplets

            logger.info(f"Infrastructure check complete: {len(all_incidents)} total incident(s)")
            return all_incidents

        except Exception as e:
            logger.error(f"Failed to check infrastructure: {str(e)}")
            raise

    async def classify_severity(
        self,
        metric: MetricType,
        current_value: float,
        threshold_value: float
    ) -> SeverityLevel:
        """
        Classify incident severity based on metric and value.

        Args:
            metric: Type of metric
            current_value: Current metric value
            threshold_value: Threshold that was exceeded

        Returns:
            Severity level
        """
        try:
            # Calculate how far over threshold we are (as percentage)
            overage_percent = ((current_value - threshold_value) / threshold_value) * 100

            # Use AI to help classify severity with context
            prompt = f"""
            Classify the severity of this infrastructure metric violation:

            Metric: {metric.value}
            Current Value: {current_value:.2f}%
            Threshold: {threshold_value:.2f}%
            Overage: {overage_percent:.2f}%

            Consider:
            - How critical is this metric type?
            - How far above threshold is it?
            - What is the potential impact?

            Respond with ONLY one word: critical, high, medium, or low
            """

            response = await self.query_agent(
                prompt=prompt,
                use_knowledge_base=False  # Simple classification doesn't need KB
            )

            # Extract severity from AI response
            ai_severity = response.get("response", "").strip().lower()

            # Map AI response to SeverityLevel enum
            severity_mapping = {
                "critical": SeverityLevel.CRITICAL,
                "high": SeverityLevel.HIGH,
                "medium": SeverityLevel.MEDIUM,
                "low": SeverityLevel.LOW
            }

            severity = severity_mapping.get(ai_severity)

            # Fallback to rule-based classification if AI response is unclear
            if not severity:
                logger.warning(f"AI returned unclear severity '{ai_severity}', using rule-based fallback")

                if current_value >= 95:
                    severity = SeverityLevel.CRITICAL
                elif overage_percent >= 20:  # 20% or more over threshold
                    severity = SeverityLevel.HIGH
                elif overage_percent >= 10:  # 10-20% over threshold
                    severity = SeverityLevel.MEDIUM
                else:
                    severity = SeverityLevel.LOW

            logger.debug(f"Classified {metric.value} ({current_value:.2f}%) as {severity.value}")
            return severity

        except Exception as e:
            logger.error(f"Failed to classify severity: {str(e)}, using HIGH as default")
            return SeverityLevel.HIGH

    async def _create_incident_from_metric(
        self,
        resource_id: str,
        resource_name: str,
        metric: MetricType,
        current_value: float,
        threshold_value: float,
        droplet: Dict[str, Any]
    ) -> Incident:
        """
        Create an incident from a metric violation.

        Args:
            resource_id: Resource ID
            resource_name: Resource name
            metric: Metric type
            current_value: Current metric value
            threshold_value: Threshold value
            droplet: Full droplet info from DO API

        Returns:
            Incident object
        """
        # Classify severity
        severity = await self.classify_severity(metric, current_value, threshold_value)

        # Create description
        description = f"{metric.value.replace('_', ' ').title()} exceeded threshold on {resource_name} droplet: {current_value:.2f}% (threshold: {threshold_value:.2f}%)"

        # Create incident
        incident = Incident(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=ResourceType.DROPLET,
            metric=metric,
            current_value=current_value,
            threshold_value=threshold_value,
            severity=severity,
            status=IncidentStatus.DETECTED,
            description=description,
            metadata={
                "droplet_size": droplet.get("size", {}).get("slug"),
                "droplet_region": droplet.get("region", {}).get("slug"),
                "droplet_vcpus": droplet.get("vcpus"),
                "droplet_memory": droplet.get("memory"),
                "droplet_disk": droplet.get("disk"),
                "droplet_status": droplet.get("status"),
                "detection_method": "prometheus_metrics"
            }
        )

        logger.info(f"Created incident {incident.id}: {description} (severity: {severity.value})")
        return incident

    async def analyze_trend(
        self,
        instance: str,
        metric: MetricType,
        hours: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze metric trends over time using AI.

        Args:
            instance: Instance identifier
            metric: Metric type to analyze
            hours: Number of hours to look back

        Returns:
            Trend analysis dictionary
        """
        from datetime import timedelta

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Build PromQL query based on metric type
            if metric == MetricType.CPU_USAGE:
                query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{instance="{instance}",mode="idle"}}[5m])) * 100)'
            elif metric == MetricType.MEMORY_USAGE:
                query = f'100 * (1 - ((node_memory_MemAvailable_bytes{{instance="{instance}"}} or node_memory_MemFree_bytes{{instance="{instance}"}}) / node_memory_MemTotal_bytes{{instance="{instance}"}}))'
            elif metric == MetricType.DISK_USAGE:
                query = f'100 - ((node_filesystem_avail_bytes{{instance="{instance}",mountpoint="/"}} / node_filesystem_size_bytes{{instance="{instance}",mountpoint="/"}}) * 100)'
            else:
                raise ValueError(f"Unsupported metric type: {metric}")

            # Get range data from Prometheus
            result = await self.prometheus_mcp.query_range(
                query=query,
                start=start_time,
                end=end_time,
                step="1m"
            )

            # Use AI to analyze the trend
            prompt = f"""
            Analyze this {metric.value} trend data for infrastructure monitoring:

            Instance: {instance}
            Time Range: Last {hours} hour(s)
            Metric Data: {result}

            Provide:
            1. Trend direction (increasing, stable, decreasing)
            2. Pattern observed (spikes, sustained high, gradual increase, etc.)
            3. Predicted behavior (will it exceed thresholds soon?)
            4. Recommended action (if any)

            Be concise and actionable.
            """

            analysis = await self.query_agent(
                prompt=prompt,
                use_knowledge_base=True
            )

            return {
                "instance": instance,
                "metric": metric.value,
                "time_range_hours": hours,
                "data_points": len(result.get("result", [])),
                "analysis": analysis.get("response"),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to analyze trend: {str(e)}")
            raise
