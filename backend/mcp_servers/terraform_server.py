"""
Terraform MCP Server
Real MCP server wrapping Terraform CLI operations over stdio transport
"""

import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger("rift.mcp_servers.terraform")

server = Server("terraform")

TF_WORKING_DIR = os.getenv("TF_WORKING_DIR", "/tmp/rift_terraform")
TF_BINARY = os.getenv("TF_BINARY", "terraform")

# Ensure working directory exists
Path(TF_WORKING_DIR).mkdir(parents=True, exist_ok=True)


def _credential_env_from_variables(variables):
    """Extract cloud credentials from variables and return as env vars.

    Terraform providers read these automatically, so credentials work
    regardless of what variable names the AI chose in the HCL config.
    """
    if not variables:
        return {}
    env = {}
    # AWS — provider reads AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION
    for key in ("aws_access_key_id", "access_key_id", "aws_access_key"):
        if variables.get(key):
            env["AWS_ACCESS_KEY_ID"] = str(variables[key])
            break
    for key in ("aws_secret_access_key", "secret_access_key", "aws_secret_key"):
        if variables.get(key):
            env["AWS_SECRET_ACCESS_KEY"] = str(variables[key])
            break
    for key in ("aws_region", "region"):
        if variables.get(key):
            env.setdefault("AWS_DEFAULT_REGION", str(variables[key]))
            break
    # DigitalOcean — provider reads DIGITALOCEAN_TOKEN
    for key in ("do_token", "digitalocean_token", "digitalocean_api_token"):
        if variables.get(key):
            env["DIGITALOCEAN_TOKEN"] = str(variables[key])
            break
    return env


async def _run_command(args, cwd=None, env=None):
    cmd = [TF_BINARY] + args
    work_dir = cwd or TF_WORKING_DIR
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=work_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=command_env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise TimeoutError(f"Terraform command timed out: {' '.join(cmd)}")
    return process.returncode or 0, stdout.decode("utf-8"), stderr.decode("utf-8")


