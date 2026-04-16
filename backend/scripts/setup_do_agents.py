#!/usr/bin/env python3
"""
Setup script for DigitalOcean Gradient AI agents and knowledge base.

Creates:
  1. A knowledge base with all docs from knowledge-base/
  2. Four AI agents: Monitor, Diagnostic, Remediation, Provisioner
  3. API keys for each agent
  4. Outputs a ready-to-use .env file

Usage:
  export DIGITALOCEAN_API_TOKEN=dop_v1_xxxx
  python scripts/setup_do_agents.py [--project-id <uuid>] [--region <region>]

If --project-id is not given, the script lists your projects and lets you pick.
If --region is not given, the script lists available GenAI regions and lets you pick.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE = "https://api.digitalocean.com/v2"
GENAI = f"{BASE}/gen-ai"

TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN", "")
if not TOKEN:
    print("ERROR: Set DIGITALOCEAN_API_TOKEN env var first.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

CLIENT = httpx.Client(headers=HEADERS, timeout=60)

# ── helpers ──────────────────────────────────────────────────────────────────

def api_get(path):
    r = CLIENT.get(f"{GENAI}/{path}")
    r.raise_for_status()
    return r.json()


def api_post(path, body):
    r = CLIENT.post(f"{GENAI}/{path}", json=body)
    if r.status_code >= 400:
        print(f"  ERROR {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()


def api_post_base(path, body):
    r = CLIENT.post(f"{BASE}/{path}", json=body)
    if r.status_code >= 400:
        print(f"  ERROR {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()


def list_projects():
    r = CLIENT.get(f"{BASE}/projects")
    r.raise_for_status()
    return r.json().get("projects", [])


def pick_project():
    projects = list_projects()
    if not projects:
        print("No projects found. Create one at cloud.digitalocean.com first.")
        sys.exit(1)
    print("\nAvailable projects:")
    for i, p in enumerate(projects):
        print(f"  [{i}] {p['name']}  (id: {p['id']})")
    choice = input("\nPick a project number: ").strip()
    return projects[int(choice)]["id"]


def list_regions():
    """List available GenAI regions."""
    return api_get("regions")


def pick_region():
    """Let user pick from available GenAI regions."""
    regions_data = list_regions()
    regions = regions_data.get("regions", [])
    if not regions:
        print("No GenAI regions found via API. Enter region manually.")
        return input("Region slug: ").strip()
    print("\nAvailable GenAI regions:")
    for i, r in enumerate(regions):
        slug = r.get("region", "unknown")
        caps = []
        if r.get("serves_inference"):
            caps.append("inference")
        if r.get("serves_batch"):
            caps.append("batch")
        cap_str = f"  ({', '.join(caps)})" if caps else ""
        print(f"  [{i}] {slug}{cap_str}")
    choice = input("\nPick a region number: ").strip()
    return regions[int(choice)]["region"]


def list_models():
    return api_get("models")


def pick_model(models_data):
    """Pick a chat/completion model from available models."""
    models = models_data.get("models", [])
    if not models:
        print("No models found via API.")
        sys.exit(1)
    print("\nAvailable models:")
    for i, m in enumerate(models):
        name = m.get("name", "unknown")
        uuid = m.get("uuid", "")
        mtype = m.get("type", "")
        print(f"  [{i}] {name}  type={mtype}  uuid={uuid}")
    choice = input("\nPick a model number for agents: ").strip()
    return models[int(choice)]["uuid"]


def pick_embedding_model(models_data):
    """Pick an embedding model for the knowledge base."""
    models = models_data.get("models", [])
    embedding_models = [m for m in models if "embed" in m.get("name", "").lower() or m.get("type", "") == "embedding"]
    if embedding_models:
        print("\nEmbedding models found:")
        for i, m in enumerate(embedding_models):
            print(f"  [{i}] {m.get('name')}  uuid={m.get('uuid')}")
        choice = input("\nPick an embedding model number: ").strip()
        return embedding_models[int(choice)]["uuid"]
    else:
        print("\nNo embedding models auto-detected. Enter embedding model UUID manually")
        print("(Check https://cloud.digitalocean.com/gen-ai for available embedding models)")
        return input("Embedding model UUID: ").strip()


def upload_file_to_kb(kb_uuid, file_path):
    """
    Upload a file to a knowledge base using the presigned URL flow:
    1. Request presigned URL from DO API
    2. Upload file to presigned URL
    3. Create data source referencing the uploaded file
    """
    file_name = file_path.name
    file_size = file_path.stat().st_size

    # Step 1: Get presigned upload URL
    presigned_body = {
        "files": [{"file_name": file_name, "size_in_bytes": file_size}]
    }
    presigned_resp = api_post(
        "knowledge_bases/data_sources/file_upload_presigned_urls",
        presigned_body,
    )

    uploads = presigned_resp.get("uploads", [])
    if not uploads:
        print(f"    WARN: No presigned URL returned for {file_name}")
        return False

    upload_info = uploads[0]
    presigned_url = upload_info.get("presigned_url", "")
    object_key = upload_info.get("object_key", "")

    if not presigned_url:
        print(f"    WARN: Empty presigned URL for {file_name}")
        return False

    # Step 2: Upload file to presigned URL (PUT with raw file content)
    with open(file_path, "rb") as f:
        file_data = f.read()

    upload_resp = httpx.put(
        presigned_url,
        content=file_data,
        headers={"Content-Type": "application/octet-stream"},
        timeout=120,
    )

    if upload_resp.status_code >= 400:
        print(f"    WARN: Presigned upload failed ({upload_resp.status_code}): {upload_resp.text[:200]}")
        return False

    # Step 3: Create data source referencing the uploaded file
    ds_body = {
        "file_upload_data_source": {
            "original_file_name": file_name,
            "size_in_bytes": str(file_size),
            "stored_object_key": object_key,
        }
    }
    try:
        api_post(f"knowledge_bases/{kb_uuid}/data_sources", ds_body)
        return True
    except Exception as e:
        print(f"    WARN: Data source creation failed: {e}")
        return False


# ── Agent definitions ────────────────────────────────────────────────────────

AGENTS = [
    {
        "name": "rift-monitor-agent",
        "env_prefix": "MONITOR",
        "description": "Infrastructure monitoring agent - detects anomalies via DigitalOcean and Prometheus metrics",
        "instruction": (
            "You are the Monitor Agent for the Rift infrastructure management platform. "
            "Your job is to analyze infrastructure metrics and classify incident severity. "
            "When given metric data (CPU, memory, disk usage), determine if thresholds are "
            "exceeded and classify severity as: critical (>95%), high (>20% over threshold), "
            "medium (>10% over threshold), or low. Consider the metric type, current value, "
            "and potential impact. Respond concisely with severity classification and brief reasoning. "
            "For trend analysis, identify patterns (spikes, sustained high, gradual increase) and "
            "predict whether thresholds will be exceeded soon."
        ),
    },
    {
        "name": "rift-diagnostic-agent",
        "env_prefix": "DIAGNOSTIC",
        "description": "Root cause analysis agent - diagnoses infrastructure incidents using RAG",
        "instruction": (
            "You are the Diagnostic Agent for the Rift infrastructure management platform. "
            "Your job is to diagnose root causes of infrastructure incidents. When given incident "
            "details (metric violations, infrastructure state, knowledge base context), provide a "
            "structured diagnosis in this exact format:\n\n"
            "ROOT CAUSE: [One sentence describing the root cause]\n"
            "CATEGORY: [capacity/performance/configuration/security/other]\n"
            "REASONING: [Detailed explanation]\n"
            "RECOMMENDATIONS: [Numbered list of 2-3 specific actionable recommendations]\n\n"
            "Use the knowledge base to find similar past incidents and proven resolutions. "
            "Be specific and actionable. When generating remediation plans, include Terraform "
            "configurations where applicable."
        ),
    },
    {
        "name": "rift-remediation-agent",
        "env_prefix": "REMEDIATION",
        "description": "Infrastructure remediation agent - generates and applies Terraform fixes",
        "instruction": (
            "You are the Remediation Agent for the Rift infrastructure management platform. "
            "Your job is to generate safe, production-ready Terraform configurations to fix "
            "infrastructure issues. When asked to generate Terraform for a remediation action, "
            "return ONLY valid HCL code with no markdown formatting. Use the DigitalOcean provider. "
            "Include all necessary variables, resource definitions, and outputs. Ensure operations "
            "are idempotent. When recording remediation results to the knowledge base, summarize "
            "the action taken, success status, and resources modified."
        ),
    },
    {
        "name": "rift-provisioner-agent",
        "env_prefix": "PROVISIONER",
        "description": "Infrastructure provisioning agent - creates resources from natural language",
        "instruction": (
            "You are the Provisioner Agent for the Rift infrastructure management platform. "
            "You generate complete, production-ready Terraform 1.x configurations from natural "
            "language infrastructure requests. Return ONLY valid Terraform HCL code, no markdown "
            "formatting or explanations. Always start with the terraform{} and provider blocks. "
            "For DigitalOcean: use digitalocean_droplet, digitalocean_database_cluster, "
            "digitalocean_loadbalancer resources. Include monitoring=true, user_data with Node "
            "Exporter install, tag 'rift' on all droplets, and ssh_keys for autonomous access. "
            "For AWS: use aws_instance, aws_db_instance, aws_lb resources. Use default VPC, avoid "
            "slow data source queries. Always include meaningful outputs with IDs, IPs, and "
            "connection strings."
        ),
    },
]


# ── Main setup ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Setup DO Gradient AI agents for Rift")
    parser.add_argument("--project-id", help="DO project UUID")
    parser.add_argument("--region", help="GenAI region (omit to pick interactively)")
    args = parser.parse_args()

    project_id = args.project_id or pick_project()

    # Pick region from available GenAI regions
    if args.region:
        region = args.region
    else:
        print("\nDiscovering available GenAI regions...")
        region = pick_region()

    print(f"\n{'='*60}")
    print(f"  Rift GenAI Setup")
    print(f"  Project: {project_id}")
    print(f"  Region:  {region}")
    print(f"{'='*60}\n")

    # Step 1: List models
    print("Step 1: Discovering available models...")
    models_data = list_models()
    model_uuid = pick_model(models_data)
    embedding_model_uuid = pick_embedding_model(models_data)
    print(f"  Agent model:     {model_uuid}")
    print(f"  Embedding model: {embedding_model_uuid}")

    # Step 2: Create knowledge base
    print("\nStep 2: Creating knowledge base...")
    kb_body = {
        "name": "rift-knowledge-base",
        "embedding_model_uuid": embedding_model_uuid,
        "project_id": project_id,
        "region": region,
        "tags": ["rift"],
    }
    kb_resp = api_post("knowledge_bases", kb_body)
    kb_data = kb_resp.get("knowledge_base", kb_resp)
    kb_uuid = kb_data.get("uuid") or kb_data.get("id")
    print(f"  Knowledge base created: {kb_uuid}")

    # Step 2b: Upload knowledge base files via presigned URL flow
    print("\nStep 2b: Uploading knowledge base documents...")
    kb_dir = Path(__file__).parent.parent / "knowledge-base"
    uploaded_count = 0
    for doc_file in sorted(kb_dir.glob("*.md")):
        if doc_file.name == "README.md":
            continue
        print(f"  Uploading {doc_file.name}...")
        if upload_file_to_kb(kb_uuid, doc_file):
            print(f"    Uploaded {doc_file.name}")
            uploaded_count += 1
        else:
            print(f"    Failed to upload {doc_file.name}")

    print(f"\n  Uploaded {uploaded_count} document(s)")

    # Wait for KB to be ready
    print("  Waiting for knowledge base indexing (30s)...")
    time.sleep(30)

    # Step 3: Create agents
    print("\nStep 3: Creating agents...")
    agent_configs = {}

    for agent_def in AGENTS:
        print(f"\n  Creating {agent_def['name']}...")
        agent_body = {
            "name": agent_def["name"],
            "description": agent_def["description"],
            "instruction": agent_def["instruction"],
            "model_uuid": model_uuid,
            "project_id": project_id,
            "region": region,
            "tags": ["rift"],
            "knowledge_base_uuid": [kb_uuid],
        }
        agent_resp = api_post("agents", agent_body)
        agent_data = agent_resp.get("agent", agent_resp)
        agent_uuid = agent_data.get("uuid") or agent_data.get("id")
        print(f"    Agent UUID: {agent_uuid}")

        # Wait a moment for agent to be ready
        time.sleep(5)

        # Get agent details to find endpoint URL
        agent_detail = api_get(f"agents/{agent_uuid}")
        agent_info = agent_detail.get("agent", agent_detail)
        deployment = agent_info.get("deployment", {})
        endpoint = deployment.get("url", "")
        if not endpoint:
            # Construct from agent UUID pattern
            endpoint = f"https://{agent_uuid}.agents.do-ai.run"
        print(f"    Endpoint: {endpoint}")

        # Create API key
        print(f"    Creating API key...")
        key_resp = api_post(f"agents/{agent_uuid}/api_keys", {"name": f"{agent_def['name']}-key"})
        key_data = key_resp.get("api_key", key_resp)
        api_key = key_data.get("key") or key_data.get("api_key") or key_data.get("token", "")
        print(f"    API Key: {api_key[:20]}..." if api_key else "    WARN: No key returned")

        agent_configs[agent_def["env_prefix"]] = {
            "uuid": agent_uuid,
            "endpoint": endpoint,
            "key": api_key,
        }

    # Step 4: Generate .env file
    print(f"\n{'='*60}")
    print("Step 4: Generating .env file...")

    env_path = Path(__file__).parent.parent / ".env"
    env_content = f"""# Rift Environment Configuration
