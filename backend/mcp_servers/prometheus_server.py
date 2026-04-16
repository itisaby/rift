"""
Prometheus MCP Server
Real MCP server for Prometheus metrics queries over stdio transport
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger("rift.mcp_servers.prometheus")

server = Server("prometheus")

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
PROMETHEUS_USER = os.getenv("PROMETHEUS_USER")
PROMETHEUS_PASSWORD = os.getenv("PROMETHEUS_PASSWORD")


def _get_client() -> httpx.AsyncClient:
    auth = None
    if PROMETHEUS_USER and PROMETHEUS_PASSWORD:
        auth = httpx.BasicAuth(PROMETHEUS_USER, PROMETHEUS_PASSWORD)
    return httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        headers={"Content-Type": "application/json"},
        auth=auth,
    )


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="prometheus_query_instant",
            description="Execute an instant PromQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "PromQL query string"},
                    "time": {"type": "string", "description": "Optional ISO timestamp"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="prometheus_query_range",
            description="Execute a range PromQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "PromQL query string"},
                    "start": {"type": "string", "description": "Start time ISO string"},
                    "end": {"type": "string", "description": "End time ISO string"},
                    "step": {"type": "string", "description": "Query resolution step", "default": "15s"},
                },
                "required": ["query", "start", "end"],
            },
        ),
        Tool(
            name="prometheus_get_cpu_usage",
            description="Get current CPU usage for an instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier (e.g. web-app:9100)"},
                },
                "required": ["instance"],
            },
        ),
        Tool(
            name="prometheus_get_memory_usage",
            description="Get current memory usage for an instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier"},
                },
                "required": ["instance"],
            },
        ),
        Tool(
            name="prometheus_get_disk_usage",
            description="Get current disk usage for an instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier"},
                    "mountpoint": {"type": "string", "description": "Filesystem mountpoint", "default": "/"},
                },
                "required": ["instance"],
            },
        ),
        Tool(
            name="prometheus_get_all_metrics",
            description="Get all common metrics (CPU, memory, disk) for an instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier"},
                },
                "required": ["instance"],
            },
        ),
        Tool(
            name="prometheus_check_threshold",
            description="Check if a metric exceeds a threshold",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier"},
                    "metric_type": {"type": "string", "description": "Metric type: cpu, memory, or disk"},
                    "threshold": {"type": "number", "description": "Threshold value (0-100)"},
                },
                "required": ["instance", "metric_type", "threshold"],
            },
        ),
        Tool(
            name="prometheus_get_alerts",
            description="Get active alerts from Prometheus",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="prometheus_check_health",
            description="Check Prometheus server health",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="prometheus_list_targets",
            description="List all currently configured scrape targets via Prometheus API",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="prometheus_get_target_health",
            description="Get health status of a specific target",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier (e.g. 1.2.3.4:9100)"},
                },
                "required": ["instance"],
            },
        ),
        Tool(
            name="prometheus_get_metric_history",
            description="Get metric trend over a time range for incident analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "Instance identifier"},
                    "metric_type": {"type": "string", "description": "Metric type: cpu, memory, or disk"},
                    "duration_minutes": {"type": "integer", "description": "How many minutes of history", "default": 30},
                    "step": {"type": "string", "description": "Query resolution step", "default": "60s"},
                },
                "required": ["instance", "metric_type"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with _get_client() as client:
        result = await _dispatch(client, name, arguments)
    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def _dispatch(client, name, args):
    if name == "prometheus_query_instant":
        return await _query_instant(client, args["query"], args.get("time"))
    elif name == "prometheus_query_range":
        return await _query_range(client, args["query"], args["start"], args["end"], args.get("step", "15s"))
    elif name == "prometheus_get_cpu_usage":
        return await _get_cpu_usage(client, args["instance"])
    elif name == "prometheus_get_memory_usage":
        return await _get_memory_usage(client, args["instance"])
    elif name == "prometheus_get_disk_usage":
        return await _get_disk_usage(client, args["instance"], args.get("mountpoint", "/"))
    elif name == "prometheus_get_all_metrics":
        return await _get_all_metrics(client, args["instance"])
    elif name == "prometheus_check_threshold":
        return await _check_threshold(client, args["instance"], args["metric_type"], args["threshold"])
    elif name == "prometheus_get_alerts":
        return await _get_alerts(client)
    elif name == "prometheus_check_health":
        return await _check_health(client)
    elif name == "prometheus_list_targets":
        return await _list_targets(client)
    elif name == "prometheus_get_target_health":
        return await _get_target_health(client, args["instance"])
    elif name == "prometheus_get_metric_history":
        return await _get_metric_history(
            client, args["instance"], args["metric_type"],
            args.get("duration_minutes", 30), args.get("step", "60s")
        )
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _query_instant(client, query, time_str=None):
    url = f"{PROMETHEUS_URL}/api/v1/query"
    params = {"query": query}
    if time_str:
        params["time"] = datetime.fromisoformat(time_str).timestamp()
    response = await client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise Exception(f"Query failed: {data.get('error')}")
    return data.get("data", {})


async def _query_range(client, query, start_str, end_str, step="15s"):
    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {
        "query": query,
        "start": datetime.fromisoformat(start_str).timestamp(),
        "end": datetime.fromisoformat(end_str).timestamp(),
        "step": step,
    }
    response = await client.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise Exception(f"Query failed: {data.get('error')}")
    return data.get("data", {})


def _extract_value(result):
    if result.get("resultType") == "vector" and result.get("result"):
        return float(result["result"][0]["value"][1])
    return None


async def _get_cpu_usage(client, instance):
    query = f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{instance="{instance}",mode="idle"}}[5m])) * 100)'
    result = await _query_instant(client, query)
    return _extract_value(result)


async def _get_memory_usage(client, instance):
    query = f'100 * (1 - ((node_memory_MemAvailable_bytes{{instance="{instance}"}} or node_memory_MemFree_bytes{{instance="{instance}"}}) / node_memory_MemTotal_bytes{{instance="{instance}"}}))'
    result = await _query_instant(client, query)
    return _extract_value(result)


async def _get_disk_usage(client, instance, mountpoint="/"):
    query = f'100 - ((node_filesystem_avail_bytes{{instance="{instance}",mountpoint="{mountpoint}"}} / node_filesystem_size_bytes{{instance="{instance}",mountpoint="{mountpoint}"}}) * 100)'
    result = await _query_instant(client, query)
    return _extract_value(result)


async def _get_all_metrics(client, instance):
    return {
        "instance": instance,
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_usage": await _get_cpu_usage(client, instance),
        "memory_usage": await _get_memory_usage(client, instance),
        "disk_usage": await _get_disk_usage(client, instance),
    }


async def _check_threshold(client, instance, metric_type, threshold):
    if metric_type == "cpu":
        value = await _get_cpu_usage(client, instance)
    elif metric_type == "memory":
        value = await _get_memory_usage(client, instance)
    elif metric_type == "disk":
        value = await _get_disk_usage(client, instance)
    else:
        raise ValueError(f"Unknown metric type: {metric_type}")
    if value is None:
        return False
    return value >= threshold


async def _get_alerts(client):
    url = f"{PROMETHEUS_URL}/api/v1/alerts"
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise Exception(f"Failed to get alerts: {data.get('error')}")
    return data.get("data", {}).get("alerts", [])


async def _check_health(client):
    url = f"{PROMETHEUS_URL}/-/healthy"
    try:
        response = await client.get(url)
        response.raise_for_status()
        return True
    except Exception:
        return False


async def _list_targets(client):
    url = f"{PROMETHEUS_URL}/api/v1/targets"
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise Exception(f"Failed to list targets: {data.get('error')}")
    targets = data.get("data", {}).get("activeTargets", [])
    return [
        {
            "instance": t.get("labels", {}).get("instance", "unknown"),
            "job": t.get("labels", {}).get("job", "unknown"),
            "health": t.get("health", "unknown"),
            "lastScrape": t.get("lastScrape"),
            "scrapeUrl": t.get("scrapeUrl"),
        }
        for t in targets
    ]


async def _get_target_health(client, instance):
    url = f"{PROMETHEUS_URL}/api/v1/targets"
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise Exception(f"Failed to get targets: {data.get('error')}")
    for t in data.get("data", {}).get("activeTargets", []):
        if t.get("labels", {}).get("instance") == instance:
            return {
                "instance": instance,
                "health": t.get("health", "unknown"),
                "lastScrape": t.get("lastScrape"),
                "lastScrapeDuration": t.get("lastScrapeDuration"),
                "lastError": t.get("lastError", ""),
            }
    return {"instance": instance, "health": "not_found", "error": f"Target {instance} not found"}


async def _get_metric_history(client, instance, metric_type, duration_minutes=30, step="60s"):
    metric_queries = {
        "cpu": f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{instance="{instance}",mode="idle"}}[5m])) * 100)',
        "memory": f'100 * (1 - ((node_memory_MemAvailable_bytes{{instance="{instance}"}} or node_memory_MemFree_bytes{{instance="{instance}"}}) / node_memory_MemTotal_bytes{{instance="{instance}"}}))',
        "disk": f'100 - ((node_filesystem_avail_bytes{{instance="{instance}",mountpoint="/"}} / node_filesystem_size_bytes{{instance="{instance}",mountpoint="/"}}) * 100)',
    }
    query = metric_queries.get(metric_type)
    if not query:
        raise ValueError(f"Unknown metric type: {metric_type}. Use cpu, memory, or disk.")

    end = datetime.utcnow()
    start = end - timedelta(minutes=duration_minutes)
    result = await _query_range(client, query, start.isoformat(), end.isoformat(), step)

    # Simplify the result
    series = result.get("result", [])
    if series:
        values = series[0].get("values", [])
        return {
            "instance": instance,
            "metric_type": metric_type,
            "duration_minutes": duration_minutes,
            "data_points": len(values),
            "values": [{"timestamp": v[0], "value": float(v[1])} for v in values],
        }
    return {
        "instance": instance,
        "metric_type": metric_type,
        "duration_minutes": duration_minutes,
        "data_points": 0,
        "values": [],
    }


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
