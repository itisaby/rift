#!/usr/bin/env python3
"""
Test Prometheus Auto-Registration
Tests that new droplets are automatically registered with Prometheus
"""

import asyncio
import sys
sys.path.insert(0, '.')

from utils.prometheus_config import PrometheusConfigManager


async def test_prometheus_registration():
    """Test adding a target to Prometheus"""
    
    print("Testing Prometheus Auto-Registration")
    print("=" * 60)
    
    # Initialize manager
    control_plane_ip = "104.236.4.131"
    manager = PrometheusConfigManager(control_plane_ip)
    
    print(f"\n1. Testing connection to control-plane ({control_plane_ip})...")
    success, stdout, stderr = await manager._execute_ssh_command("echo 'Connection test'")
    
    if not success:
        print(f"❌ Failed to connect to control-plane")
        print(f"Error: {stderr}")
        return False
    
    print(f"✓ Connected successfully")
    
    # Test reading current config
    print(f"\n2. Reading current Prometheus configuration...")
    config = await manager._read_config()
    
    if not config:
        print("❌ Failed to read Prometheus config")
        return False
    
    print(f"✓ Config read successfully ({len(config)} bytes)")
    print(f"\nCurrent scrape jobs:")
    for line in config.split('\n'):
        if 'job_name:' in line:
            print(f"  {line.strip()}")
    
    # Test adding a dummy target (but don't actually add it)
    print(f"\n3. Simulating target addition...")
    test_job_name = "test-droplet"
    test_ip = "192.0.2.1"  # TEST-NET-1 (documentation use only)
    
    new_config = manager._add_target_to_config(
        config,
        test_job_name,
        test_ip,
        9100,
        {'env': 'test', 'managed_by': 'rift'}
    )
    
    if test_job_name in new_config and test_ip in new_config:
        print(f"✓ Target would be added correctly")
        print(f"\nNew job config:")
        for line in new_config.split('\n')[-10:]:
            if line.strip():
                print(f"  {line}")
    else:
        print(f"❌ Failed to add target to config")
        return False
    
    print(f"\n" + "=" * 60)
    print("✓ All tests passed!")
    print(f"\nNote: No actual changes were made to Prometheus configuration")
    print(f"To actually register a new droplet, it will happen automatically")
    print(f"during provisioning via the Provisioner Agent.")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_prometheus_registration())
    sys.exit(0 if result else 1)
