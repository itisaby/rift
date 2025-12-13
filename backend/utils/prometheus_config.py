"""
Prometheus Configuration Manager
Automatically updates Prometheus to monitor newly provisioned droplets
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger("rift.prometheus_config")


class PrometheusConfigManager:
    """
    Manages Prometheus configuration for automatic target discovery
    """
    
    def __init__(self, control_plane_ip: str, ssh_key_path: str = "~/.ssh/id_ed25519_do_rift"):
        """
        Initialize Prometheus configuration manager
        
        Args:
            control_plane_ip: IP address of control-plane droplet running Prometheus
            ssh_key_path: Path to SSH key for authentication
        """
        self.control_plane_ip = control_plane_ip
        self.ssh_key_path = ssh_key_path
        logger.info(f"Initialized PrometheusConfigManager for {control_plane_ip}")
    
    async def add_target(
        self,
        job_name: str,
        target_ip: str,
        target_port: int = 9100,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Add a new monitoring target to Prometheus
        
        Args:
            job_name: Name for the Prometheus job (e.g., 'web-app', 'api-server')
            target_ip: IP address of the target to monitor
            target_port: Port number (default: 9100 for Node Exporter)
            labels: Additional labels for the target
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Adding Prometheus target: {job_name} -> {target_ip}:{target_port}")
            
            # Step 1: Backup current config
            backup_success = await self._backup_config()
            if not backup_success:
                logger.warning("Failed to backup Prometheus config, continuing anyway...")
            
            # Step 2: Read current config
            current_config = await self._read_config()
            if not current_config:
                logger.error("Failed to read current Prometheus config")
                return False
            
            # Step 3: Add new target
            new_config = self._add_target_to_config(
                current_config,
                job_name,
                target_ip,
                target_port,
                labels
            )
            
            # Step 4: Write new config
            write_success = await self._write_config(new_config)
            if not write_success:
                logger.error("Failed to write new Prometheus config")
                return False
            
            # Step 5: Reload Prometheus
            reload_success = await self._reload_prometheus()
            if not reload_success:
                logger.error("Failed to reload Prometheus")
                # Try to restore backup
                await self._restore_backup()
                return False
            
            logger.info(f"✓ Successfully added Prometheus target: {job_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add Prometheus target: {str(e)}", exc_info=True)
            return False
    
    async def remove_target(self, job_name: str) -> bool:
        """
        Remove a monitoring target from Prometheus
        
        Args:
            job_name: Name of the job to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Removing Prometheus target: {job_name}")
            
            # Backup, read, modify, write, reload (same pattern as add)
            await self._backup_config()
            current_config = await self._read_config()
            if not current_config:
                return False
            
            new_config = self._remove_target_from_config(current_config, job_name)
            
            if not await self._write_config(new_config):
                return False
            
            if not await self._reload_prometheus():
                await self._restore_backup()
                return False
            
            logger.info(f"✓ Successfully removed Prometheus target: {job_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove Prometheus target: {str(e)}", exc_info=True)
            return False
    
    async def _execute_ssh_command(self, command: str, timeout: int = 30) -> tuple[bool, str, str]:
        """Execute SSH command on control-plane"""
        try:
            import os
            ssh_key = os.path.expanduser(self.ssh_key_path)
            
            ssh_command = [
                "ssh",
                "-i", ssh_key,
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", f"ConnectTimeout={timeout}",
                f"root@{self.control_plane_ip}",
                command
            ]
            
            process = await asyncio.create_subprocess_exec(
                *ssh_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            success = process.returncode == 0
            return success, stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')
            
        except asyncio.TimeoutError:
            logger.error(f"SSH command timed out after {timeout}s")
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            logger.error(f"SSH command failed: {str(e)}")
            return False, "", str(e)
    
    async def _backup_config(self) -> bool:
        """Backup current Prometheus config"""
        # Try both possible locations
        command = "cp /etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml.backup 2>/dev/null || cp /root/prometheus-*/prometheus.yml /root/prometheus-*/prometheus.yml.backup"
        success, _, _ = await self._execute_ssh_command(command)
        return success
    
    async def _restore_backup(self) -> bool:
        """Restore Prometheus config from backup"""
        command = "cp /etc/prometheus/prometheus.yml.backup /etc/prometheus/prometheus.yml 2>/dev/null || cp /root/prometheus-*/prometheus.yml.backup /root/prometheus-*/prometheus.yml"
        success, _, _ = await self._execute_ssh_command(command)
        return success
    
    async def _read_config(self) -> Optional[str]:
        """Read current Prometheus config"""
        # Try /etc/prometheus first, then /root/prometheus-*
        command = "cat /etc/prometheus/prometheus.yml 2>/dev/null || cat /root/prometheus-*/prometheus.yml 2>/dev/null"
        success, stdout, _ = await self._execute_ssh_command(command)
        return stdout if success else None
    
    async def _write_config(self, config: str) -> bool:
        """Write new Prometheus config"""
        # Escape single quotes in config
        escaped_config = config.replace("'", "'\\''")
        # Try to write to both possible locations
        command = f"(echo '{escaped_config}' | tee /etc/prometheus/prometheus.yml > /dev/null 2>&1) || (echo '{escaped_config}' | tee /root/prometheus-*/prometheus.yml > /dev/null)"
        success, _, _ = await self._execute_ssh_command(command)
        return success
    
    async def _reload_prometheus(self) -> bool:
        """Reload Prometheus to pick up new config"""
        # Try systemctl first, then send SIGHUP to process
        command = "systemctl reload prometheus 2>/dev/null || systemctl restart prometheus 2>/dev/null || pkill -HUP prometheus"
        success, _, _ = await self._execute_ssh_command(command)
        return success
    
    def _add_target_to_config(
        self,
        config: str,
        job_name: str,
        target_ip: str,
        target_port: int,
        labels: Optional[Dict[str, str]]
    ) -> str:
        """
        Add a new scrape target to Prometheus config
        
        This is a simple implementation that appends a new scrape job.
        For production, you'd want to parse YAML properly.
        """
        # Simple approach: append new job at the end
        new_job = f"""
  - job_name: '{job_name}'
    static_configs:
      - targets: ['{target_ip}:{target_port}']"""
        
        if labels:
            labels_str = ", ".join([f"{k}: '{v}'" for k, v in labels.items()])
            new_job += f"""
        labels:
          {labels_str}"""
        
        return config + new_job + "\n"
    
    def _remove_target_from_config(self, config: str, job_name: str) -> str:
        """
        Remove a scrape target from Prometheus config
        
        Simple implementation - for production, use proper YAML parsing
        """
        lines = config.split('\n')
        new_lines = []
        skip_until_next_job = False
        
        for line in lines:
            if f"job_name: '{job_name}'" in line or f'job_name: "{job_name}"' in line:
                skip_until_next_job = True
                continue
            
            if skip_until_next_job:
                # Keep skipping until we hit the next job or end of scrape_configs
                if line.strip().startswith('- job_name:') or line.strip() == '':
                    skip_until_next_job = False
                else:
                    continue
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
