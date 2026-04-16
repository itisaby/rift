"""
DigitalOcean MCP Server
Real MCP server for DigitalOcean API operations over stdio transport
"""

import asyncio
import json
import logging
import os

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger("rift.mcp_servers.do")

server = Server("do")

API_TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN", "")
BASE_URL = "https://api.digitalocean.com/v2"


def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
    )


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_droplets",
            description="List all droplets, optionally filtered by tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "description": "Optional tag to filter droplets"},
                },
            },
        ),
        Tool(
            name="get_droplet",
            description="Get details for a specific droplet by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "droplet_id": {"type": "integer", "description": "Droplet ID"},
                },
                "required": ["droplet_id"],
            },
        ),
        Tool(
            name="get_droplet_by_name",
            description="Find a droplet by its name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Droplet name"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="resize_droplet",
            description="Resize a droplet to a new size",
            inputSchema={
                "type": "object",
                "properties": {
                    "droplet_id": {"type": "integer", "description": "Droplet ID"},
                    "new_size": {"type": "string", "description": "New size slug (e.g. s-2vcpu-4gb)"},
                    "disk": {"type": "boolean", "description": "Whether to resize disk (irreversible)", "default": True},
                },
                "required": ["droplet_id", "new_size"],
            },
        ),
        Tool(
            name="reboot_droplet",
            description="Reboot a droplet (soft reboot)",
            inputSchema={
                "type": "object",
                "properties": {
                    "droplet_id": {"type": "integer", "description": "Droplet ID"},
                },
                "required": ["droplet_id"],
            },
        ),
        Tool(
            name="power_cycle_droplet",
            description="Power cycle a droplet (hard reboot)",
            inputSchema={
                "type": "object",
                "properties": {
                    "droplet_id": {"type": "integer", "description": "Droplet ID"},
                },
                "required": ["droplet_id"],
            },
        ),
        Tool(
            name="get_action_status",
            description="Get status of a droplet action",
            inputSchema={
                "type": "object",
                "properties": {
                    "droplet_id": {"type": "integer", "description": "Droplet ID"},
                    "action_id": {"type": "integer", "description": "Action ID"},
                },
                "required": ["droplet_id", "action_id"],
            },
        ),
        Tool(
            name="wait_for_action",
            description="Wait for a droplet action to complete",
            inputSchema={
                "type": "object",
                "properties": {
                    "droplet_id": {"type": "integer", "description": "Droplet ID"},
                    "action_id": {"type": "integer", "description": "Action ID"},
                    "timeout": {"type": "integer", "description": "Max wait seconds", "default": 300},
                    "poll_interval": {"type": "integer", "description": "Poll interval seconds", "default": 5},
                },
                "required": ["droplet_id", "action_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with _get_client() as client:
        result = await _dispatch(client, name, arguments)
    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def _dispatch(client: httpx.AsyncClient, name: str, args: dict):
    if name == "list_droplets":
        return await _list_droplets(client, args.get("tag"))
    elif name == "get_droplet":
        return await _get_droplet(client, args["droplet_id"])
    elif name == "get_droplet_by_name":
        return await _get_droplet_by_name(client, args["name"])
    elif name == "resize_droplet":
        return await _resize_droplet(client, args["droplet_id"], args["new_size"], args.get("disk", True))
    elif name == "reboot_droplet":
        return await _reboot_droplet(client, args["droplet_id"])
    elif name == "power_cycle_droplet":
        return await _power_cycle_droplet(client, args["droplet_id"])
    elif name == "get_action_status":
        return await _get_action_status(client, args["droplet_id"], args["action_id"])
    elif name == "wait_for_action":
        return await _wait_for_action(client, args["droplet_id"], args["action_id"], args.get("timeout", 300), args.get("poll_interval", 5))
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _list_droplets(client, tag=None):
    url = f"{BASE_URL}/droplets"
    params = {}
    if tag:
        params["tag_name"] = tag
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json().get("droplets", [])


async def _get_droplet(client, droplet_id):
    url = f"{BASE_URL}/droplets/{droplet_id}"
    response = await client.get(url)
    response.raise_for_status()
    return response.json().get("droplet", {})


async def _get_droplet_by_name(client, name):
    droplets = await _list_droplets(client)
    for droplet in droplets:
        if droplet.get("name") == name:
            return droplet
    return None


async def _resize_droplet(client, droplet_id, new_size, disk=True):
    url = f"{BASE_URL}/droplets/{droplet_id}/actions"
    payload = {"type": "resize", "size": new_size, "disk": disk}
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("action", {})


async def _reboot_droplet(client, droplet_id):
    url = f"{BASE_URL}/droplets/{droplet_id}/actions"
    payload = {"type": "reboot"}
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("action", {})


async def _power_cycle_droplet(client, droplet_id):
    url = f"{BASE_URL}/droplets/{droplet_id}/actions"
    payload = {"type": "power_cycle"}
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("action", {})


async def _get_action_status(client, droplet_id, action_id):
    url = f"{BASE_URL}/droplets/{droplet_id}/actions/{action_id}"
    response = await client.get(url)
    response.raise_for_status()
    return response.json().get("action", {})


async def _wait_for_action(client, droplet_id, action_id, timeout=300, poll_interval=5):
    elapsed = 0
    while elapsed < timeout:
        action = await _get_action_status(client, droplet_id, action_id)
        status = action.get("status")
        if status == "completed":
            return True
        elif status == "errored":
            return False
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return False


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
