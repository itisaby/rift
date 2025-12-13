"""
Prometheus MCP Client
Interfaces with Prometheus for metrics collection and querying
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from urllib.parse import quote

logger = logging.getLogger("rift.mcp.prometheus")


class PrometheusMCP:
    """
    Client for interacting with Prometheus API.
    Provides methods for querying metrics and checking thresholds.
    """

    def __init__(
        self,
        prometheus_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Prometheus MCP client.

        Args:
            prometheus_url: Prometheus server URL (e.g., http://localhost:9090)
            username: Optional basic auth username
            password: Optional basic auth password
        """
        if not prometheus_url:
            prometheus_url = "http://localhost:9090"
            logger.warning("No Prometheus URL provided, using default: http://localhost:9090")
        
        self.prometheus_url = prometheus_url.rstrip("/")
        self.api_url = f"{self.prometheus_url}/api/v1"

        headers = {"Content-Type": "application/json"}

        # Set up auth if provided
        auth = None
        if username and password:
            auth = httpx.BasicAuth(username, password)

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=headers,
            auth=auth
        )

        logger.info(f"Prometheus MCP client initialized: {prometheus_url}")

    async def query_instant(
        self,
        query: str,
        time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Execute an instant Prometheus query.

        Args:
            query: PromQL query string
            time: Optional timestamp for query (defaults to now)

        Returns:
            Query result dictionary
        """
        try:
            url = f"{self.api_url}/query"

            params = {"query": query}
            if time:
                params["time"] = time.timestamp()

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Query failed: {data.get('error')}")

            logger.debug(f"Instant query executed: {query}")
            return data.get("data", {})

        except Exception as e:
            logger.error(f"Instant query failed: {str(e)}")
            raise

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "15s"
    ) -> Dict[str, Any]:
        """
        Execute a range Prometheus query.

        Args:
            query: PromQL query string
            start: Start time
            end: End time
            step: Query resolution step (e.g., '15s', '1m')

        Returns:
            Query result dictionary
        """
        try:
            url = f"{self.api_url}/query_range"

            params = {
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Query failed: {data.get('error')}")

            logger.debug(f"Range query executed: {query}")
            return data.get("data", {})

        except Exception as e:
            logger.error(f"Range query failed: {str(e)}")
            raise

    async def get_cpu_usage(self, instance: str) -> Optional[float]:
        """
        Get current CPU usage for an instance.

        Args:
            instance: Instance identifier (e.g., 'web-app:9100')

        Returns:
            CPU usage percentage (0-100) or None if not available
        """
        try:
            # Query for CPU usage (1 - idle)
            query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{instance="{instance}",mode="idle"}}[5m])) * 100)'

            result = await self.query_instant(query)

            if result.get("resultType") == "vector" and result.get("result"):
                value = float(result["result"][0]["value"][1])
                logger.info(f"CPU usage for {instance}: {value:.2f}%")
                return value

            logger.warning(f"No CPU data for {instance}")
            return None

        except Exception as e:
            logger.error(f"Failed to get CPU usage for {instance}: {str(e)}")
            return None

    async def get_memory_usage(self, instance: str) -> Optional[float]:
        """
        Get current memory usage for an instance.

        Args:
            instance: Instance identifier

        Returns:
            Memory usage percentage (0-100) or None if not available
        """
        try:
            # Query for memory usage
            query = f'100 * (1 - ((node_memory_MemAvailable_bytes{{instance="{instance}"}} or node_memory_MemFree_bytes{{instance="{instance}"}}) / node_memory_MemTotal_bytes{{instance="{instance}"}}))'

            result = await self.query_instant(query)

            if result.get("resultType") == "vector" and result.get("result"):
                value = float(result["result"][0]["value"][1])
                logger.info(f"Memory usage for {instance}: {value:.2f}%")
                return value

            logger.warning(f"No memory data for {instance}")
            return None

        except Exception as e:
            logger.error(f"Failed to get memory usage for {instance}: {str(e)}")
            return None

    async def get_disk_usage(self, instance: str, mountpoint: str = "/") -> Optional[float]:
        """
        Get current disk usage for an instance.

        Args:
            instance: Instance identifier
            mountpoint: Filesystem mountpoint (default: /)

        Returns:
            Disk usage percentage (0-100) or None if not available
        """
        try:
            # Query for disk usage
            query = f'100 - ((node_filesystem_avail_bytes{{instance="{instance}",mountpoint="{mountpoint}"}} / node_filesystem_size_bytes{{instance="{instance}",mountpoint="{mountpoint}"}}) * 100)'

            result = await self.query_instant(query)

            if result.get("resultType") == "vector" and result.get("result"):
                value = float(result["result"][0]["value"][1])
                logger.info(f"Disk usage for {instance}:{mountpoint}: {value:.2f}%")
                return value

            logger.warning(f"No disk data for {instance}:{mountpoint}")
            return None

        except Exception as e:
            logger.error(f"Failed to get disk usage for {instance}: {str(e)}")
            return None

    async def get_all_metrics(self, instance: str) -> Dict[str, Optional[float]]:
        """
        Get all common metrics for an instance.

        Args:
            instance: Instance identifier

        Returns:
            Dictionary with cpu, memory, and disk usage
        """
        try:
            metrics = {
                "instance": instance,
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_usage": await self.get_cpu_usage(instance),
                "memory_usage": await self.get_memory_usage(instance),
                "disk_usage": await self.get_disk_usage(instance)
            }

            logger.info(f"Retrieved all metrics for {instance}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to get metrics for {instance}: {str(e)}")
            raise

    async def check_threshold(
        self,
        instance: str,
        metric_type: str,
        threshold: float
    ) -> bool:
        """
        Check if a metric exceeds a threshold.

        Args:
            instance: Instance identifier
            metric_type: Type of metric ('cpu', 'memory', 'disk')
            threshold: Threshold value (0-100)

        Returns:
            True if metric exceeds threshold, False otherwise
        """
        try:
            if metric_type == "cpu":
                value = await self.get_cpu_usage(instance)
            elif metric_type == "memory":
                value = await self.get_memory_usage(instance)
            elif metric_type == "disk":
                value = await self.get_disk_usage(instance)
            else:
                raise ValueError(f"Unknown metric type: {metric_type}")

            if value is None:
                logger.warning(f"No data for {metric_type} on {instance}, assuming threshold not exceeded")
                return False

            exceeds = value >= threshold
            if exceeds:
                logger.warning(f"{metric_type.upper()} threshold exceeded: {value:.2f}% >= {threshold}%")
            else:
                logger.debug(f"{metric_type.upper()} within threshold: {value:.2f}% < {threshold}%")

            return exceeds

        except Exception as e:
            logger.error(f"Failed to check threshold: {str(e)}")
            return False

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active alerts from Prometheus.

        Returns:
            List of active alerts
        """
        try:
            url = f"{self.api_url}/alerts"

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise Exception(f"Failed to get alerts: {data.get('error')}")

            alerts = data.get("data", {}).get("alerts", [])
            logger.info(f"Retrieved {len(alerts)} active alerts")

            return alerts

        except Exception as e:
            logger.error(f"Failed to get alerts: {str(e)}")
            return []

    async def check_health(self) -> bool:
        """
        Check Prometheus server health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.prometheus_url}/-/healthy"

            response = await self.client.get(url)
            response.raise_for_status()

            logger.info("Prometheus is healthy")
            return True

        except Exception as e:
            logger.error(f"Prometheus health check failed: {str(e)}")
            return False

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
        logger.info("Prometheus MCP client closed")
