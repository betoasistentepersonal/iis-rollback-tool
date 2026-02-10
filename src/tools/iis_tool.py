"""
IIS Tool - Internet Information Services Management
===================================================

This module provides functionality for managing IIS websites on Windows Server,
including site operations (start/stop) and content management.

Author: CrewAI Team
Version: 1.0.0
"""

import logging
import re
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .ssh_tool import SSHExecutor

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class IISSite:
    """
    Represents an IIS website.
    
    Attributes:
        name: Site name
        id: Site ID
        bindings: List of binding strings
        state: Site state (Started/Stopped)
        physical_path: Root physical path
    """
    name: str
    id: str
    bindings: List[str]
    state: str
    physical_path: str


class IISManager:
    """
    Manages IIS websites on Windows Server.
    
    This class provides methods for:
    - Listing IIS sites
    - Starting/stopping sites
    - Getting site information
    - Managing site content
    
    Attributes:
        ssh: SSHExecutor instance for remote command execution
        
    Example:
        >>> ssh = SSHExecutor(config)
        >>> ssh.connect()
        >>> iis = IISManager(ssh)
        >>> iis.stop_site("MyWebsite")
        >>> iis.start_site("MyWebsite")
    """
    
    def __init__(self, ssh: SSHExecutor):
        """
        Initialize IIS Manager with SSH executor.
        
        Args:
            ssh: SSHExecutor instance for remote command execution
        """
        self.ssh = ssh
        logger.info("IISManager initialized")
    
    def list_sites(self) -> List[IISSite]:
        """
        List all IIS websites on the server.
        
        Returns:
            List of IISSite objects representing all sites
            
        Example:
            >>> sites = iis.list_sites()
            >>> for site in sites:
            ...     print(f"{site.name}: {site.state}")
        """
        command = (
            "appcmd list site /xml /config:* | "
            "powershell -Command \""
            "$input | "
            "Select-Xml -XPath '//site' | "
            "%{ "
            "$node = $_.Node; "
            "$bindings = $node.bindings.binding | "
            "Select-Object @{Name='name'; Expression={$node.name}}, "
            "@{Name='id'; Expression={$node.id}}, "
            "@{Name='bindings'; Expression={$bindings}}, "
            "@{Name='state'; Expression={$node.state}}, "
            "@{Name='physical_path'; Expression={$node.application.virtualDirectory.path}}"
            "}\" "
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if not result['success']:
            logger.error(f"Failed to list IIS sites: {result['stderr']}")
            return []
        
        sites = self._parse_sites(result['stdout'])
        logger.info(f"Found {len(sites)} IIS sites")
        return sites
    
    def _parse_sites(self, output: str) -> List[IISSite]:
        """
        Parse the output of appcmd list sites command.
        
        Args:
            output: Raw output from appcmd command
            
        Returns:
            List of parsed IISSite objects
        """
        sites = []
        
        # Parse each site from the output
        # Output format: name|id|state|physical_path|binding1,binding2,...
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = line.split('|')
                if len(parts) >= 5:
                    site = IISSite(
                        name=parts[0].strip(),
                        id=parts[1].strip(),
                        state=parts[2].strip(),
                        physical_path=parts[3].strip(),
                        bindings=parts[4].split(',') if len(parts) > 4 else []
                    )
                    sites.append(site)
            except Exception as e:
                logger.warning(f"Failed to parse site line: {line}, error: {e}")
        
        return sites
    
    def get_site(self, site_name: str) -> Optional[IISSite]:
        """
        Get information about a specific IIS site.
        
        Args:
            site_name: Name of the site to retrieve
            
        Returns:
            IISSite object if found, None otherwise
        """
        sites = self.list_sites()
        
        for site in sites:
            if site.name.lower() == site_name.lower():
                return site
        
        logger.warning(f"Site '{site_name}' not found")
        return None
    
    def stop_site(self, site_name: str) -> Dict[str, Any]:
        """
        Stop an IIS website.
        
        Args:
            site_name: Name of the site to stop
            
        Returns:
            Dict with command execution results
            
        Example:
            >>> result = iis.stop_site("MyWebsite")
            >>> if result['success']:
            ...     print("Site stopped successfully")
        """
        logger.info(f"Stopping IIS site: {site_name}")
        
        # Use appcmd to stop the site
        command = f'appcmd stop site "{site_name}"'
        
        result = self.ssh.execute_command(command, powershell=False)
        
        if result['success']:
            logger.info(f"Successfully stopped site: {site_name}")
        else:
            logger.error(
                f"Failed to stop site '{site_name}': {result['stderr']}"
            )
        
        return result
    
    def start_site(self, site_name: str) -> Dict[str, Any]:
        """
        Start an IIS website.
        
        Args:
            site_name: Name of the site to start
            
        Returns:
            Dict with command execution results
            
        Example:
            >>> result = iis.start_site("MyWebsite")
            >>> if result['success']:
            ...     print("Site started successfully")
        """
        logger.info(f"Starting IIS site: {site_name}")
        
        # Use appcmd to start the site
        command = f'appcmd start site "{site_name}"'
        
        result = self.ssh.execute_command(command, powershell=False)
        
        if result['success']:
            logger.info(f"Successfully started site: {site_name}")
        else:
            logger.error(
                f"Failed to start site '{site_name}': {result['stderr']}"
            )
        
        return result
    
    def restart_site(self, site_name: str) -> Dict[str, Any]:
        """
        Restart an IIS website (stop then start).
        
        Args:
            site_name: Name of the site to restart
            
        Returns:
            Dict with command execution results
        """
        logger.info(f"Restarting IIS site: {site_name}")
        
        # Stop the site
        stop_result = self.stop_site(site_name)
        
        if not stop_result['success']:
            return {
                'success': False,
                'message': f"Failed to stop site: {stop_result['stderr']}"
            }
        
        # Small delay to ensure clean restart
        time.sleep(2)
        
        # Start the site
        start_result = self.start_site(site_name)
        
        if start_result['success']:
            return {
                'success': True,
                'message': f"Successfully restarted site: {site_name}"
            }
        else:
            return {
                'success': False,
                'message': f"Failed to start site: {start_result['stderr']}"
            }
    
    def get_site_state(self, site_name: str) -> Optional[str]:
        """
        Get the current state of an IIS site.
        
        Args:
            site_name: Name of the site
            
        Returns:
            State string ('Started', 'Stopped') or None if not found
        """
        command = (
            f'powershell -Command "'
            f'$site = Get-Website -Name \\"{site_name}\\"; '
            f'if ($site) {{ $site.State }} else {{ \\"NotFound\\" }}"'
        )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success']:
            return result['stdout'].strip()
        
        return None
    
    def delete_site_content(
        self,
        site_path: str,
        keep_root: bool = True
    ) -> Dict[str, Any]:
        """
        Delete website content files.
        
        Args:
            site_path: Path to the website root directory
            keep_root: If True, keeps the root folder itself
            
        Returns:
            Dict with command execution results
            
        Example:
            >>> result = iis.delete_site_content("E:\\Web Sites\\MyWebsite")
            >>> if result['success']:
            ...     print("Content deleted")
        """
        logger.info(
            f"Deleting site content from: {site_path} "
            f"(keep_root={keep_root})"
        )
        
        if keep_root:
            # Delete all contents of the folder but keep the folder
            command = (
                f'powershell -Command "'
                f'Remove-Item -Path \\"{site_path}\\*\\" -Recurse -Force -ErrorAction SilentlyContinue; '
                f'$files = Get-ChildItem -Path \\"{site_path}\\" -File -Recurse; '
                f'$files | ForEach-Object {{ Remove-Item -Path $_.FullName -Force }}; '
                f'Write-Host \\"Content deletion complete\\""'
            )
        else:
            # Delete entire folder including root
            command = (
                f'powershell -Command "'
                f'Remove-Item -Path \\"{site_path}\\" -Recurse -Force; '
                f'Write-Host \\"Folder deletion complete\\""'
            )
        
        result = self.ssh.execute_command(command, powershell=True)
        
        if result['success']:
            logger.info(f"Successfully deleted content from: {site_path}")
        else:
            logger.error(
                f"Failed to delete content from '{site_path}': {result['stderr']}"
            )
        
        return result
    
    def copy_files(
        self,
        source_path: str,
        destination_path: str
    ) -> Dict[str, Any]:
        """
        Copy files using robocopy for reliable file operations.
        
        Args:
            source_path: Source directory path
            destination_path: Destination directory path
            
        Returns:
            Dict with command execution results
        """
        logger.info(f"Copying files from {source_path} to {destination_path}")
        
        # Use robocopy for reliable file copying
        command = (
            f'robocopy "{source_path}" "{destination_path}" /E /Z /B /MT:16 /R:3 /W:5'
        )
        
        result = self.ssh.execute_command(command, powershell=False)
        
        # Robocopy returns specific exit codes:
        # 0 = no files copied
        # 1 = files copied successfully
        # 2 = extra files/directories detected
        # >=8 = error
        
        if result['return_code'] in [0, 1, 2]:
            logger.info(
                f"Successfully copied files from {source_path} to {destination_path}"
            )
            return {
                'success': True,
                'message': f"Files copied (robocopy exit code: {result['return_code']})",
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'return_code': result['return_code']
            }
        else:
            logger.error(
                f"Failed to copy files: {result['stderr']}"
            )
            return {
                'success': False,
                'message': f"Copy failed: {result['stderr']}",
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'return_code': result['return_code']
            }
    
    def __repr__(self) -> str:
        """String representation of IISManager instance."""
        return f"IISManager(ssh_connected={self.ssh.is_connected()})"