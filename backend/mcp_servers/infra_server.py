"""
Infrastructure Management MCP Server
Manages local Docker containers, Prometheus config, and SSH execution over stdio transport
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger("rift.mcp_servers.infra")

server = Server("infra")

PROMETHEUS_CONFIG_PATH = os.getenv("PROMETHEUS_CONFIG_PATH", "/tmp/rift_prometheus/prometheus.yml")
PROMETHEUS_CONTAINER_NAME = os.getenv("PROMETHEUS_CONTAINER_NAME", "rift-prometheus")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
SSH_DEFAULT_KEY_PATH = os.getenv("SSH_DEFAULT_KEY_PATH", os.path.expanduser("~/.ssh/id_ed25519_do_rift"))


async def _run_command(cmd, timeout=30):
    """Run a shell command and return (returncode, stdout, stderr)."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
    return process.returncode or 0, stdout.decode("utf-8", errors="ignore"), stderr.decode("utf-8", errors="ignore")


def _read_prometheus_config():
    """Read and parse the Prometheus YAML config."""
    config_path = Path(PROMETHEUS_CONFIG_PATH)
    if not config_path.exists():
        return {
            "global": {"scrape_interval": "15s", "evaluation_interval": "15s"},
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [{"targets": ["localhost:9090"]}],
                }
            ],
        }
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def _write_prometheus_config(config):
    """Write Prometheus YAML config to disk."""
    config_path = Path(PROMETHEUS_CONFIG_PATH)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="infra_manage_prometheus_targets",
            description="Add, remove, or list scrape targets in local Prometheus config",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "remove", "list"],
                        "description": "Action to perform",
                    },
                    "job_name": {"type": "string", "description": "Scrape job name (required for add/remove)"},
                    "target_ip": {"type": "string", "description": "Target IP address (required for add)"},
                    "target_port": {"type": "integer", "description": "Target port (default 9100)", "default": 9100},
                    "labels": {
                        "type": "object",
                        "description": "Optional labels to attach to the target",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="infra_reload_prometheus",
            description="Reload Prometheus configuration via lifecycle API or Docker restart",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="infra_execute_ssh_command",
            description="Execute an SSH command on a remote host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Remote host IP or hostname"},
                    "command": {"type": "string", "description": "Command to execute"},
                    "ssh_key_path": {"type": "string", "description": "Path to SSH private key"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                },
                "required": ["host", "command"],
            },
        ),
        Tool(
            name="infra_get_docker_status",
            description="Get status of a Docker container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "Container name or ID"},
                },
                "required": ["container_name"],
            },
        ),
        Tool(
            name="infra_docker_action",
            description="Start, stop, or restart a Docker container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "Container name or ID"},
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "restart"],
                        "description": "Action to perform",
                    },
                },
                "required": ["container_name", "action"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    result = await _dispatch(name, arguments)
    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def _dispatch(name, args):
    if name == "infra_manage_prometheus_targets":
        return await _manage_prometheus_targets(args)
    elif name == "infra_reload_prometheus":
        return await _reload_prometheus()
    elif name == "infra_execute_ssh_command":
        return await _execute_ssh_command(args)
    elif name == "infra_get_docker_status":
        return await _get_docker_status(args)
    elif name == "infra_docker_action":
        return await _docker_action(args)
    else:
        raise ValueError(f"Unknown tool: {name}")


# --------------- Tool implementations ---------------

async def _manage_prometheus_targets(args):
    action = args["action"]
    config = _read_prometheus_config()
    scrape_configs = config.setdefault("scrape_configs", [])

    if action == "list":
        targets = []
        for sc in scrape_configs:
            job = sc.get("job_name", "unknown")
            for static in sc.get("static_configs", []):
                for t in static.get("targets", []):
                    targets.append({"job_name": job, "target": t, "labels": static.get("labels", {})})
        return {"success": True, "targets": targets}

    job_name = args.get("job_name")
    if not job_name:
        return {"success": False, "error": "job_name is required for add/remove"}

    if action == "add":
        target_ip = args.get("target_ip")
        if not target_ip:
            return {"success": False, "error": "target_ip is required for add"}
        target_port = args.get("target_port", 9100)
        labels = args.get("labels", {})
        target_str = f"{target_ip}:{target_port}"

        # Check if job already exists
        for sc in scrape_configs:
            if sc.get("job_name") == job_name:
                # Add target to existing job
                static_configs = sc.setdefault("static_configs", [])
                if static_configs:
                    existing_targets = static_configs[0].get("targets", [])
                    if target_str not in existing_targets:
                        existing_targets.append(target_str)
                        static_configs[0]["targets"] = existing_targets
                else:
                    entry = {"targets": [target_str]}
                    if labels:
                        entry["labels"] = labels
                    static_configs.append(entry)
                _write_prometheus_config(config)
                # Auto-reload
                await _reload_prometheus()
                return {"success": True, "message": f"Added {target_str} to existing job '{job_name}'"}

        # Create new job
        new_job = {
            "job_name": job_name,
            "static_configs": [{"targets": [target_str]}],
        }
        if labels:
            new_job["static_configs"][0]["labels"] = labels
        scrape_configs.append(new_job)
        _write_prometheus_config(config)
        # Auto-reload
        await _reload_prometheus()
        return {"success": True, "message": f"Created job '{job_name}' with target {target_str}"}

    elif action == "remove":
        removed = False
        new_scrape_configs = []
        for sc in scrape_configs:
            if sc.get("job_name") == job_name:
                removed = True
                continue
            new_scrape_configs.append(sc)
        if removed:
            config["scrape_configs"] = new_scrape_configs
            _write_prometheus_config(config)
            await _reload_prometheus()
            return {"success": True, "message": f"Removed job '{job_name}'"}
        return {"success": False, "error": f"Job '{job_name}' not found"}

    return {"success": False, "error": f"Unknown action: {action}"}


async def _reload_prometheus():
    """Reload Prometheus via lifecycle API, fall back to Docker restart."""
    import httpx

    # Try lifecycle API first
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{PROMETHEUS_URL}/-/reload")
            if resp.status_code == 200:
                return {"success": True, "method": "lifecycle_api"}
    except Exception as e:
        logger.debug(f"Lifecycle API reload failed: {e}, trying Docker restart")

    # Fall back to Docker restart
    try:
        returncode, stdout, stderr = await _run_command(
            ["docker", "restart", PROMETHEUS_CONTAINER_NAME], timeout=30
        )
        if returncode == 0:
            return {"success": True, "method": "docker_restart"}
        return {"success": False, "error": f"Docker restart failed: {stderr}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _execute_ssh_command(args):
    host = args["host"]
    command = args["command"]
    key_path = args.get("ssh_key_path", SSH_DEFAULT_KEY_PATH)
    timeout = args.get("timeout", 30)

    ssh_cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", f"ConnectTimeout={timeout}",
        f"root@{host}",
        command,
    ]

    try:
        returncode, stdout, stderr = await _run_command(ssh_cmd, timeout=timeout + 5)
        return {
            "success": returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode,
        }
    except TimeoutError:
        return {"success": False, "stdout": "", "stderr": f"SSH command timed out after {timeout}s", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


async def _get_docker_status(args):
    container = args["container_name"]
    try:
        returncode, stdout, stderr = await _run_command(
            ["docker", "inspect", "--format", "{{.State.Status}}", container], timeout=10
        )
        if returncode == 0:
            status = stdout.strip()
            return {"success": True, "container": container, "status": status}
        return {"success": False, "error": stderr.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _docker_action(args):
    container = args["container_name"]
    action = args["action"]
    if action not in ("start", "stop", "restart"):
        return {"success": False, "error": f"Invalid action: {action}"}
    try:
        returncode, stdout, stderr = await _run_command(
            ["docker", action, container], timeout=30
        )
        return {
            "success": returncode == 0,
            "action": action,
            "container": container,
            "output": stdout.strip() or stderr.strip(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
