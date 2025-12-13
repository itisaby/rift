"""
Test AWS provisioning with fixed Terraform generation
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agents.provisioner_agent import ProvisionerAgent
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.provision_request import ProvisionRequest


async def test_aws_provisioning():
    """Test AWS EC2 provisioning"""
    
    print("=" * 80)
    print("AWS PROVISIONING TEST")
    print("=" * 80)
    print()
    
    # Initialize MCP clients
    terraform_mcp = TerraformMCP()
    do_mcp = DigitalOceanMCP(os.getenv("DIGITALOCEAN_API_TOKEN"))
    
    # Initialize Provisioner
    provisioner = ProvisionerAgent(
        agent_endpoint=os.getenv("PROVISIONER_AGENT_ENDPOINT"),
        agent_key=os.getenv("PROVISIONER_AGENT_KEY"),
        agent_id=os.getenv("PROVISIONER_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )
    
    print("✓ Provisioner initialized")
    print()
    
    # Create AWS EC2 request
    request = ProvisionRequest(
        request_id="test-aws-ec2",
        user_id="test-user",
        description="provision an EC2 instance in AWS",
        region="us-east-1",
        environment="development",
        tags=["test", "aws"]
    )
    
    print(f"📝 Request: {request.description}")
    print(f"🌍 Region: {request.region}")
    print()
    
    try:
        # Generate Terraform
        print("🔨 Generating Terraform configuration...")
        terraform_code = await provisioner._generate_terraform(request)
        
        print(f"✓ Generated {len(terraform_code)} bytes of Terraform")
        print()
        
        # Check for common issues
        print("🔍 Checking for deprecated syntax...")
        issues = []
        
        if "aws_subnet_ids" in terraform_code:
            issues.append("❌ DEPRECATED: Uses aws_subnet_ids (should be aws_subnets)")
        else:
            print("  ✓ No aws_subnet_ids found (good)")
        
        if "ipv4_address" in terraform_code:
            issues.append("❌ INCORRECT: Uses ipv4_address (should be public_ip)")
        else:
            print("  ✓ No ipv4_address found (good)")
        
        if "data \"aws_subnets\"" in terraform_code:
            print("  ✓ Uses aws_subnets data source (correct)")
        
        if "public_ip" in terraform_code:
            print("  ✓ Uses public_ip attribute (correct)")
        
        print()
        
        # Save to file
        with open("/tmp/test_aws_ec2.tf", "w") as f:
            f.write(terraform_code)
        print(f"💾 Saved to: /tmp/test_aws_ec2.tf")
        print()
        
        # Validate with Terraform
        print("✅ Validating with Terraform...")
        is_valid = await terraform_mcp.validate(terraform_code)
        
        if is_valid:
            print("  ✓ Terraform validation PASSED!")
            print()
            print("🎉 AWS provisioning is ready!")
            print()
            print("Next steps:")
            print("1. Test from frontend UI")
            print("2. Create a project with AWS credentials")
            print("3. Try query: 'provision an EC2 instance in AWS'")
        else:
            print("  ❌ Terraform validation FAILED")
            print()
            print("Issues found:")
            for issue in issues:
                print(f"  {issue}")
            print()
            print("📄 Review generated code at: /tmp/test_aws_ec2.tf")
        
        print()
        
        # Show preview
        print("=" * 80)
        print("GENERATED TERRAFORM PREVIEW (first 50 lines)")
        print("=" * 80)
        lines = terraform_code.split('\n')
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3d} | {line}")
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")
        print("=" * 80)
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_aws_provisioning())
    exit(0 if result else 1)
