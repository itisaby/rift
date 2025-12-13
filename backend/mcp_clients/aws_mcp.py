"""
AWS MCP Client for Rift
Provides interface to AWS services (EC2, RDS, ELB, VPC, etc.)
"""

import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger("rift.mcp.aws")


class AWSMCP:
    """
    MCP client for AWS operations.
    Provides methods to interact with AWS services.
    """

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        profile: Optional[str] = None
    ):
        """
        Initialize AWS MCP client.

        Args:
            access_key_id: AWS access key ID (optional if using profile)
            secret_access_key: AWS secret access key (optional if using profile)
            region: Default AWS region
            profile: AWS CLI profile name (alternative to keys)
        """
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.profile = profile

        # Import boto3 here to make it optional
        try:
            import boto3
            
            # Initialize session
            if profile:
                self.session = boto3.Session(profile_name=profile, region_name=region)
            elif access_key_id and secret_access_key:
                self.session = boto3.Session(
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    region_name=region
                )
            else:
                # Use default credentials (environment variables or instance role)
                self.session = boto3.Session(region_name=region)

            # Initialize clients
            self.ec2 = self.session.client('ec2')
            self.rds = self.session.client('rds')
            self.elb = self.session.client('elbv2')
            self.s3 = self.session.client('s3')
            self.cloudwatch = self.session.client('cloudwatch')

            logger.info(f"AWS MCP initialized for region: {region}")

        except ImportError:
            logger.warning("boto3 not installed. Install with: pip install boto3")
            raise ImportError("boto3 is required for AWS integration. Install with: pip install boto3")

    # ============================================================================
    # EC2 Operations
    # ============================================================================

    async def list_instances(self, filters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        List EC2 instances.

        Args:
            filters: Optional filters (e.g., [{'Name': 'tag:Project', 'Values': ['my-project']}])

        Returns:
            List of instance information dictionaries
        """
        try:
            response = self.ec2.describe_instances(Filters=filters or [])
            
            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'id': instance.get('InstanceId'),
                        'name': self._get_instance_name(instance),
                        'type': instance.get('InstanceType'),
                        'state': instance.get('State', {}).get('Name'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId'),
                        'launch_time': str(instance.get('LaunchTime')),
                        'tags': instance.get('Tags', [])
                    })

            logger.info(f"Listed {len(instances)} EC2 instances")
            return instances

        except Exception as e:
            logger.error(f"Failed to list EC2 instances: {str(e)}")
            raise

    async def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Get details of a specific EC2 instance.

        Args:
            instance_id: EC2 instance ID

        Returns:
            Instance information dictionary
        """
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            
            if not response.get('Reservations'):
                raise ValueError(f"Instance {instance_id} not found")

            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                'id': instance.get('InstanceId'),
                'name': self._get_instance_name(instance),
                'type': instance.get('InstanceType'),
                'state': instance.get('State', {}).get('Name'),
                'public_ip': instance.get('PublicIpAddress'),
                'private_ip': instance.get('PrivateIpAddress'),
                'vpc_id': instance.get('VpcId'),
                'subnet_id': instance.get('SubnetId'),
                'security_groups': instance.get('SecurityGroups', []),
                'launch_time': str(instance.get('LaunchTime')),
                'tags': instance.get('Tags', []),
                'monitoring': instance.get('Monitoring', {}).get('State')
            }

        except Exception as e:
            logger.error(f"Failed to get instance {instance_id}: {str(e)}")
            raise

    # ============================================================================
    # RDS Operations
    # ============================================================================

    async def list_databases(self) -> List[Dict[str, Any]]:
        """
        List RDS database instances.

        Returns:
            List of database information dictionaries
        """
        try:
            response = self.rds.describe_db_instances()
            
            databases = []
            for db in response.get('DBInstances', []):
                databases.append({
                    'id': db.get('DBInstanceIdentifier'),
                    'engine': db.get('Engine'),
                    'engine_version': db.get('EngineVersion'),
                    'instance_class': db.get('DBInstanceClass'),
                    'status': db.get('DBInstanceStatus'),
                    'endpoint': db.get('Endpoint', {}).get('Address'),
                    'port': db.get('Endpoint', {}).get('Port'),
                    'storage': db.get('AllocatedStorage'),
                    'multi_az': db.get('MultiAZ'),
                    'vpc_id': db.get('DBSubnetGroup', {}).get('VpcId'),
                    'created_time': str(db.get('InstanceCreateTime'))
                })

            logger.info(f"Listed {len(databases)} RDS instances")
            return databases

        except Exception as e:
            logger.error(f"Failed to list RDS instances: {str(e)}")
            raise

    # ============================================================================
    # Load Balancer Operations
    # ============================================================================

    async def list_load_balancers(self) -> List[Dict[str, Any]]:
        """
        List Application/Network Load Balancers.

        Returns:
            List of load balancer information dictionaries
        """
        try:
            response = self.elb.describe_load_balancers()
            
            load_balancers = []
            for lb in response.get('LoadBalancers', []):
                load_balancers.append({
                    'arn': lb.get('LoadBalancerArn'),
                    'name': lb.get('LoadBalancerName'),
                    'dns_name': lb.get('DNSName'),
                    'type': lb.get('Type'),
                    'scheme': lb.get('Scheme'),
                    'vpc_id': lb.get('VpcId'),
                    'state': lb.get('State', {}).get('Code'),
                    'created_time': str(lb.get('CreatedTime'))
                })

            logger.info(f"Listed {len(load_balancers)} load balancers")
            return load_balancers

        except Exception as e:
            logger.error(f"Failed to list load balancers: {str(e)}")
            raise

    # ============================================================================
    # VPC Operations
    # ============================================================================

    async def list_vpcs(self) -> List[Dict[str, Any]]:
        """
        List VPCs.

        Returns:
            List of VPC information dictionaries
        """
        try:
            response = self.ec2.describe_vpcs()
            
            vpcs = []
            for vpc in response.get('Vpcs', []):
                vpcs.append({
                    'id': vpc.get('VpcId'),
                    'cidr_block': vpc.get('CidrBlock'),
                    'state': vpc.get('State'),
                    'is_default': vpc.get('IsDefault'),
                    'tags': vpc.get('Tags', [])
                })

            logger.info(f"Listed {len(vpcs)} VPCs")
            return vpcs

        except Exception as e:
            logger.error(f"Failed to list VPCs: {str(e)}")
            raise

    # ============================================================================
    # CloudWatch Metrics
    # ============================================================================

    async def get_instance_metrics(
        self,
        instance_id: str,
        metric_name: str,
        period: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Get CloudWatch metrics for an EC2 instance.

        Args:
            instance_id: EC2 instance ID
            metric_name: Metric name (e.g., 'CPUUtilization', 'NetworkIn')
            period: Period in seconds (default: 300 = 5 minutes)

        Returns:
            List of metric datapoints
        """
        try:
            from datetime import datetime, timedelta

            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=period,
                Statistics=['Average', 'Maximum', 'Minimum']
            )

            datapoints = response.get('Datapoints', [])
            logger.info(f"Retrieved {len(datapoints)} datapoints for {metric_name}")
            
            return datapoints

        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            raise

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """Extract instance name from tags."""
        tags = instance.get('Tags', [])
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value', 'unnamed')
        return 'unnamed'

    async def get_credentials(self) -> Dict[str, str]:
        """
        Get AWS credentials (for Terraform).

        Returns:
            Dictionary with access_key_id and secret_access_key
        """
        if self.profile:
            # Get credentials from profile
            credentials = self.session.get_credentials()
            return {
                'access_key_id': credentials.access_key,
                'secret_access_key': credentials.secret_key,
                'session_token': credentials.token
            }
        else:
            return {
                'access_key_id': self.access_key_id or '',
                'secret_access_key': self.secret_access_key or ''
            }
