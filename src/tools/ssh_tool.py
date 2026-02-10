"""
SSH Tool - Remote Command Execution on Windows Server
=====================================================

This module provides SSH connectivity to Windows Server for executing
PowerShell commands remotely. Uses paramiko for SSH connectivity.

Author: CrewAI Team
Version: 1.0.0
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

import paramiko
from paramiko import SSHClient, AutoAddPolicy
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class SSHConfig:
    """
    Configuration for SSH connection to Windows Server.
    
    Attributes:
        host: IP address or hostname of the Windows Server
        username: SSH username for authentication
        port: SSH port number (default: 22)
        password: SSH password for authentication
        key_path: Optional path to SSH private key file
        timeout: Connection timeout in seconds
    """
    host: str
    username: str
    port: int = 22
    password: Optional[str] = None
    key_path: Optional[str] = None
    timeout: int = 30


class SSHExecutor:
    """
    Executes commands remotely on Windows Server via SSH.
    
    This class manages SSH connections and provides methods for
    executing PowerShell commands on remote Windows Server.
    
    Attributes:
        config: SSH connection configuration
        client: Paramiko SSH client instance
        connected: Connection status flag
        
    Example:
        >>> config = SSHConfig(host='192.168.1.100', username='admin', password='pass')
        >>> ssh = SSHExecutor(config)
        >>> ssh.connect()
        >>> result = ssh.execute_command('powershell Get-Process')
        >>> ssh.disconnect()
    """
    
    def __init__(self, config: SSHConfig):
        """
        Initialize SSH executor with configuration.
        
        Args:
            config: SSHConfig instance with connection parameters
        """
        self.config = config
        self.client: Optional[SSHClient] = None
        self.connected = False
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"SSHExecutor initialized for host: {config.host}:{config.port}")
    
    def _validate_config(self) -> None:
        """
        Validate that required configuration is present.
        
        Raises:
            ValueError: If neither password nor key_path is provided
        """
        if not self.config.password and not self.config.key_path:
            raise ValueError(
                "Either SSH password or SSH key path must be provided"
            )
        
        # Check key file exists if path is provided
        if self.config.key_path:
            key_path = os.path.expanduser(self.config.key_path)
            if not os.path.exists(key_path):
                raise ValueError(f"SSH key file not found: {key_path}")
    
    def connect(self) -> bool:
        """
        Establish SSH connection to Windows Server.
        
        Uses exponential backoff retry strategy for robust connection handling.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            paramiko.AuthenticationException: If authentication fails
            paramiko.SSHException: If SSH protocol error occurs
            socket.error: If connection to host fails
        """
        if self.connected:
            logger.warning("Already connected to SSH server")
            return True
        
        self.client = SSHClient()
        
        # Set host key policy - AutoAddPolicy for known hosts
        # In production, consider using RejectPolicy for security
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        
        try:
            # Connect with retry logic
            self._connect_with_retry()
            
            self.connected = True
            logger.info(
                f"Successfully connected to {self.config.host}:{self.config.port}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SSH server: {e}")
            self.connected = False
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _connect_with_retry(self) -> None:
        """
        Internal connection method with retry logic.
        
        This method is decorated with tenacity for automatic retry
        on connection failures.
        """
        connect_params = {
            'hostname': self.config.host,
            'port': self.config.port,
            'username': self.config.username,
            'timeout': self.config.timeout,
        }
        
        # Add password or key authentication
        if self.config.password:
            connect_params['password'] = self.config.password
        elif self.config.key_path:
            key_path = os.path.expanduser(self.config.key_path)
            connect_params['key_filename'] = key_path
        
        self.client.connect(**connect_params)
    
    def disconnect(self) -> None:
        """
        Close SSH connection gracefully.
        
        Ensures proper cleanup of SSH client resources.
        """
        if self.client and self.connected:
            self.client.close()
            self.connected = False
            logger.info(f"Disconnected from {self.config.host}")
        else:
            logger.warning("No active SSH connection to disconnect")
    
    def execute_command(
        self,
        command: str,
        timeout: int = 60,
        powershell: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a command on the remote Windows Server.
        
        Args:
            command: Command to execute (without 'powershell' prefix if powershell=True)
            timeout: Command execution timeout in seconds
            powershell: If True, wraps command in 'powershell -Command'
            
        Returns:
            Dict containing:
                - success: bool indicating if command succeeded
                - stdout: standard output from command
                - stderr: standard error from command
                - return_code: exit code from command
                
        Example:
            >>> ssh.execute_command('Get-Process calc', powershell=True)
            {'success': True, 'stdout': '...', 'stderr': '', 'return_code': 0}
        """
        if not self.connected:
            raise RuntimeError("Not connected to SSH server. Call connect() first.")
        
        # Build the full command
        if powershell:
            full_command = f'powershell -Command "{command}"'
        else:
            full_command = command
        
        logger.debug(f"Executing command: {full_command}")
        
        try:
            # Execute command
            stdin, stdout, stderr = self.client.exec_command(
                full_command,
                timeout=timeout
            )
            
            # Read output
            stdout_content = stdout.read().decode('utf-8', errors='replace')
            stderr_content = stderr.read().decode('utf-8', errors='replace')
            exit_code = stdout.channel.recv_exit_status()
            
            result = {
                'success': exit_code == 0,
                'stdout': stdout_content.strip(),
                'stderr': stderr_content.strip(),
                'return_code': exit_code
            }
            
            logger.debug(
                f"Command exit code: {exit_code}, stdout length: {len(stdout_content)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1
            }
    
    def execute_script(
        self,
        script_path: str,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Execute a PowerShell script file on the remote server.
        
        Args:
            script_path: Path to PowerShell script on remote server
            timeout: Execution timeout in seconds
            
        Returns:
            Dict with command execution results
        """
        command = f'& "{script_path}"'
        return self.execute_command(command, timeout=timeout, powershell=True)
    
    def is_connected(self) -> bool:
        """
        Check if SSH connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def __enter__(self) -> 'SSHExecutor':
        """Context manager entry - connects to SSH server."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - disconnects from SSH server."""
        self.disconnect()
    
    def __repr__(self) -> str:
        """String representation of SSHExecutor instance."""
        return (
            f"SSHExecutor(host={self.config.host}, "
            f"port={self.config.port}, "
            f"username={self.config.username}, "
            f"connected={self.connected})"
        )