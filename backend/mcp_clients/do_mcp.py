"""
DigitalOcean MCP Client
Interfaces with DigitalOcean API for infrastructure operations
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("rift.mcp.digitalocean")


class DigitalOceanMCP:
    """
    Client for interacting with DigitalOcean API.
    Provides methods for droplet management and monitoring.
    """

    def __init__(self, api_token: str):
        """
        Initialize DigitalOcean MCP client.

        Args:
            api_token: DigitalOcean API token
        """
        self.api_token = api_token
        self.base_url = "https://api.digitalocean.com/v2"

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
        )

        logger.info("DigitalOcean MCP client initialized")

    async def list_droplets(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all droplets, optionally filtered by tag.

        Args:
            tag: Optional tag to filter droplets

        Returns:
            List of droplet dictionaries
        """
        try:
            url = f"{self.base_url}/droplets"
            params = {}

            if tag:
                params["tag_name"] = tag

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            droplets = data.get("droplets", [])

            logger.info(f"Retrieved {len(droplets)} droplets")
            return droplets

        except Exception as e:
            logger.error(f"Failed to list droplets: {str(e)}")
            raise

    async def get_droplet(self, droplet_id: int) -> Dict[str, Any]:
        """
        Get details for a specific droplet.

        Args:
            droplet_id: Droplet ID

        Returns:
            Droplet details dictionary
        """
        try:
            url = f"{self.base_url}/droplets/{droplet_id}"
            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            droplet = data.get("droplet", {})

            logger.info(f"Retrieved droplet {droplet_id}: {droplet.get('name')}")
            return droplet

        except Exception as e:
            logger.error(f"Failed to get droplet {droplet_id}: {str(e)}")
            raise

    async def get_droplet_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get droplet by name.

        Args:
            name: Droplet name

        Returns:
            Droplet dictionary or None if not found
        """
        try:
            droplets = await self.list_droplets()

            for droplet in droplets:
                if droplet.get("name") == name:
                    logger.info(f"Found droplet '{name}' (ID: {droplet['id']})")
                    return droplet

            logger.warning(f"Droplet '{name}' not found")
            return None

        except Exception as e:
            logger.error(f"Failed to get droplet by name '{name}': {str(e)}")
            raise

    async def get_droplet_metrics(
        self,
        droplet_id: int,
        metric_type: str = "cpu"
    ) -> Dict[str, Any]:
        """
        Get droplet metrics from DigitalOcean monitoring.

        Note: DigitalOcean metrics have limited granularity.
        For detailed metrics, use Prometheus.

        Args:
            droplet_id: Droplet ID
            metric_type: Type of metric (cpu, memory, disk, etc.)

        Returns:
            Metrics data dictionary
        """
        try:
            # Note: DO API doesn't provide real-time metrics endpoint
            # This is a placeholder for droplet monitoring info
            # Real metrics should come from Prometheus

            droplet = await self.get_droplet(droplet_id)

            # Return basic monitoring status
            metrics = {
                "droplet_id": droplet_id,
                "name": droplet.get("name"),
                "status": droplet.get("status"),
                "monitoring_enabled": droplet.get("features", []) and "monitoring" in droplet.get("features", []),
                "timestamp": datetime.utcnow().isoformat(),
                "note": "For detailed metrics, use Prometheus MCP client"
            }

            logger.info(f"Retrieved metrics info for droplet {droplet_id}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to get metrics for droplet {droplet_id}: {str(e)}")
            raise

    async def resize_droplet(
        self,
        droplet_id: int,
        new_size: str,
        disk: bool = True
    ) -> Dict[str, Any]:
        """
        Resize a droplet.

        Args:
            droplet_id: Droplet ID
            new_size: New size slug (e.g., 's-2vcpu-4gb')
            disk: Whether to resize disk (irreversible if True)

        Returns:
            Action result dictionary
        """
        try:
            url = f"{self.base_url}/droplets/{droplet_id}/actions"

            payload = {
                "type": "resize",
                "size": new_size,
                "disk": disk
            }

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            action = data.get("action", {})

            logger.info(f"Initiated resize for droplet {droplet_id} to {new_size}")
            return action

        except Exception as e:
            logger.error(f"Failed to resize droplet {droplet_id}: {str(e)}")
            raise

    async def reboot_droplet(self, droplet_id: int) -> Dict[str, Any]:
        """
        Reboot a droplet.

        Args:
            droplet_id: Droplet ID

        Returns:
            Action result dictionary
        """
        try:
            url = f"{self.base_url}/droplets/{droplet_id}/actions"

            payload = {"type": "reboot"}

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            action = data.get("action", {})

            logger.info(f"Initiated reboot for droplet {droplet_id}")
            return action

        except Exception as e:
            logger.error(f"Failed to reboot droplet {droplet_id}: {str(e)}")
            raise

    async def power_cycle_droplet(self, droplet_id: int) -> Dict[str, Any]:
        """
        Power cycle a droplet (hard reboot).

        Args:
            droplet_id: Droplet ID

        Returns:
            Action result dictionary
        """
        try:
            url = f"{self.base_url}/droplets/{droplet_id}/actions"

            payload = {"type": "power_cycle"}

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            action = data.get("action", {})

            logger.info(f"Initiated power cycle for droplet {droplet_id}")
            return action

        except Exception as e:
            logger.error(f"Failed to power cycle droplet {droplet_id}: {str(e)}")
            raise

    async def get_action_status(self, droplet_id: int, action_id: int) -> Dict[str, Any]:
        """
        Get status of a droplet action.

        Args:
            droplet_id: Droplet ID
            action_id: Action ID

        Returns:
            Action status dictionary
        """
        try:
            url = f"{self.base_url}/droplets/{droplet_id}/actions/{action_id}"

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            action = data.get("action", {})

            logger.info(f"Retrieved action {action_id} status: {action.get('status')}")
            return action

        except Exception as e:
            logger.error(f"Failed to get action status: {str(e)}")
            raise

    async def wait_for_action(
        self,
        droplet_id: int,
        action_id: int,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for a droplet action to complete.

        Args:
            droplet_id: Droplet ID
            action_id: Action ID
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            True if action completed successfully, False otherwise
        """
        import asyncio

        elapsed = 0

        while elapsed < timeout:
            action = await self.get_action_status(droplet_id, action_id)
            status = action.get("status")

            if status == "completed":
                logger.info(f"Action {action_id} completed successfully")
                return True
            elif status == "errored":
                logger.error(f"Action {action_id} failed")
                return False

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning(f"Action {action_id} timed out after {timeout}s")
        return False

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
        logger.info("DigitalOcean MCP client closed")
