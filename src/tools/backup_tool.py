"""
Backup Tool - Backup and Rollback Management
============================================

This module provides functionality for managing IIS backups and executing
rollback operations, including ZIP extraction, preventive backups, and
temporary folder management.

Author: CrewAI Team
Version: 1.0.0
"""

import os
import time
import shutil
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from .ssh_tool import SSHExecutor
from .iis_tool import IISManager

# Configure module logger
logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Enum for backup types."""
    ZIP = "zip"
    FOLDER = "folder"
    UNKNOWN = "unknown"


class RollbackMode(Enum):
    """Enum for rollback modes."""
    ZIP = "zip"
    FOLDER = "folder"
    NONE = "none"


@dataclass
class BackupInfo:
    """
    Information about a backup.
    
    Attributes:
        path: Full path to backup
        type: BackupType (ZIP or FOLDER)
        name: Backup name/identifier
        timestamp: Creation timestamp
    """
    path: str
    type: BackupType
    name: str
    timestamp: datetime


class BackupManager:
    """
    Manages IIS backups and rollback operations.
    
    This class provides methods for:
    - Detecting backup types
    - Creating preventive backups
    - Extracting ZIP archives
    - Managing temporary folders
    - Logging rollback results
    
    Attributes:
        ssh: SSHExecutor instance for remote command execution
        iis: IISManager instance for IIS operations
        
    Example:
        >>> ssh = SSHExecutor(config)
        >>> ssh.connect()
        >>> iis = IISManager(ssh)
        >>> backup = BackupManager(ssh, iis)
        >>> backup.detect_backup_type("E:\\Backups\\MyWebsite\\Backup20240101")
    """
    
    def __init__(self, ssh: SSHExecutor, iis: IISManager):
        """
        Initialize Backup Manager with SSH executor and IIS manager.
        
        Args:
            ssh: SSHExecutor instance for remote command execution
            iis: IISManager instance for IIS operations
        """
        self.ssh = ssh
        self.iis = iis
        self.temp_folder: Optional[str] = None
        logger.info("BackupManager initialized")
    
    def detect_backup_type(self, backup_path: str) -> Dict[str, Any]:
        """
        Detect the type of backup at the given path.
        
        Checks for ZIP files and determines if backup is:
        - ZIP mode: exactly 1 ZIP file found
        - Folder mode: no ZIP files, treat as folder
        - Abort: more than 1 ZIP file (ambiguous)
        
        Args:
            backup_path: Path to the backup directory or ZIP file
            
        Returns:
            Dict containing:
                - type: RollbackMode (ZIP, FOLDER, or NONE)
                - zip_count: Number of ZIP files found
                - backup_info: BackupInfo if valid backup found
                - message: Human-readable status message
                
        Example:
            >>> result = backup.detect_backup_type("E:\\Backups\\MyWebsite")
            >>> if result['type'] == RollbackMode.ZIP:
            ...     print("ZIP mode detected")
        """
        logger.info(f"Detecting backup type at: {backup_path}")
        
        # Count ZIP files in the backup path
        command = (
            f'powershell -Command "'
            f'$zipCount = (Get-ChildItem -Path \\"{backup_path}\\" -Filter *.zip -ErrorAction SilentlyContinue).Count; '
            f'Write-Host $zipCount"'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if not result['success']:
            logger.error(f"Failed to detect backup type: {result['stderr']}")
            return {
                'type': RollbackMode.NONE,
                'zip_count': -1,
                'backup_info': None,
                'message': f"Failed to check backup: {result['stderr']}"
            }
        
        try:
            zip_count = int(result['stdout'].strip())
        except ValueError:
            zip_count = 0
        
        logger.info(f"Found {zip_count} ZIP file(s) in backup path")
        
        # Determine backup mode based on ZIP count
        if zip_count == 1:
            # ZIP mode - exactly one ZIP file found
            zip_info = self._get_zip_info(backup_path)
            
            return {
                'type': RollbackMode.ZIP,
                'zip_count': 1,
                'backup_info': zip_info,
                'message': "ZIP mode detected (1 ZIP file found)"
            }
        
        elif zip_count > 1:
            # Abort - multiple ZIP files found (ambiguous)
            logger.error(
                f"Multiple ZIP files ({zip_count}) found - rollback aborted"
            )
            return {
                'type': RollbackMode.NONE,
                'zip_count': zip_count,
                'backup_info': None,
                'message': f"Abort: {zip_count} ZIP files found (expected 1)"
            }
        
        else:
            # Folder mode - no ZIP files, treat as folder
            folder_info = self._get_folder_info(backup_path)
            
            return {
                'type': RollbackMode.FOLDER,
                'zip_count': 0,
                'backup_info': folder_info,
                'message': "Folder mode detected (no ZIP files)"
            }
    
    def _get_zip_info(self, backup_path: str) -> BackupInfo:
        """
        Get information about a ZIP backup.
        
        Args:
            backup_path: Path to the backup directory
            
        Returns:
            BackupInfo object with ZIP backup details
        """
        command = (
            f'powershell -Command "'
            f'$zipFile = Get-ChildItem -Path \\"{backup_path}\\" -Filter *.zip | Select-Object -First 1; '
            f'Write-Host \\"$($zipFile.Name)|$($zipFile.LastWriteTimeUtc.ToString(\'yyyy-MM-dd HH:mm:ss\\'))\\""'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success'] and result['stdout']:
            parts = result['stdout'].split('|')
            if len(parts) >= 2:
                try:
                    timestamp = datetime.strptime(
                        parts[1].strip(),
                        '%Y-%m-%d %H:%M:%S'
                    )
                    return BackupInfo(
                        path=backup_path,
                        type=BackupType.ZIP,
                        name=parts[0].strip(),
                        timestamp=timestamp
                    )
                except ValueError:
                    pass
        
        # Fallback
        return BackupInfo(
            path=backup_path,
            type=BackupType.ZIP,
            name="backup.zip",
            timestamp=datetime.now()
        )
    
    def _get_folder_info(self, backup_path: str) -> BackupInfo:
        """
        Get information about a folder backup.
        
        Args:
            backup_path: Path to the backup directory
            
        Returns:
            BackupInfo object with folder backup details
        """
        folder_name = os.path.basename(backup_path.rstrip('\\'))
        
        command = (
            f'powershell -Command "'
            f'$folder = Get-Item -Path \\"{backup_path}\\" -ErrorAction SilentlyContinue; '
            f'if ($folder) {{ Write-Host $folder.LastWriteTimeUtc.ToString(\'yyyy-MM-dd HH:mm:ss\') }}"'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        timestamp = datetime.now()
        
        if result['success'] and result['stdout']:
            try:
                timestamp = datetime.strptime(
                    result['stdout'].strip(),
                    '%Y-%m-%d %H:%M:%S'
                )
            except ValueError:
                pass
        
        return BackupInfo(
            path=backup_path,
            type=BackupType.FOLDER,
            name=folder_name,
            timestamp=timestamp
        )
    
    def create_temp_folder(self, base_path: str = "E:\\Temp") -> str:
        """
        Create a temporary folder for rollback operations.
        
        Args:
            base_path: Base directory for temp folder creation
            
        Returns:
            Path to the created temp folder
            
        Example:
            >>> temp_folder = backup.create_temp_folder()
            >>> print(f"Created: {temp_folder}")
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_folder = os.path.join(base_path, f"Rollback_{timestamp}")
        
        logger.info(f"Creating temp folder: {temp_folder}")
        
        # Create parent Temp folder if it doesn't exist
        command = (
            f'powershell -Command "'
            f'if (!(Test-Path \\"{base_path}\\")) {{ New-Item -Path \\"{basePath}\\" -ItemType Directory -Force }}; '
            f'New-Item -Path \\"{temp_folder}\\" -ItemType Directory -Force | Out-Null; '
            f'Write-Host \\"Created\\""'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success']:
            self.temp_folder = temp_folder
            logger.info(f"Temp folder created: {temp_folder}")
            return temp_folder
        else:
            logger.error(f"Failed to create temp folder: {result['stderr']}")
            raise RuntimeError(f"Failed to create temp folder: {result['stderr']}")
    
    def extract_zip(self, zip_path: str, destination: str) -> Dict[str, Any]:
        """
        Extract a ZIP archive using PowerShell Expand-Archive.
        
        Args:
            zip_path: Path to the ZIP file
            destination: Destination folder for extraction
            
        Returns:
            Dict with command execution results
            
        Example:
            >>> result = backup.extract_zip("E:\\Backups\\backup.zip", "E:\\Temp\\Rollback")
            >>> if result['success']:
            ...     print("ZIP extracted successfully")
        """
        logger.info(f"Extracting ZIP: {zip_path} -> {destination}")
        
        command = (
            f'powershell -Command "'
            f'Expand-Archive -Path \\"{zip_path}\\" -DestinationPath \\"{destination}\\" -Force; '
            f'Write-Host \\"Extraction complete\\""'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success']:
            logger.info(f"Successfully extracted ZIP to: {destination}")
        else:
            logger.error(f"Failed to extract ZIP: {result['stderr']}")
        
        return result
    
    def create_preventive_backup(
        self,
        site_path: str,
        backup_base_path: str,
        site_name: str
    ) -> Dict[str, Any]:
        """
        Create a preventive backup before rollback.
        
        Args:
            site_path: Path to the IIS website root
            backup_base_path: Base path for backup storage
            site_name: Name of the IIS site
            
        Returns:
            Dict with command execution results
            
        Example:
            >>> result = backup.create_preventive_backup(
            ...     "E:\\Web Sites\\MyWebsite",
            ...     "E:\\Web Sites Backups\\MyWebsite",
            ...     "MyWebsite"
            ... )
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_base_path, f"PreRollback_{timestamp}")
        
        logger.info(f"Creating preventive backup: {backup_path}")
        
        # Use robocopy to create backup
        command = (
            f'powershell -Command "'
            f'New-Item -Path \\"{backup_path}\\" -ItemType Directory -Force | Out-Null; '
            f'robocopy \\"{site_path}\\" \\"{backup_path}\\" /E /Z /R:3 /W:5 | Out-Null; '
            f'Write-Host \\"Backup created at {backup_path}\\""'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success']:
            logger.info(f"Preventive backup created: {backup_path}")
            return {
                'success': True,
                'backup_path': backup_path,
                'message': f"Preventive backup created: {backup_path}"
            }
        else:
            logger.error(
                f"Failed to create preventive backup: {result['stderr']}"
            )
            return {
                'success': False,
                'backup_path': None,
                'message': f"Failed to create backup: {result['stderr']}"
            }
    
    def cleanup_temp_folder(self) -> Dict[str, Any]:
        """
        Clean up temporary rollback folder.
        
        Returns:
            Dict with command execution results
        """
        if not self.temp_folder:
            logger.warning("No temp folder to clean up")
            return {
                'success': True,
                'message': "No temp folder to clean up"
            }
        
        logger.info(f"Cleaning up temp folder: {self.temp_folder}")
        
        command = (
            f'powershell -Command "'
            f'Remove-Item -Path \\"{self.temp_folder}\\" -Recurse -Force -ErrorAction SilentlyContinue; '
            f'Write-Host \\"Cleanup complete\\""'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success']:
            logger.info(f"Successfully cleaned up temp folder: {self.temp_folder}")
            self.temp_folder = None
            return {
                'success': True,
                'message': f"Cleaned up temp folder: {self.temp_folder}"
            }
        else:
            logger.warning(
                f"Failed to clean up temp folder: {result['stderr']}"
            )
            return {
                'success': False,
                'message': f"Failed to clean up: {result['stderr']}"
            }
    
    def get_rollback_result(
        self,
        site_name: str,
        success: bool,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate and log rollback result.
        
        Args:
            site_name: Name of the IIS site
            success: Whether rollback was successful
            details: Additional details about the operation
            
        Returns:
            Dict containing complete rollback result
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = {
            'timestamp': timestamp,
            'site_name': site_name,
            'success': success,
            'details': details,
            'message': ''
        }
        
        if success:
            result['message'] = (
                f"IIS rollback completed successfully for site '{site_name}' "
                f"at {timestamp}"
            )
            logger.info(result['message'])
        else:
            result['message'] = (
                f"IIS rollback failed for site '{site_name}' "
                f"at {timestamp}. Details: {details.get('error', 'Unknown error')}"
            )
            logger.error(result['message'])
        
        return result
    
    def __repr__(self) -> str:
        """String representation of BackupManager instance."""
        return (
            f"BackupManager(temp_folder={self.temp_folder})"
        )