"""
Test script to verify Multi-Cloud Knowledge Base integration
Tests both DigitalOcean and AWS infrastructure generation
"""

import asyncio
import sys
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from agents.provisioner_agent import ProvisionerAgent
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from mcp_clients.aws_mcp import AWSMCP
from models.provision_request import ProvisionRequest


async def test_multicloud_knowledge_base():
    """Test if the provisioner agent can use the multi-cloud knowledge base"""
    
    print("=" * 80)
    print("MULTI-CLOUD KNOWLEDGE BASE INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Initialize MCP clients
    print("1. Initializing MCP clients...")
    terraform_mcp = TerraformMCP()
    do_mcp = DigitalOceanMCP(os.getenv("DIGITALOCEAN_API_TOKEN"))
    aws_mcp = AWSMCP(
        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )
    print("   ✓ MCP clients initialized (DigitalOcean + AWS)")
    print()
    
    # Initialize Provisioner Agent with Knowledge Base
    print("2. Initializing Provisioner Agent with Multi-Cloud Knowledge Base...")
    print(f"   Knowledge Base ID: {os.getenv('KNOWLEDGE_BASE_ID')}")
    
    provisioner = ProvisionerAgent(
        agent_endpoint=os.getenv("PROVISIONER_AGENT_ENDPOINT"),
        agent_key=os.getenv("PROVISIONER_AGENT_KEY"),
        agent_id=os.getenv("PROVISIONER_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )
    print("   ✓ Provisioner Agent initialized")
    print()
    
    # Test 1: AWS-specific request
    print("=" * 80)
    print("TEST 1: AWS Infrastructure Generation")
    print("=" * 80)
    print("   Request: 'Deploy a Node.js application on AWS EC2 with RDS PostgreSQL'")
    print()
    
    request_aws = ProvisionRequest(
        request_id="kb-test-aws-1",
        user_id="test-user",
        description="Deploy a Node.js application on AWS EC2 with RDS PostgreSQL",
        region="us-east-1",
        environment="production",
        tags=["test", "aws", "multicloud"]
    )
    
    try:
        print("   Generating AWS Terraform configuration...")
        terraform_code_aws = await provisioner._generate_terraform(request_aws)
        
        print("   ✓ AWS Terraform code generated successfully!")
        print()
        print("   " + "-" * 76)
        print("   AWS TERRAFORM CODE PREVIEW:")
        print("   " + "-" * 76)
        
        # Show first 40 lines
        lines = terraform_code_aws.split('\n')
        for i, line in enumerate(lines[:40], 1):
            print(f"   {i:3d} | {line}")
        
        if len(lines) > 40:
            print(f"   ... ({len(lines) - 40} more lines)")
        
        print("   " + "-" * 76)
        print()
        
        # Check AWS-specific elements
        print("   Verifying AWS Knowledge Base integration...")
        aws_checks = {
            "AWS Provider": "provider \"aws\"" in terraform_code_aws or "hashicorp/aws" in terraform_code_aws,
            "EC2 Instance": "aws_instance" in terraform_code_aws,
            "RDS Database": "aws_db_instance" in terraform_code_aws,
            "Security Group": "aws_security_group" in terraform_code_aws,
            "VPC/Subnet": "vpc" in terraform_code_aws.lower() or "subnet" in terraform_code_aws.lower(),
            "AWS Region Variable": 'variable "aws_region"' in terraform_code_aws or "us-east-1" in terraform_code_aws,
        }
        
        print()
        for check_name, passed in aws_checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check_name}: {'PASS' if passed else 'FAIL'}")
        
        aws_passed = sum(aws_checks.values())
        aws_total = len(aws_checks)
        
        print()
        if aws_passed >= aws_total - 1:  # Allow 1 failure
            print(f"   🎉 AWS checks passed ({aws_passed}/{aws_total})!")
        else:
            print(f"   ⚠️  Only {aws_passed}/{aws_total} AWS checks passed")
        
    except Exception as e:
        print(f"   ✗ Error generating AWS infrastructure: {str(e)}")
        aws_passed = 0
        aws_total = 6
    
    print()
    
    # Test 2: DigitalOcean-specific request
    print("=" * 80)
    print("TEST 2: DigitalOcean Infrastructure Generation")
    print("=" * 80)
    print("   Request: 'Create a Node.js web app with MongoDB on DigitalOcean'")
    print()
    
    request_do = ProvisionRequest(
        request_id="kb-test-do-1",
        user_id="test-user",
        description="Create a Node.js web app with MongoDB on DigitalOcean",
        region="nyc3",
        environment="production",
        tags=["test", "digitalocean", "multicloud"]
    )
    
    try:
        print("   Generating DigitalOcean Terraform configuration...")
        terraform_code_do = await provisioner._generate_terraform(request_do)
        
        print("   ✓ DigitalOcean Terraform code generated successfully!")
        print()
        print("   " + "-" * 76)
        print("   DIGITALOCEAN TERRAFORM CODE PREVIEW:")
        print("   " + "-" * 76)
        
        # Show first 40 lines
        lines = terraform_code_do.split('\n')
        for i, line in enumerate(lines[:40], 1):
            print(f"   {i:3d} | {line}")
        
        if len(lines) > 40:
            print(f"   ... ({len(lines) - 40} more lines)")
        
        print("   " + "-" * 76)
        print()
        
        # Check DigitalOcean-specific elements
        print("   Verifying DigitalOcean Knowledge Base integration...")
        do_checks = {
            "DO Provider": "provider \"digitalocean\"" in terraform_code_do or "digitalocean/digitalocean" in terraform_code_do,
            "Droplet": "digitalocean_droplet" in terraform_code_do,
            "Database": "digitalocean_database_cluster" in terraform_code_do or "mongodb" in terraform_code_do.lower(),
            "DO Token Variable": 'variable "do_token"' in terraform_code_do,
            "Monitoring": "monitoring = true" in terraform_code_do,
            "SSH Keys": "ssh_keys" in terraform_code_do or "digitalocean_ssh_key" in terraform_code_do,
        }
        
        print()
        for check_name, passed in do_checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check_name}: {'PASS' if passed else 'FAIL'}")
        
        do_passed = sum(do_checks.values())
        do_total = len(do_checks)
        
        print()
        if do_passed >= do_total - 1:  # Allow 1 failure
            print(f"   🎉 DigitalOcean checks passed ({do_passed}/{do_total})!")
        else:
            print(f"   ⚠️  Only {do_passed}/{do_total} DigitalOcean checks passed")
        
    except Exception as e:
        print(f"   ✗ Error generating DigitalOcean infrastructure: {str(e)}")
        do_passed = 0
        do_total = 6
    
    print()
    
    # Final Results
    print("=" * 80)
    print("MULTI-CLOUD TEST RESULTS")
    print("=" * 80)
    print()
    
    total_passed = aws_passed + do_passed
    total_checks = aws_total + do_total
    
    print(f"   AWS Tests:          {aws_passed}/{aws_total} passed")
    print(f"   DigitalOcean Tests: {do_passed}/{do_total} passed")
    print(f"   Overall:            {total_passed}/{total_checks} passed")
    print()
    
    if total_passed >= total_checks - 2:  # Allow 2 total failures
        print("   🎉 Multi-Cloud Knowledge Base is working correctly!")
        print("   ✓ AWS infrastructure generation: READY")
        print("   ✓ DigitalOcean infrastructure generation: READY")
        print()
        print("   Next steps:")
        print("   1. Test from frontend UI with multi-cloud project creation")
        print("   2. Try provisioning with mixed queries (e.g., 'Deploy app on DO and DB on AWS')")
        print("   3. Monitor both cloud providers in the dashboard")
        success = True
    else:
        print("   ⚠️  Some tests failed. Possible reasons:")
        print("   - Knowledge base still indexing (wait 5-10 minutes)")
        print("   - Missing AWS or DigitalOcean examples in knowledge base")
        print("   - Agent needs more context in queries")
        success = False
    
    print()
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    print()
    print("Starting Multi-Cloud Knowledge Base integration test...")
    print("This will verify AWS and DigitalOcean infrastructure generation.")
    print()
    
    try:
        result = asyncio.run(test_multicloud_knowledge_base())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
