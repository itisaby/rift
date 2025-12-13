#!/usr/bin/env python3
"""
Rift Setup Verification Script
Checks that all Phase 1 requirements are met
"""

import os
import sys
from pathlib import Path

def check_mark(passed: bool) -> str:
    """Return check mark or X based on status"""
    return "✅" if passed else "❌"

def verify_environment():
    """Verify .env file exists and has required variables"""
    print("\n🔧 Checking Environment Configuration...")

    env_file = Path(".env")
    if not env_file.exists():
        print(f"  {check_mark(False)} .env file not found")
        print("     Run: cp .env.example .env (if you have one)")
        return False

    print(f"  {check_mark(True)} .env file exists")

    # Check for required variables
    required_vars = [
        "DIGITALOCEAN_API_TOKEN",
        "MONITOR_AGENT_ENDPOINT",
        "MONITOR_AGENT_KEY",
        "DIAGNOSTIC_AGENT_ENDPOINT",
        "DIAGNOSTIC_AGENT_KEY",
        "REMEDIATION_AGENT_ENDPOINT",
        "REMEDIATION_AGENT_KEY",
        "KNOWLEDGE_BASE_ID",
        "API_SECRET_KEY"
    ]

    missing_vars = []
    for var in required_vars:
        # Try to load from environment or check if placeholder
        value = os.getenv(var, "")
        if not value or "your_" in value.lower() or "xxxxx" in value:
            missing_vars.append(var)

    if missing_vars:
        print(f"  {check_mark(False)} Missing or incomplete environment variables:")
        for var in missing_vars:
            print(f"     - {var}")
        return False
    else:
        print(f"  {check_mark(True)} All required environment variables set")
        return True

def verify_dependencies():
    """Verify Python dependencies are installed"""
    print("\n📦 Checking Python Dependencies...")

    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "aiohttp",
        "structlog",
        "python-dotenv"
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  {check_mark(True)} {package}")
        except ImportError:
            print(f"  {check_mark(False)} {package}")
            missing.append(package)

    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False

    return True

def verify_structure():
    """Verify project structure"""
    print("\n📁 Checking Project Structure...")

    required_dirs = [
        "agents",
        "mcp_clients",
        "orchestrator",
        "models",
        "utils",
        "terraform",
        "demo",
        "tests",
        "knowledge-base",
        "logs"
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        exists = dir_path.exists() and dir_path.is_dir()
        print(f"  {check_mark(exists)} {dir_name}/")
        if not exists:
            all_exist = False

    return all_exist

def verify_files():
    """Verify key files exist"""
    print("\n📄 Checking Key Files...")

    required_files = [
        "main.py",
        "requirements.txt",
        ".env",
        "README.md",
        "SETUP.md",
        "models/incident.py",
        "utils/config.py",
        "utils/logger.py",
        "knowledge-base/runbooks.md"
    ]

    all_exist = True
    for file_name in required_files:
        file_path = Path(file_name)
        exists = file_path.exists() and file_path.is_file()
        print(f"  {check_mark(exists)} {file_name}")
        if not exists:
            all_exist = False

    return all_exist

def verify_models():
    """Verify data models can be imported"""
    print("\n🔍 Checking Data Models...")

    try:
        from models.incident import (
            Incident, Diagnosis, RemediationPlan,
            RemediationResult, SystemStatus, AgentHealth
        )
        print(f"  {check_mark(True)} All models import successfully")
        return True
    except Exception as e:
        print(f"  {check_mark(False)} Model import failed: {e}")
        return False

def verify_config():
    """Verify configuration can be loaded"""
    print("\n⚙️  Checking Configuration...")

    try:
        from utils.config import get_settings
        settings = get_settings()
        print(f"  {check_mark(True)} Configuration loads successfully")
        print(f"     Environment: {settings.environment}")
        print(f"     Demo Mode: {settings.demo_mode}")
        print(f"     Auto Remediation: {settings.auto_remediation_enabled}")
        return True
    except Exception as e:
        print(f"  {check_mark(False)} Configuration load failed: {e}")
        return False

def check_external_tools():
    """Check external tools availability"""
    print("\n🛠️  Checking External Tools...")

    tools = {
        "doctl": "DigitalOcean CLI",
        "terraform": "Terraform",
        "python3": "Python 3"
    }

    all_available = True
    for cmd, name in tools.items():
        available = os.system(f"which {cmd} > /dev/null 2>&1") == 0
        print(f"  {check_mark(available)} {name} ({cmd})")
        if not available:
            all_available = False

    return all_available

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("🤖 Rift Setup Verification")
    print("=" * 60)

    checks = [
        ("Project Structure", verify_structure),
        ("Key Files", verify_files),
        ("Python Dependencies", verify_dependencies),
        ("Data Models", verify_models),
        ("Environment Configuration", verify_environment),
        ("Configuration Loading", verify_config),
        ("External Tools", check_external_tools)
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n  ❌ Error running {check_name}: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        print(f"  {check_mark(result)} {check_name}")

    print(f"\n  Score: {passed}/{total} checks passed")

    if passed == total:
        print("\n  🎉 Phase 1 setup is complete!")
        print("  Next steps:")
        print("    1. Review SETUP.md for infrastructure setup")
        print("    2. Create DigitalOcean droplets")
        print("    3. Set up Gradient AI agents")
        print("    4. Configure environment variables")
        print("    5. Start Phase 2: Monitor Agent")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} check(s) failed")
        print("  Please fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())
