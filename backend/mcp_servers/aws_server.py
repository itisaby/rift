"""
AWS MCP Server
Real MCP server for AWS operations over stdio transport
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

logger = logging.getLogger("rift.mcp_servers.aws")

server = Server("aws")


def _get_boto3_session():
    import boto3

    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    if access_key and secret_key:
        return boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
    return boto3.Session(region_name=region)


def _get_instance_name(instance):
    for tag in instance.get("Tags", []):
        if tag.get("Key") == "Name":
            return tag.get("Value", "unnamed")
    return "unnamed"


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="aws_list_instances",
            description="List EC2 instances with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "array",
                        "description": "Optional EC2 filters",
                        "items": {"type": "object"},
                    },
                },
            },
        ),
        Tool(
            name="aws_get_instance",
            description="Get details of a specific EC2 instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "EC2 instance ID"},
                },
                "required": ["instance_id"],
            },
        ),
        Tool(
            name="aws_list_databases",
            description="List RDS database instances",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="aws_list_load_balancers",
            description="List Application/Network Load Balancers",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="aws_list_vpcs",
            description="List VPCs",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="aws_get_instance_metrics",
            description="Get CloudWatch metrics for an EC2 instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "EC2 instance ID"},
                    "metric_name": {"type": "string", "description": "Metric name (e.g. CPUUtilization)"},
                    "period": {"type": "integer", "description": "Period in seconds", "default": 300},
                },
                "required": ["instance_id", "metric_name"],
            },
        ),
        Tool(
            name="aws_get_credentials",
            description="Get AWS credentials for Terraform integration",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    result = await _dispatch(name, arguments)
    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def _dispatch(name, args):
    if name == "aws_list_instances":
        return await _list_instances(args.get("filters"))
    elif name == "aws_get_instance":
        return await _get_instance(args["instance_id"])
    elif name == "aws_list_databases":
        return await _list_databases()
    elif name == "aws_list_load_balancers":
        return await _list_load_balancers()
    elif name == "aws_list_vpcs":
        return await _list_vpcs()
    elif name == "aws_get_instance_metrics":
        return await _get_instance_metrics(args["instance_id"], args["metric_name"], args.get("period", 300))
    elif name == "aws_get_credentials":
        return await _get_credentials()
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _list_instances(filters=None):
    def _sync():
        session = _get_boto3_session()
        ec2 = session.client("ec2")
        response = ec2.describe_instances(Filters=filters or [])
        instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append({
                    "id": instance.get("InstanceId"),
                    "name": _get_instance_name(instance),
                    "type": instance.get("InstanceType"),
                    "state": instance.get("State", {}).get("Name"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "vpc_id": instance.get("VpcId"),
                    "subnet_id": instance.get("SubnetId"),
                    "launch_time": str(instance.get("LaunchTime")),
                    "tags": instance.get("Tags", []),
                })
        return instances
    return await asyncio.to_thread(_sync)


async def _get_instance(instance_id):
    def _sync():
        session = _get_boto3_session()
        ec2 = session.client("ec2")
        response = ec2.describe_instances(InstanceIds=[instance_id])
        if not response.get("Reservations"):
            raise ValueError(f"Instance {instance_id} not found")
        instance = response["Reservations"][0]["Instances"][0]
        return {
            "id": instance.get("InstanceId"),
            "name": _get_instance_name(instance),
            "type": instance.get("InstanceType"),
            "state": instance.get("State", {}).get("Name"),
            "public_ip": instance.get("PublicIpAddress"),
            "private_ip": instance.get("PrivateIpAddress"),
            "vpc_id": instance.get("VpcId"),
            "subnet_id": instance.get("SubnetId"),
            "security_groups": instance.get("SecurityGroups", []),
            "launch_time": str(instance.get("LaunchTime")),
            "tags": instance.get("Tags", []),
            "monitoring": instance.get("Monitoring", {}).get("State"),
        }
    return await asyncio.to_thread(_sync)


async def _list_databases():
    def _sync():
        session = _get_boto3_session()
        rds = session.client("rds")
        response = rds.describe_db_instances()
        databases = []
        for db in response.get("DBInstances", []):
            databases.append({
                "id": db.get("DBInstanceIdentifier"),
                "engine": db.get("Engine"),
                "engine_version": db.get("EngineVersion"),
                "instance_class": db.get("DBInstanceClass"),
                "status": db.get("DBInstanceStatus"),
                "endpoint": db.get("Endpoint", {}).get("Address"),
                "port": db.get("Endpoint", {}).get("Port"),
                "storage": db.get("AllocatedStorage"),
                "multi_az": db.get("MultiAZ"),
                "vpc_id": db.get("DBSubnetGroup", {}).get("VpcId"),
                "created_time": str(db.get("InstanceCreateTime")),
            })
        return databases
    return await asyncio.to_thread(_sync)


async def _list_load_balancers():
    def _sync():
        session = _get_boto3_session()
        elb = session.client("elbv2")
        response = elb.describe_load_balancers()
        lbs = []
        for lb in response.get("LoadBalancers", []):
            lbs.append({
                "arn": lb.get("LoadBalancerArn"),
                "name": lb.get("LoadBalancerName"),
                "dns_name": lb.get("DNSName"),
                "type": lb.get("Type"),
                "scheme": lb.get("Scheme"),
                "vpc_id": lb.get("VpcId"),
                "state": lb.get("State", {}).get("Code"),
                "created_time": str(lb.get("CreatedTime")),
            })
        return lbs
    return await asyncio.to_thread(_sync)


async def _list_vpcs():
    def _sync():
        session = _get_boto3_session()
        ec2 = session.client("ec2")
        response = ec2.describe_vpcs()
        vpcs = []
        for vpc in response.get("Vpcs", []):
            vpcs.append({
                "id": vpc.get("VpcId"),
                "cidr_block": vpc.get("CidrBlock"),
                "state": vpc.get("State"),
                "is_default": vpc.get("IsDefault"),
                "tags": vpc.get("Tags", []),
            })
        return vpcs
    return await asyncio.to_thread(_sync)


async def _get_instance_metrics(instance_id, metric_name, period=300):
    def _sync():
        session = _get_boto3_session()
        cloudwatch = session.client("cloudwatch")
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName=metric_name,
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=period,
            Statistics=["Average", "Maximum", "Minimum"],
        )
        return response.get("Datapoints", [])
    return await asyncio.to_thread(_sync)


async def _get_credentials():
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    return {"access_key_id": access_key, "secret_access_key": secret_key}


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