# Generated by setup_do_agents.py
# {time.strftime('%Y-%m-%d %H:%M:%S')}

# ============================================
# Environment
# ============================================
ENVIRONMENT=development
DEMO_MODE=true

# ============================================
# API Configuration
# ============================================
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO

# ============================================
# DigitalOcean Configuration
# ============================================
DIGITALOCEAN_API_TOKEN={TOKEN}

# ============================================
# Prometheus Configuration
# ============================================
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_USER=
PROMETHEUS_PASSWORD=

# ============================================
# DigitalOcean Gradient AI - Monitor Agent
# ============================================
MONITOR_AGENT_ENDPOINT={agent_configs['MONITOR']['endpoint']}
MONITOR_AGENT_KEY={agent_configs['MONITOR']['key']}
MONITOR_AGENT_ID={agent_configs['MONITOR']['uuid']}

# ============================================
# DigitalOcean Gradient AI - Diagnostic Agent
# ============================================
DIAGNOSTIC_AGENT_ENDPOINT={agent_configs['DIAGNOSTIC']['endpoint']}
DIAGNOSTIC_AGENT_KEY={agent_configs['DIAGNOSTIC']['key']}
DIAGNOSTIC_AGENT_ID={agent_configs['DIAGNOSTIC']['uuid']}

