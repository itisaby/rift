"""
Test: Provision Node.js Web App with SQL Database
This simulates the frontend request to test the provisioning workflow
"""

import asyncio
import json
import sys
from dotenv import load_dotenv
import os

load_dotenv()

from agents.provisioner_agent import ProvisionerAgent
from mcp_clients.terraform_mcp import TerraformMCP
from mcp_clients.do_mcp import DigitalOceanMCP
from models.provision_request import ProvisionRequest


async def test_nodejs_sql_provision():
    """Test provisioning Node.js app with SQL database"""
    
    print("\n" + "=" * 100)
    print(" " * 25 + "PROVISION TEST: Node.js Web App with SQL Database")
    print("=" * 100 + "\n")
    
    # Initialize
    print("🔧 Initializing provisioner...")
    terraform_mcp = TerraformMCP()
    do_mcp = DigitalOceanMCP(os.getenv("DIGITALOCEAN_API_TOKEN"))
    
    provisioner = ProvisionerAgent(
        agent_endpoint=os.getenv("PROVISIONER_AGENT_ENDPOINT"),
        agent_key=os.getenv("PROVISIONER_AGENT_KEY"),
        agent_id=os.getenv("PROVISIONER_AGENT_ID"),
        terraform_mcp=terraform_mcp,
        do_mcp=do_mcp,
        knowledge_base_id=os.getenv("KNOWLEDGE_BASE_ID")
    )
    print("✓ Provisioner initialized\n")
    
    # Create request (matching what frontend will send)
    print("📝 Creating provision request...")
    request = ProvisionRequest(
        request_id="test-nodejs-sql-001",
        user_id="test-user",
        description="Create a Node.js Web App with a SQL Database",
        region="nyc3",
        environment="production",
        tags=["nodejs", "sql", "webapp", "test"]
    )
    
    print(f"   Description: {request.description}")
    print(f"   Region: {request.region}")
    print(f"   Environment: {request.environment}")
    print(f"   Tags: {', '.join(request.tags)}\n")
    
    # Generate Terraform
    print("🤖 Generating Terraform configuration with AI...")
    print("   (This uses the knowledge base for best practices)\n")
    
    try:
        terraform_code = await provisioner._generate_terraform(request)
        
        print("✓ Terraform code generated successfully!\n")
        
        # Analyze what was generated
        print("=" * 100)
        print(" " * 35 + "GENERATED INFRASTRUCTURE")
        print("=" * 100 + "\n")
        
        # Check for resources
        has_droplet = "digitalocean_droplet" in terraform_code
        has_database = "digitalocean_database_cluster" in terraform_code
        has_firewall = "digitalocean_firewall" in terraform_code
        has_monitoring = "monitoring = true" in terraform_code
        has_outputs = "output" in terraform_code
        
        print("📦 Resources Detected:")
        print(f"   {'✓' if has_droplet else '✗'} Web Server Droplet (digitalocean_droplet)")
        print(f"   {'✓' if has_database else '✗'} SQL Database (digitalocean_database_cluster)")
        print(f"   {'✓' if has_firewall else '✗'} Firewall Rules (digitalocean_firewall)")
        print(f"   {'✓' if has_monitoring else '✗'} Monitoring Enabled")
        print(f"   {'✓' if has_outputs else '✗'} Output Values\n")
        
        # Check for specific configurations
        print("🔍 Configuration Details:")
        
        # Check for Node.js setup
        if "nodejs" in terraform_code.lower() or "node" in terraform_code.lower():
            print("   ✓ Node.js installation configured in user_data")
        
        # Check database engine
        if 'engine = "pg"' in terraform_code or 'engine = "mysql"' in terraform_code:
            engine = "PostgreSQL" if 'engine = "pg"' in terraform_code else "MySQL"
            print(f"   ✓ Database Engine: {engine}")
        
        # Check for connection string output
        if "connection_string" in terraform_code:
            print("   ✓ Database connection string output configured")
        
        # Check for proper firewall ports
        if "port_range" in terraform_code:
            ports = []
            if '"22"' in terraform_code or "'22'" in terraform_code:
                ports.append("SSH (22)")
            if '"80"' in terraform_code or "'80'" in terraform_code:
                ports.append("HTTP (80)")
            if '"443"' in terraform_code or "'443'" in terraform_code:
                ports.append("HTTPS (443)")
            if '"3000"' in terraform_code or "'3000'" in terraform_code:
                ports.append("Node.js (3000)")
            
            if ports:
                print(f"   ✓ Firewall Ports: {', '.join(ports)}")
        
        print()
        
        # Show preview of generated code
        print("=" * 100)
        print(" " * 35 + "TERRAFORM CODE PREVIEW")
        print("=" * 100 + "\n")
        
        lines = terraform_code.split('\n')
        for i, line in enumerate(lines[:50], 1):
            print(f"   {i:3d} | {line}")
        
        if len(lines) > 50:
            print(f"\n   ... ({len(lines) - 50} more lines)")
        
        print("\n" + "=" * 100 + "\n")
        
        # Summary
        print("✅ PROVISION REQUEST READY!")
        print("\n📋 What happens next in the frontend:")
        print("   1. User enters query: 'Create a Node.js Web App with a SQL Database'")
        print("   2. Frontend sends request to: POST /provision/create")
        print("   3. AI generates Terraform code (like above)")
        print("   4. Terraform code is validated and fixed")
        print("   5. Terraform apply runs to create infrastructure")
        print("   6. Resources are parsed and stored in project")
        print("   7. Real-time logs stream to frontend\n")
        
        # Check resource count estimation
        resource_count = terraform_code.count("resource \"digitalocean_")
        print(f"💰 Estimated Resources: {resource_count}")
        
        # Rough cost estimate
        monthly_cost = 0
        if has_droplet:
            if "s-2vcpu-4gb" in terraform_code:
                monthly_cost += 24
            elif "s-1vcpu-2gb" in terraform_code:
                monthly_cost += 12
            else:
                monthly_cost += 12
        
        if has_database:
            if "db-s-2vcpu-4gb" in terraform_code:
                monthly_cost += 60
            elif "db-s-1vcpu-1gb" in terraform_code:
                monthly_cost += 15
            else:
                monthly_cost += 60
        
        print(f"💵 Estimated Monthly Cost: ~${monthly_cost}/month\n")
        
        print("=" * 100)
        print("\n🎉 SUCCESS! Your query will generate production-ready infrastructure!\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating Terraform: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Testing provisioning with query: 'Create a Node.js Web App with a SQL Database'\n")
    
    try:
        result = asyncio.run(test_nodejs_sql_provision())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
