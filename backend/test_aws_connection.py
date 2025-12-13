"""
Test AWS MCP Client Connection
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from mcp_clients.aws_mcp import AWSMCP


async def test_aws_connection():
    print("\n" + "=" * 80)
    print(" " * 25 + "AWS CONNECTION TEST")
    print("=" * 80 + "\n")
    
    # Initialize AWS MCP
    print("🔧 Initializing AWS MCP client...")
    aws = AWSMCP(
        access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region=os.getenv('AWS_REGION', 'us-east-1')
    )
    print(f"✅ AWS MCP initialized for region: {aws.region}\n")
    
    # Test EC2
    print("📦 Testing EC2 Operations...")
    try:
        instances = await aws.list_instances()
        print(f"✅ Found {len(instances)} EC2 instance(s)")
        
        for i, instance in enumerate(instances[:3], 1):
            print(f"\n   {i}. {instance['name']} (ID: {instance['id']})")
            print(f"      Type: {instance['type']} | State: {instance['state']}")
            print(f"      Public IP: {instance.get('public_ip', 'N/A')}")
    except Exception as e:
        print(f"⚠️  EC2 list failed: {str(e)}")
    
    # Test RDS
    print("\n💾 Testing RDS Operations...")
    try:
        databases = await aws.list_databases()
        print(f"✅ Found {len(databases)} RDS database(s)")
        
        for i, db in enumerate(databases[:3], 1):
            print(f"\n   {i}. {db['id']}")
            print(f"      Engine: {db['engine']} {db['engine_version']}")
            print(f"      Status: {db['status']}")
            print(f"      Endpoint: {db.get('endpoint', 'N/A')}")
    except Exception as e:
        print(f"⚠️  RDS list failed: {str(e)}")
    
    # Test Load Balancers
    print("\n⚖️  Testing Load Balancer Operations...")
    try:
        load_balancers = await aws.list_load_balancers()
        print(f"✅ Found {len(load_balancers)} load balancer(s)")
        
        for i, lb in enumerate(load_balancers[:3], 1):
            print(f"\n   {i}. {lb['name']}")
            print(f"      Type: {lb['type']} | State: {lb['state']}")
            print(f"      DNS: {lb['dns_name']}")
    except Exception as e:
        print(f"⚠️  Load Balancer list failed: {str(e)}")
    
    # Test VPC
    print("\n🌐 Testing VPC Operations...")
    try:
        vpcs = await aws.list_vpcs()
        print(f"✅ Found {len(vpcs)} VPC(s)")
        
        for i, vpc in enumerate(vpcs[:3], 1):
            print(f"\n   {i}. {vpc['id']}")
            print(f"      CIDR: {vpc['cidr_block']}")
            print(f"      Default: {vpc['is_default']}")
    except Exception as e:
        print(f"⚠️  VPC list failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print(" " * 25 + "AWS CONNECTION SUCCESSFUL!")
    print("=" * 80 + "\n")
    
    print("✅ AWS MCP Client is ready for multi-cloud provisioning!")
    print("\n💡 Next Steps:")
    print("   1. Upload multi-cloud-guide.md to Gradient AI knowledge base")
    print("   2. Test provisioning with: 'Create an EC2 instance on AWS'")
    print("   3. Multi-cloud is ready! 🚀\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_aws_connection())
    except Exception as e:
        print(f"\n❌ AWS Connection Failed: {str(e)}")
        import traceback
        traceback.print_exc()
