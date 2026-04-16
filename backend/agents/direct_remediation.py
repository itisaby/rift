"""
Direct Remediation Actions
Execute immediate fixes via MCP SSH and DigitalOcean API without Terraform
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("rift.agents.direct_remediation")


@dataclass
class RemediationResult:
    """Result of a direct remediation action"""
    success: bool
    message: str
    details: Dict[str, Any]
    logs: List[str]


class DirectRemediationExecutor:
    """
    Executes direct remediation actions on infrastructure
    without needing Terraform - for fast, safe operations.
    All SSH commands go through the infra MCP server.
    """

    def __init__(self, mcp_manager):
        """
        Initialize executor

        Args:
            mcp_manager: MCPSessionManager instance for MCP tool calls
        """
        self.mcp_manager = mcp_manager
        logger.info("Direct Remediation Executor initialized")

    async def execute_ssh_command(
        self,
        droplet_ip: str,
        command: str,
        timeout: int = 30
    ) -> tuple[bool, str, str]:
        """
        Execute SSH command on a droplet via infra MCP server.

        Args:
            droplet_ip: IP address of droplet
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            logger.info(f"Executing SSH command on {droplet_ip} via MCP: {command}")

            result = await self.mcp_manager.call("infra", "infra_execute_ssh_command", {
                "host": droplet_ip,
                "command": command,
                "timeout": timeout,
            })

            success = result.get("success", False)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")

            logger.info(f"SSH command {'succeeded' if success else 'failed'}")
            return success, stdout, stderr

        except Exception as e:
            logger.error(f"SSH MCP call failed: {str(e)}")
            return False, "", str(e)
    
    async def restart_service_action(
        self,
        droplet_ip: str,
        incident_details: Dict[str, Any]
    ) -> RemediationResult:
        """
        Restart service or kill runaway processes
        
        Strategy:
        1. Identify high CPU/memory processes
        2. Kill the offending process(es)
        3. Verify system recovery
        
        Args:
            droplet_ip: Droplet IP address
            incident_details: Incident metadata
            
        Returns:
            RemediationResult
        """
        logs = []
        logs.append(f"🔧 Starting service restart on {droplet_ip}")
        
        try:
            # Step 1: Identify top CPU consumers
            logs.append("Step 1: Identifying high resource processes...")
            
            ps_command = "ps aux --sort=-%cpu | head -n 10"
            success, stdout, stderr = await self.execute_ssh_command(droplet_ip, ps_command)
            
            if not success:
                return RemediationResult(
                    success=False,
                    message="Failed to query processes",
                    details={"error": stderr},
                    logs=logs
                )
            
            logs.append(f"Top processes:\n{stdout[:500]}")
            
            # Step 2: Parse and identify problem processes
            # Skip header and get processes using > 50% CPU
            lines = stdout.strip().split('\n')[1:]  # Skip header
            problem_pids = []
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 11:
                    try:
                        cpu_usage = float(parts[2])
                        pid = parts[1]
                        process_name = parts[10]
                        
                        # Kill processes using > 50% CPU (excluding system processes)
                        if cpu_usage > 50.0 and process_name not in ['systemd', 'kernel', 'init']:
                            problem_pids.append((pid, process_name, cpu_usage))
                            logs.append(f"⚠️  Found problem process: PID={pid} ({process_name}) using {cpu_usage}% CPU")
                    except (ValueError, IndexError):
                        continue
            
            if not problem_pids:
                # Check for stress testing processes specifically
                stress_check = "pgrep -a stress || pgrep -a stress-ng || true"
                success, stdout, stderr = await self.execute_ssh_command(droplet_ip, stress_check)
                
                if stdout.strip():
                    # Found stress processes
                    for line in stdout.strip().split('\n'):
                        parts = line.split()
                        if parts:
                            problem_pids.append((parts[0], 'stress', 100.0))
                            logs.append(f"⚠️  Found stress test process: PID={parts[0]}")
            
            if not problem_pids:
                logs.append("✓ No problematic processes found (CPU usage normalized)")
                return RemediationResult(
                    success=True,
                    message="No action needed - system healthy",
                    details={"processes_checked": len(lines)},
                    logs=logs
                )
            
            # Step 3: Kill problem processes
            logs.append(f"Step 2: Terminating {len(problem_pids)} problem process(es)...")
            
            killed_count = 0
            for pid, name, cpu in problem_pids:
                kill_command = f"kill -9 {pid}"
                success, stdout, stderr = await self.execute_ssh_command(droplet_ip, kill_command)
                
                if success:
                    logs.append(f"✓ Killed PID {pid} ({name}, {cpu}% CPU)")
                    killed_count += 1
                else:
                    logs.append(f"✗ Failed to kill PID {pid}: {stderr}")
            
            # Step 4: Wait for system to stabilize
            logs.append("Step 3: Waiting for system to stabilize (10 seconds)...")
            await asyncio.sleep(10)
            
            # Step 5: Verify recovery
            logs.append("Step 4: Verifying system recovery...")
            verify_command = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
            success, cpu_usage, stderr = await self.execute_ssh_command(droplet_ip, verify_command)
            
            if success and cpu_usage.strip():
                try:
                    current_cpu = float(cpu_usage.strip().replace('%us,', ''))
                    logs.append(f"✓ Current CPU usage: {current_cpu}%")
                    
                    if current_cpu < 60.0:  # Below our threshold
                        logs.append("✅ System recovered successfully!")
                        return RemediationResult(
                            success=True,
                            message=f"Successfully killed {killed_count} process(es) and verified recovery",
                            details={
                                "killed_processes": killed_count,
                                "final_cpu_usage": current_cpu,
                                "problem_pids": [{"pid": p[0], "name": p[1], "cpu": p[2]} for p in problem_pids]
                            },
                            logs=logs
                        )
                except ValueError:
                    pass
            
            # If we got here, we killed processes but couldn't verify
            logs.append("⚠️  Killed processes but couldn't verify full recovery")
            return RemediationResult(
                success=True,
                message=f"Killed {killed_count} process(es), verification incomplete",
                details={"killed_processes": killed_count},
                logs=logs
            )
            
        except Exception as e:
            logger.error(f"Service restart action failed: {str(e)}")
            logs.append(f"❌ Exception: {str(e)}")
            return RemediationResult(
                success=False,
                message=f"Remediation failed: {str(e)}",
                details={"error": str(e)},
                logs=logs
            )
    
    async def clean_disk_action(
        self,
        droplet_ip: str,
        incident_details: Dict[str, Any]
    ) -> RemediationResult:
        """
        Clean up disk space
        
        Strategy:
        1. Clean apt cache
        2. Remove old log files
        3. Clean temp directories
        4. Verify space freed
        
        Args:
            droplet_ip: Droplet IP address
            incident_details: Incident metadata
            
        Returns:
            RemediationResult
        """
        logs = []
        logs.append(f"🧹 Starting disk cleanup on {droplet_ip}")
        
        try:
            # Step 1: Check current disk usage
            logs.append("Step 1: Checking current disk usage...")
            df_command = "df -h / | tail -n 1"
            success, stdout, stderr = await self.execute_ssh_command(droplet_ip, df_command)
            
            if success:
                logs.append(f"Current disk usage:\n{stdout}")
                parts = stdout.split()
                if len(parts) >= 5:
                    initial_usage = parts[4]
                    logs.append(f"Initial usage: {initial_usage}")
            
            # Step 2: Clean apt cache
            logs.append("Step 2: Cleaning apt cache...")
            apt_clean = "apt-get clean && apt-get autoclean && apt-get autoremove -y"
            success, stdout, stderr = await self.execute_ssh_command(droplet_ip, apt_clean, timeout=60)
            
            if success:
                logs.append(f"✓ Apt cache cleaned: {stdout.strip()}")
            else:
                logs.append(f"⚠️  Apt clean warning: {stderr[:200]}")
            
            # Step 3: Clean old logs (keep last 7 days)
            logs.append("Step 3: Cleaning old log files...")
            log_clean = "find /var/log -type f -name '*.log.*' -mtime +7 -delete && find /var/log -type f -name '*.gz' -mtime +7 -delete"
            success, stdout, stderr = await self.execute_ssh_command(droplet_ip, log_clean)
            
            if success:
                logs.append("✓ Old log files removed")
            
            # Step 4: Clean temp directories
            logs.append("Step 4: Cleaning temporary directories...")
            temp_clean = "rm -rf /tmp/* /var/tmp/* 2>/dev/null || true"
            await self.execute_ssh_command(droplet_ip, temp_clean)
            logs.append("✓ Temp directories cleaned")
            
            # Step 5: Clean journal logs
            logs.append("Step 5: Cleaning journal logs (keep 7 days)...")
            journal_clean = "journalctl --vacuum-time=7d"
            success, stdout, stderr = await self.execute_ssh_command(droplet_ip, journal_clean)
            
            if success:
                logs.append(f"✓ Journal cleaned: {stdout.strip()[:100]}")
            
            # Step 6: Verify space freed
            logs.append("Step 6: Verifying disk space freed...")
            await asyncio.sleep(2)  # Let filesystem update
            
            success, stdout, stderr = await self.execute_ssh_command(droplet_ip, df_command)
            
            if success:
                logs.append(f"Final disk usage:\n{stdout}")
                parts = stdout.split()
                if len(parts) >= 5:
                    final_usage = parts[4]
                    available = parts[3]
                    logs.append(f"✅ Cleanup complete! Final usage: {final_usage}, Available: {available}")
                    
                    return RemediationResult(
                        success=True,
                        message="Disk cleanup completed successfully",
                        details={
                            "initial_usage": initial_usage if 'initial_usage' in locals() else "unknown",
                            "final_usage": final_usage,
                            "available": available
                        },
                        logs=logs
                    )
            
            # Generic success if we couldn't parse details
            return RemediationResult(
                success=True,
                message="Disk cleanup executed (verification incomplete)",
                details={},
                logs=logs
            )
            
        except Exception as e:
            logger.error(f"Disk cleanup action failed: {str(e)}")
            logs.append(f"❌ Exception: {str(e)}")
            return RemediationResult(
                success=False,
                message=f"Disk cleanup failed: {str(e)}",
                details={"error": str(e)},
                logs=logs
            )
    
    async def resize_droplet_action(
        self,
        droplet_id: int,
        new_size: str,
        incident_details: Dict[str, Any]
    ) -> RemediationResult:
        """
        Resize a droplet to a larger size
        
        Args:
            droplet_id: Droplet ID
            new_size: Target size slug (e.g., 's-2vcpu-2gb')
            incident_details: Incident metadata
            
        Returns:
            RemediationResult
        """
        logs = []
        logs.append(f"📈 Resizing droplet {droplet_id} to {new_size}")
        
        try:
            # Step 1: Get current droplet info
            logs.append("Step 1: Getting current droplet info...")
            droplet = await self.mcp_manager.call("do", "get_droplet", {"droplet_id": droplet_id})
            
            current_size = droplet.get("size", {}).get("slug", "unknown")
            logs.append(f"Current size: {current_size}")
            
            if current_size == new_size:
                logs.append("⚠️  Droplet is already the target size")
                return RemediationResult(
                    success=True,
                    message="No resize needed - already at target size",
                    details={"current_size": current_size, "target_size": new_size},
                    logs=logs
                )
            
            # Step 2: Power off droplet (required for resize)
            logs.append("Step 2: Powering off droplet...")
            power_off_result = await self.mcp_manager.call("do", "power_cycle_droplet", {"droplet_id": droplet_id})
            
            if not power_off_result:
                return RemediationResult(
                    success=False,
                    message="Failed to power off droplet",
                    details={"error": "power cycle failed"},
                    logs=logs
                )

            logs.append("✓ Droplet power cycle initiated")

            # Step 3: Wait for power-off to complete
            logs.append("Step 3: Waiting for power-off to complete...")
            await asyncio.sleep(10)

            # Step 4: Resize droplet
            logs.append(f"Step 4: Resizing to {new_size}...")
            resize_result = await self.mcp_manager.call("do", "resize_droplet", {"droplet_id": droplet_id, "new_size": new_size})

            if not resize_result:
                logs.append("❌ Resize failed, rebooting droplet...")
                await self.mcp_manager.call("do", "reboot_droplet", {"droplet_id": droplet_id})

                return RemediationResult(
                    success=False,
                    message="Resize operation failed",
                    details={"error": "resize call failed"},
                    logs=logs
                )

            logs.append("✓ Resize initiated")

            # Step 5: Wait for resize to complete
            logs.append("Step 5: Waiting for resize to complete (60 seconds)...")
            await asyncio.sleep(60)

            # Step 6: Reboot droplet
            logs.append("Step 6: Rebooting droplet...")
            await self.mcp_manager.call("do", "reboot_droplet", {"droplet_id": droplet_id})
            logs.append("✓ Droplet rebooted")

            # Step 7: Verify new size
            logs.append("Step 7: Verifying new size...")
            await asyncio.sleep(10)

            updated_droplet = await self.mcp_manager.call("do", "get_droplet", {"droplet_id": droplet_id})
            final_size = updated_droplet.get("size", {}).get("slug", "unknown")
            
            logs.append(f"✅ Resize complete! New size: {final_size}")
            
            return RemediationResult(
                success=True,
                message=f"Successfully resized from {current_size} to {final_size}",
                details={
                    "original_size": current_size,
                    "new_size": final_size,
                    "droplet_id": droplet_id
                },
                logs=logs
            )
            
        except Exception as e:
            logger.error(f"Resize action failed: {str(e)}")
            logs.append(f"❌ Exception: {str(e)}")
            return RemediationResult(
                success=False,
                message=f"Resize failed: {str(e)}",
                details={"error": str(e)},
                logs=logs
            )