# ============================================
# DigitalOcean Gradient AI - Remediation Agent
# ============================================
REMEDIATION_AGENT_ENDPOINT={agent_configs['REMEDIATION']['endpoint']}
REMEDIATION_AGENT_KEY={agent_configs['REMEDIATION']['key']}
REMEDIATION_AGENT_ID={agent_configs['REMEDIATION']['uuid']}

# ============================================
# DigitalOcean Gradient AI - Provisioner Agent
# ============================================
PROVISIONER_AGENT_ENDPOINT={agent_configs['PROVISIONER']['endpoint']}
PROVISIONER_AGENT_KEY={agent_configs['PROVISIONER']['key']}
PROVISIONER_AGENT_ID={agent_configs['PROVISIONER']['uuid']}

# ============================================
# Knowledge Base
# ============================================
KNOWLEDGE_BASE_ID={kb_uuid}

# ============================================
# Auto-Remediation Settings
# ============================================
AUTO_REMEDIATION_ENABLED=true
CONFIDENCE_THRESHOLD=0.85
MAX_COST_AUTO_APPROVE=50.00

# ============================================
# Terraform
# ============================================
TF_WORKING_DIR=/tmp/rift_terraform
TF_BINARY=terraform

# ============================================
# SSH (for autonomous remediation)
# ============================================
SSH_KEY_ID=
CONTROL_PLANE_IP=

# ============================================
# AWS (optional)
# ============================================
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
"""

    env_path.write_text(env_content)
    print(f"  Written to: {env_path}")

    # Summary
    print(f"\n{'='*60}")
    print("  SETUP COMPLETE!")
    print(f"{'='*60}")
    print(f"\n  Knowledge Base: {kb_uuid}")
    for prefix, cfg in agent_configs.items():
        print(f"  {prefix:13s} Agent: {cfg['uuid']}")
        print(f"  {' ':13s} Endpoint: {cfg['endpoint']}")
    print(f"\n  .env written to: {env_path}")
    print(f"\n  Next steps:")
    print(f"    1. Verify agents at https://cloud.digitalocean.com/gen-ai")
    print(f"    2. Fill in SSH_KEY_ID and CONTROL_PLANE_IP in .env")
    print(f"    3. Run: cd backend && python main.py")


if __name__ == "__main__":
    main()
