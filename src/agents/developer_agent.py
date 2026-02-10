"""
Developer Agent - Implements Rollback Functionality
====================================================

This agent is responsible for:
- Implementing the main rollback logic
- Executing the rollback workflow
- Coordinating with other agents
- Handling errors and recovery

Author: CrewAI Team
Version: 1.0.0
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from crewai import Agent

from ..tools.ssh_tool import SSHExecutor, SSHConfig
from ..tools.iis_tool import IISManager
from ..tools.backup_tool import BackupManager, RollbackMode

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class RollbackConfig:
    """
    Configuration for the rollback operation.
    
    Attributes:
        site_name: Name of the IIS site
        site_path: Path to the IIS site root
        backup_path: Path to the backup directory
        ssh_config: SSH connection configuration
    """
    site_name: str
    site_path: str
    backup_path: str
    ssh_config: SSHConfig


@dataclass
class RollbackResult:
    """
    Result of the rollback operation.
    
    Attributes:
        success: Whether the rollback succeeded
        mode: Rollback mode used (ZIP or FOLDER)
        backup_path: Path to backup used
        preventive_backup_path: Path to preventive backup (if created)
        temp_folder: Path to temp folder (if created)
        error: Error message (if failed)
        duration_seconds: Duration of operation in seconds
    """
    success: bool
    mode: str = ""
    backup_path: str = ""
    preventive_backup_path: str = ""
    temp_folder: str = ""
    error: str = ""
    duration_seconds: float = 0.0


class DeveloperAgent:
    """
    Agent responsible for implementing and executing rollback.
    
    This agent:
    - Executes the complete rollback workflow
    - Manages SSH connections and remote operations
    - Coordinates between IIS and Backup managers
    - Handles errors and provides recovery options
    
    Attributes:
        agent: CrewAI Agent instance
        ssh: SSHExecutor instance
        iis: IISManager instance
        backup: BackupManager instance
    """
    
    def __init__(self):
        """Initialize the Developer Agent."""
        self.agent = Agent(
            role="IIS Rollback Developer",
            goal="Implement and execute reliable IIS rollback operations",
            backstory="""You are a senior DevOps engineer specializing in 
            Windows Server administration and IIS deployment. You have 
            extensive experience with PowerShell scripting, SSH automation, 
            and implementing robust rollback procedures. You always follow 
            best practices and never take shortcuts.""",
            verbose=True
        )
        
        self.ssh: Optional[SSHExecutor] = None
        self.iis: Optional[IISManager] = None
        self.backup: Optional[BackupManager] = None
        
        logger.info("DeveloperAgent initialized")
    
    def _connect_ssh(self, config: SSHConfig) -> bool:
        """
        Establish SSH connection to Windows Server.
        
        Args:
            config: SSH configuration
            
        Returns:
            bool: True if connection successful
        """
        logger.info(f"Connecting to {config.host}:{config.port}")
        
        try:
            self.ssh = SSHExecutor(config)
            self.ssh.connect()
            
            # Initialize IIS and Backup managers
            self.iis = IISManager(self.ssh)
            self.backup = BackupManager(self.ssh, self.iis)
            
            logger.info("SSH connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SSH server: {e}")
            return False
    
    def _disconnect_ssh(self) -> None:
        """Close SSH connection."""
        if self.ssh:
            self.ssh.disconnect()
            logger.info("SSH connection closed")
    
    def execute_rollback(self, config: RollbackConfig) -> RollbackResult:
        """
        Execute the complete rollback operation.
        
        This is the main method that orchestrates the entire rollback:
        1. Connect to server via SSH
        2. Detect backup type
        3. Create preventive backup
        4. Stop IIS site
        5. Delete site content
        6. Copy backup files
        7. Start IIS site
        8. Cleanup temp folder
        9. Return result
        
        Args:
            config: Rollback configuration
            
        Returns:
            RollbackResult with operation outcome
        """
        start_time = time.time()
        errors = []
        
        logger.info(f"Starting rollback for site: {config.site_name}")
        logger.info(f"Backup path: {config.backup_path}")
        
        try:
            # Step 1: Connect to SSH
            logger.info("Step 1: Connecting to SSH server...")
            if not self._connect_ssh(config.ssh_config):
                return RollbackResult(
                    success=False,
                    error="Failed to establish SSH connection"
                )
            
            # Step 2: Detect backup type
            logger.info("Step 2: Detecting backup type...")
            detection = self.backup.detect_backup_type(config.backup_path)
            
            if detection['type'] == RollbackMode.NONE:
                return RollbackResult(
                    success=False,
                    error=detection['message']
                )
            
            mode = detection['type'].value
            logger.info(f"Backup mode: {mode}")
            
            backup_source = config.backup_path
            temp_folder = ""
            
            # Step 3: Handle ZIP extraction if needed
            if detection['type'] == RollbackMode.ZIP:
                logger.info("Step 3: Extracting ZIP backup...")
                temp_folder = self.backup.create_temp_folder()
                zip_path = os.path.join(
                    config.backup_path,
                    detection['backup_info'].name
                )
                extract_result = self.backup.extract_zip(zip_path, temp_folder)
                
                if not extract_result['success']:
                    return RollbackResult(
                        success=False,
                        mode=mode,
                        error=f"Failed to extract ZIP: {extract_result.get('stderr', 'Unknown error')}",
                        temp_folder=temp_folder
                    )
                
                backup_source = temp_folder
                logger.info(f"ZIP extracted to: {temp_folder}")
            
            # Step 4: Create preventive backup
            logger.info("Step 4: Creating preventive backup...")
            backup_base = os.path.dirname(config.backup_path)
            preventive_result = self.backup.create_preventive_backup(
                config.site_path,
                backup_base,
                config.site_name
            )
            
            if not preventive_result['success']:
                logger.warning(
                    f"Preventive backup failed: {preventive_result['message']}"
                )
                # Continue anyway - not critical
            
            # Step 5: Stop IIS site
            logger.info("Step 5: Stopping IIS site...")
            stop_result = self.iis.stop_site(config.site_name)
            
            if not stop_result['success']:
                errors.append(f"Failed to stop site: {stop_result.get('stderr', 'Unknown')}")
                # Don't fail immediately - site might already be stopped
            
            # Step 6: Delete site content
            logger.info("Step 6: Deleting site content...")
            delete_result = self.iis.delete_site_content(config.site_path, keep_root=True)
            
            if not delete_result['success']:
                errors.append(f"Failed to delete content: {delete_result.get('stderr', 'Unknown')}")
            
            # Step 7: Copy backup files
            logger.info("Step 7: Copying backup files...")
            copy_result = self.iis.copy_files(backup_source, config.site_path)
            
            if not copy_result['success']:
                return RollbackResult(
                    success=False,
                    mode=mode,
                    error=f"Failed to copy files: {copy_result.get('stderr', 'Unknown')}",
                    backup_path=config.backup_path,
                    preventive_backup_path=preventive_result.get('backup_path', ''),
                    temp_folder=temp_folder
                )
            
            # Step 8: Start IIS site
            logger.info("Step 8: Starting IIS site...")
            start_result = self.iis.start_site(config.site_name)
            
            if not start_result['success']:
                errors.append(f"Failed to start site: {start_result.get('stderr', 'Unknown')}")
            
            # Step 9: Cleanup temp folder
            if temp_folder:
                logger.info("Step 9: Cleaning up temp folder...")
                cleanup_result = self.backup.cleanup_temp_folder()
                if not cleanup_result['success']:
                    logger.warning(f"Cleanup failed: {cleanup_result['message']}")
            
            duration = time.time() - start_time
            
            # Check final status
            if errors:
                logger.warning(f"Rollback completed with {len(errors)} error(s)")
                return RollbackResult(
                    success=True,  # Main operation succeeded
                    mode=mode,
                    backup_path=config.backup_path,
                    preventive_backup_path=preventive_result.get('backup_path', ''),
                    temp_folder=temp_folder,
                    error=f"Completed with errors: {'; '.join(errors)}",
                    duration_seconds=duration
                )
            
            logger.info(f"Rollback completed successfully in {duration:.2f}s")
            return RollbackResult(
                success=True,
                mode=mode,
                backup_path=config.backup_path,
                preventive_backup_path=preventive_result.get('backup_path', ''),
                temp_folder=temp_folder,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Rollback failed: {e}")
            return RollbackResult(
                success=False,
                error=str(e),
                duration_seconds=duration
            )
        
        finally:
            # Always disconnect SSH
            self._disconnect_ssh()
    
    def execute_rollback_simple(
        self,
        site_name: str,
        site_path: str,
        backup_path: str,
        ssh_host: str,
        ssh_username: str,
        ssh_password: str = None,
        ssh_key_path: str = None
    ) -> RollbackResult:
        """
        Simple rollback execution with inline configuration.
        
        This method provides a simpler interface for executing rollback
        without needing to create RollbackConfig manually.
        
        Args:
            site_name: Name of the IIS site
            site_path: Path to the IIS site root
            backup_path: Path to the backup directory
            ssh_host: SSH server hostname/IP
            ssh_username: SSH username
            ssh_password: SSH password (optional if key provided)
            ssh_key_path: Path to SSH private key (optional)
            
        Returns:
            RollbackResult with operation outcome
        """
        config = RollbackConfig(
            site_name=site_name,
            site_path=site_path,
            backup_path=backup_path,
            ssh_config=SSHConfig(
                host=ssh_host,
                username=ssh_username,
                password=ssh_password,
                key_path=ssh_key_path
            )
        )
        
        return self.execute_rollback(config)
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI Agent instance.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
    
    def __repr__(self) -> str:
        """String representation of DeveloperAgent."""
        connected = self.ssh.is_connected() if self.ssh else False
        return f"DeveloperAgent(connected={connected})"


def create_developer_agent() -> Agent:
    """
    Factory function to create Developer Agent.
    
    Returns:
        CrewAI Agent configured for development
    """
    agent = DeveloperAgent()
    return agent.get_agent()