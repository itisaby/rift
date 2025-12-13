"""
Quick test to verify Gradient AI is responding for both AWS and DigitalOcean queries
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_gradient_responses():
    """Test if Gradient AI returns responses for AWS and DO queries"""
    
    endpoint = os.getenv("PROVISIONER_AGENT_ENDPOINT")
    api_key = os.getenv("PROVISIONER_AGENT_KEY")
    agent_id = os.getenv("PROVISIONER_AGENT_ID")
    kb_id = os.getenv("KNOWLEDGE_BASE_ID")
    
    print("=" * 80)
    print("GRADIENT AI RESPONSE TEST")
    print("=" * 80)
    print(f"Endpoint: {endpoint}")
    print(f"Agent ID: {agent_id}")
    print(f"Knowledge Base ID: {kb_id}")
    print()
    
    # Test 1: AWS Query
    print("TEST 1: AWS Infrastructure Query")
    print("-" * 80)
    
    aws_prompt = "Generate Terraform code for AWS EC2 instance with RDS PostgreSQL database"
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": aws_prompt
            }
        ],
        "stream": False,
        "include_retrieval_info": True,
        "knowledge_base_id": kb_id
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = f"{endpoint}/api/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Sending AWS query...")
        response = await client.post(url, json=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                print(f"Response length: {len(content)} characters")
                print(f"Preview: {content[:500]}...")
                print()
                
                if "aws" in content.lower() or "ec2" in content.lower():
                    print("✓ AWS-related content detected")
                else:
                    print("✗ No AWS-related content detected")
            else:
                print("✗ No choices in response")
        else:
            print(f"✗ Error: {response.text}")
        
        print()
    
    # Test 2: DigitalOcean Query
    print("TEST 2: DigitalOcean Infrastructure Query")
    print("-" * 80)
    
    do_prompt = "Generate Terraform code for DigitalOcean droplet with MongoDB database"
    
    payload["messages"] = [{"role": "user", "content": do_prompt}]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Sending DigitalOcean query...")
        response = await client.post(url, json=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                print(f"Response length: {len(content)} characters")
                print(f"Preview: {content[:500]}...")
                print()
                
                if "digitalocean" in content.lower() or "droplet" in content.lower():
                    print("✓ DigitalOcean-related content detected")
                else:
                    print("✗ No DigitalOcean-related content detected")
            else:
                print("✗ No choices in response")
        else:
            print(f"✗ Error: {response.text}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_gradient_responses())
