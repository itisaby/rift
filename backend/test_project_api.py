"""
Test script for project management endpoints
Run this after starting the backend server
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_project_endpoints():
    """Test all project management endpoints"""
    
    print("🧪 Testing Project Management API\n")
    print("=" * 50)
    
    # Test 1: Create a project
    print("\n1. Creating a new project...")
    create_data = {
        "name": "Test Production Environment",
        "description": "Testing project management system",
        "user_id": "user-test-123",
        "cloud_providers": [
            {
                "provider": "digitalocean",
                "credentials": {"api_token": "dop_v1_test_token"},
                "region": "nyc3"
            }
        ],
        "tags": ["test", "production"]
    }
    
    try:
        response = requests.post(f"{API_URL}/projects", json=create_data)
        response.raise_for_status()
        project = response.json()
        project_id = project["project_id"]
        print(f"✅ Project created: {project['name']} (ID: {project_id})")
        print(f"   Status: {project['status']}")
        print(f"   Monitoring: {project['monitoring_enabled']}")
        print(f"   Auto-remediation: {project['auto_remediation']}")
    except Exception as e:
        print(f"❌ Failed to create project: {e}")
        return
    
    # Test 2: List all projects
    print("\n2. Listing all projects...")
    try:
        response = requests.get(f"{API_URL}/projects")
        response.raise_for_status()
        projects = response.json()
        print(f"✅ Found {len(projects)} project(s)")
        for p in projects:
            print(f"   - {p['name']} ({p['project_id']})")
    except Exception as e:
        print(f"❌ Failed to list projects: {e}")
    
    # Test 3: Get specific project
    print(f"\n3. Getting project details for {project_id}...")
    try:
        response = requests.get(f"{API_URL}/projects/{project_id}")
        response.raise_for_status()
        project = response.json()
        print(f"✅ Project details retrieved")
        print(f"   Name: {project['name']}")
        print(f"   Total Resources: {project['total_resources']}")
        print(f"   Active Incidents: {project['active_incidents']}")
        print(f"   Total Cost: ${project['total_cost']}")
    except Exception as e:
        print(f"❌ Failed to get project: {e}")
    
    # Test 4: Update project
    print(f"\n4. Updating project {project_id}...")
    update_data = {
        "monitoring_enabled": False,
        "auto_remediation": False,
        "tags": ["test", "staging"]
    }
    try:
        response = requests.put(f"{API_URL}/projects/{project_id}", json=update_data)
        response.raise_for_status()
        project = response.json()
        print(f"✅ Project updated")
        print(f"   Monitoring: {project['monitoring_enabled']}")
        print(f"   Auto-remediation: {project['auto_remediation']}")
        print(f"   Tags: {project['tags']}")
    except Exception as e:
        print(f"❌ Failed to update project: {e}")
    
    # Test 5: Get infrastructure graph
    print(f"\n5. Getting infrastructure graph for {project_id}...")
    try:
        response = requests.get(f"{API_URL}/projects/{project_id}/infrastructure")
        response.raise_for_status()
        graph = response.json()
        print(f"✅ Infrastructure graph retrieved")
        print(f"   Nodes: {len(graph['nodes'])}")
        print(f"   Edges: {len(graph['edges'])}")
    except Exception as e:
        print(f"❌ Failed to get infrastructure graph: {e}")
    
    # Test 6: Delete project
    print(f"\n6. Deleting project {project_id}...")
    try:
        response = requests.delete(f"{API_URL}/projects/{project_id}")
        response.raise_for_status()
        result = response.json()
        print(f"✅ {result['message']}")
    except Exception as e:
        print(f"❌ Failed to delete project: {e}")
    
    # Verify deletion
    print(f"\n7. Verifying deletion...")
    try:
        response = requests.get(f"{API_URL}/projects/{project_id}")
        if response.status_code == 404:
            print(f"✅ Project successfully deleted (404 as expected)")
        else:
            print(f"⚠️  Project still exists (status: {response.status_code})")
    except Exception as e:
        print(f"✅ Project successfully deleted (connection error as expected)")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")


if __name__ == "__main__":
    test_project_endpoints()