_WORKING_DIR_PROP = {"type": "string", "description": "Optional per-project working directory (overrides global TF_WORKING_DIR)"}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="terraform_clean_state", description="Clean Terraform state files", inputSchema={
            "type": "object",
            "properties": {"working_dir": _WORKING_DIR_PROP},
        }),
        Tool(
            name="terraform_init",
            description="Initialize Terraform working directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "backend_config": {"type": "object", "description": "Optional backend config key-value pairs"},
                    "working_dir": _WORKING_DIR_PROP,
                },
            },
        ),
        Tool(
            name="terraform_validate",
            description="Validate Terraform configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "config": {"type": "string", "description": "Terraform configuration content"},
                    "working_dir": _WORKING_DIR_PROP,
                },
                "required": ["config"],
            },
        ),
        Tool(
            name="terraform_plan",
            description="Generate Terraform execution plan",
            inputSchema={
                "type": "object",
                "properties": {
                    "config": {"type": "string", "description": "Terraform configuration content"},
                    "variables": {"type": "object", "description": "Optional variables"},
                    "working_dir": _WORKING_DIR_PROP,
                },
                "required": ["config"],
            },
        ),
        Tool(
            name="terraform_apply",
            description="Apply Terraform configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "config": {"type": "string", "description": "Terraform configuration content"},
                    "variables": {"type": "object", "description": "Optional variables"},
                    "auto_approve": {"type": "boolean", "description": "Auto-approve changes", "default": False},
                    "working_dir": _WORKING_DIR_PROP,
                },
                "required": ["config"],
            },
        ),
        Tool(name="terraform_get_outputs", description="Get Terraform output values", inputSchema={
            "type": "object",
            "properties": {"working_dir": _WORKING_DIR_PROP},
        }),
        Tool(
            name="terraform_show_state",
            description="Show current Terraform state",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource": {"type": "string", "description": "Optional specific resource to show"},
                    "working_dir": _WORKING_DIR_PROP,
                },
            },
        ),
        Tool(
            name="terraform_destroy",
            description="Destroy Terraform-managed infrastructure",
            inputSchema={
                "type": "object",
                "properties": {
                    "auto_approve": {"type": "boolean", "description": "Auto-approve destruction", "default": False},
                    "working_dir": _WORKING_DIR_PROP,
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    result = await _dispatch(name, arguments)
    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def _dispatch(name, args):
    wd = args.get("working_dir")
    if wd:
        Path(wd).mkdir(parents=True, exist_ok=True)
    if name == "terraform_clean_state":
        return await _clean_state(working_dir=wd)
    elif name == "terraform_init":
        return await _init(args.get("backend_config"), working_dir=wd)
    elif name == "terraform_validate":
        return await _validate(args["config"], working_dir=wd)
    elif name == "terraform_plan":
        return await _plan(args["config"], args.get("variables"), working_dir=wd)
    elif name == "terraform_apply":
        return await _apply(args["config"], args.get("variables"), args.get("auto_approve", False), working_dir=wd)
    elif name == "terraform_get_outputs":
        return await _get_outputs(working_dir=wd)
    elif name == "terraform_show_state":
        return await _show_state(args.get("resource"), working_dir=wd)
    elif name == "terraform_destroy":
        return await _destroy(args.get("auto_approve", False), working_dir=wd)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _clean_state(working_dir=None):
    working_path = Path(working_dir or TF_WORKING_DIR)
    for state_file in ["terraform.tfstate", "terraform.tfstate.backup"]:
        p = working_path / state_file
        if p.exists():
            p.unlink()
    lock_file = working_path / ".terraform.lock.hcl"
    if lock_file.exists():
        lock_file.unlink()
    terraform_dir = working_path / ".terraform"
    if terraform_dir.exists():
        shutil.rmtree(terraform_dir)
    return True


async def _init(backend_config=None, working_dir=None):
    args = ["init", "-no-color"]
    if backend_config:
        for key, value in backend_config.items():
            args.extend(["-backend-config", f"{key}={value}"])
    returncode, stdout, stderr = await _run_command(args, cwd=working_dir)
    if returncode != 0:
        return False
    return True


def _auto_declare_missing_variables(config):
    """Auto-add variable blocks for any var.X references that aren't declared."""
    import re
    vars_used = set(re.findall(r'var\.(\w+)', config))
    vars_declared = set(re.findall(r'variable\s+"(\w+)"', config))
    missing = vars_used - vars_declared
    if missing:
        logger.info(f"Auto-declaring missing variables: {missing}")
        for var_name in sorted(missing):
            # Infer type from usage context
            # If used with concat() or in a list context, it's a list
            if re.search(rf'concat\s*\(\s*var\.{var_name}', config) or \
               re.search(rf'var\.{var_name}\s*,\s*\[', config):
                var_type = "list(string)"
                var_default = "[]"
            else:
                var_type = "string"
                var_default = '""'
            config += f'\nvariable "{var_name}" {{\n  description = "Auto-declared variable"\n  type        = {var_type}\n  default     = {var_default}\n}}\n'
    return config


async def _validate(config, working_dir=None):
    wd = Path(working_dir or TF_WORKING_DIR)
    # Auto-declare any missing variables before writing
    config = _auto_declare_missing_variables(config)
    config_file = wd / "main.tf"
    config_file.write_text(config)

    # Write dummy tfvars so validate doesn't fail on required vars without defaults
    import re
    declared_vars = re.findall(r'variable\s+"(\w+)"', config)
    if declared_vars:
        dummy_vars = {v: "placeholder" for v in declared_vars}
        var_file = wd / "terraform.tfvars.json"
        var_file.write_text(json.dumps(dummy_vars, indent=2))

    await _init(working_dir=working_dir)
    returncode, stdout, stderr = await _run_command(["validate", "-json", "-no-color"], cwd=working_dir)
    try:
        result = json.loads(stdout)
        valid = result.get("valid", False)
        errors = [d.get("summary", "") for d in result.get("diagnostics", []) if d.get("severity") == "error"]
        warnings = [d.get("summary", "") for d in result.get("diagnostics", []) if d.get("severity") == "warning"]
        return {"valid": valid, "errors": errors, "warnings": warnings, "metadata": result}
    except json.JSONDecodeError:
        valid = returncode == 0
        return {"valid": valid, "errors": [stderr] if not valid else [], "warnings": [], "metadata": {"stdout": stdout, "stderr": stderr}}


def _filter_variables(config, variables):
    """
    Build tfvars: keep provided values for declared vars,
    and fill in defaults for any declared vars not in the provided variables.
    """
    import re
    declared = set(re.findall(r'variable\s+"(\w+)"', config))
    result = {}
    for var_name in declared:
        if var_name in variables:
            result[var_name] = variables[var_name]
        else:
            # Check if the variable has a default in the config
            # Match: variable "X" { ... default = ... }
            pattern = rf'variable\s+"{var_name}"\s*\{{[^}}]*default\s*='
            if not re.search(pattern, config, re.DOTALL):
                # No default — provide a placeholder so terraform doesn't prompt
                result[var_name] = ""
    return result


async def _plan(config, variables=None, working_dir=None):
    wd = Path(working_dir or TF_WORKING_DIR)
    config = _auto_declare_missing_variables(config)
    config_file = wd / "main.tf"
    config_file.write_text(config)
    cred_env = _credential_env_from_variables(variables)
    if variables:
        variables = _filter_variables(config, variables)
    if variables:
        var_file = wd / "terraform.tfvars.json"
        var_file.write_text(json.dumps(variables, indent=2))
    await _init(working_dir=working_dir)
    args = ["plan", "-no-color", "-out=tfplan"]
    if variables:
        args.extend(["-var-file=terraform.tfvars.json"])
    returncode, stdout, stderr = await _run_command(args, cwd=working_dir, env=cred_env)
    if returncode != 0:
        return {
            "success": False, "changes_count": 0,
            "resources_to_add": 0, "resources_to_change": 0, "resources_to_destroy": 0,
            "plan_output": stderr, "metadata": {"error": stderr},
        }
    add_count = change_count = destroy_count = 0
    for line in stdout.split("\n"):
        if "Plan:" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if i > 0 and i + 1 < len(parts):
                    try:
                        if parts[i] == "to" and parts[i + 1].startswith("add"):
                            add_count = int(parts[i - 1])
                        elif parts[i] == "to" and parts[i + 1].startswith("change"):
                            change_count = int(parts[i - 1])
                        elif parts[i] == "to" and parts[i + 1].startswith("destroy"):
                            destroy_count = int(parts[i - 1])
                    except (ValueError, IndexError):
                        continue
    return {
        "success": True,
        "changes_count": add_count + change_count + destroy_count,
        "resources_to_add": add_count,
        "resources_to_change": change_count,
        "resources_to_destroy": destroy_count,
        "plan_output": stdout,
        "metadata": {"stdout": stdout, "stderr": stderr},
    }


async def _apply(config, variables=None, auto_approve=False, working_dir=None):
    wd = Path(working_dir or TF_WORKING_DIR)
    config = _auto_declare_missing_variables(config)
    config_file = wd / "main.tf"
    config_file.write_text(config)
    cred_env = _credential_env_from_variables(variables)
    if variables:
        variables = _filter_variables(config, variables)
    if variables:
        var_file = wd / "terraform.tfvars.json"
        var_file.write_text(json.dumps(variables, indent=2))
    await _init(working_dir=working_dir)
    args = ["apply", "-no-color"]
    if auto_approve:
        args.append("-auto-approve")
    if variables:
        args.extend(["-var-file=terraform.tfvars.json"])
    start_time = time.time()
    returncode, stdout, stderr = await _run_command(args, cwd=working_dir, env=cred_env)
    duration = time.time() - start_time
    if returncode != 0:
        return {
            "success": False, "resources_created": 0, "resources_updated": 0,
            "resources_destroyed": 0, "output_values": {}, "duration_seconds": duration,
            "error_message": stderr,
        }
    created = stdout.count("Creating...")
    updated = stdout.count("Modifying...")
    destroyed = stdout.count("Destroying...")
    output_values = await _get_outputs(working_dir=working_dir)
    return {
        "success": True,
        "resources_created": created,
        "resources_updated": updated,
        "resources_destroyed": destroyed,
        "output_values": output_values,
        "duration_seconds": duration,
    }


async def _get_outputs(working_dir=None):
    returncode, stdout, stderr = await _run_command(["output", "-json", "-no-color"], cwd=working_dir)
    if returncode != 0:
        return {}
    try:
        outputs = json.loads(stdout)
        result = {}
        for key, value in outputs.items():
            if isinstance(value, dict) and "value" in value:
                result[key] = value["value"]
            else:
                result[key] = value
        return result
    except json.JSONDecodeError:
        return {}


async def _show_state(resource=None, working_dir=None):
    args = ["show", "-json", "-no-color"]
    if resource:
        args.append(resource)
    returncode, stdout, stderr = await _run_command(args, cwd=working_dir)
    if returncode != 0:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


async def _destroy(auto_approve=False, working_dir=None):
    # Read saved tfvars to extract credential env vars
    wd = Path(working_dir or TF_WORKING_DIR)
    cred_env = {}
    tfvars_path = wd / "terraform.tfvars.json"
    if tfvars_path.exists():
        try:
            saved_vars = json.loads(tfvars_path.read_text())
            cred_env = _credential_env_from_variables(saved_vars)
        except (json.JSONDecodeError, OSError):
            pass
    args = ["destroy", "-no-color"]
    if auto_approve:
        args.append("-auto-approve")
    if tfvars_path.exists():
        args.extend(["-var-file=terraform.tfvars.json"])
    returncode, stdout, stderr = await _run_command(args, cwd=working_dir, env=cred_env)
    return returncode == 0


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
