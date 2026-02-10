"""
Development Tasks - Task Definitions for Developer Agent
=========================================================

This module contains task definitions for the Developer Agent.

Author: CrewAI Team
Version: 1.0.0
"""

from crewai import Task
from typing import Dict, Any, Optional


def execute_rollback_task(
    agent,
    site_name: str,
    site_path: str,
    backup_path: str,
    ssh_host: str,
    ssh_username: str,
    ssh_password: str = None,
    ssh_key_path: str = None
) -> Task:
    """
    Create a task to execute the complete rollback operation.
    
    This is the main task that orchestrates the entire rollback workflow:
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
        agent: Developer agent instance
        site_name: Name of the IIS site
        site_path: Path to the IIS site root
        backup_path: Path to the backup directory
        ssh_host: SSH server hostname/IP
        ssh_username: SSH username
        ssh_password: SSH password (optional)
        ssh_key_path: Path to SSH private key (optional)
        
    Returns:
        CrewAI Task for executing rollback
    """
    return Task(
        description=f"""
        Execute the complete IIS rollback operation for site: {site_name}
        
        Configuration:
        - Site Path: {site_path}
        - Backup Path: {backup_path}
        - SSH Host: {ssh_host}
        - SSH Username: {ssh_username}
        
        Please perform the following steps:
        
        1. SSH Connect
           - Establish SSH connection to {ssh_host}
           - Verify connection is successful
        
        2. Detect Backup Type
           - Check for ZIP files in {backup_path}
           - If 1 ZIP: use ZIP mode
           - If 0 ZIP: use folder mode
           - If >1 ZIP: abort with error
        
        3. ZIP Mode (if applicable)
           - Create temp folder: E:\\Temp\\Rollback_[timestamp]
           - Extract ZIP to temp folder using Expand-Archive
        
        4. Create Preventive Backup
           - Create: E:\\Web Sites Backups\\[Sitio]\\PreRollback_[timestamp]
           - Use robocopy to copy current site content
        
        5. Stop IIS Site
           - Execute: appcmd stop site "{site_name}"
           - Verify site is stopped
        
        6. Delete Site Content
           - Remove all content from {site_path}
           - Keep the root folder
        
        7. Copy Backup Files
           - Use robocopy to copy from backup to site path
           - Include all subdirectories and files
        
        8. Start IIS Site
           - Execute: appcmd start site "{site_name}"
           - Verify site is started
        
        9. Cleanup Temp Folder
           - Remove temp folder if created
           - Report cleanup status
        
        10. Log Result
            - Record all operations
            - Note any errors
            - Return final status
        
        Return a detailed result including:
        - Success/failure status
        - Backup mode used
        - Duration
        - Any errors encountered
        """,
        expected_output="Rollback operation result",
        agent=agent
    )


def create_backup_task(
    agent,
    site_path: str,
    backup_path: str
) -> Task:
    """
    Create a task to create a backup of the site.
    
    Args:
        agent: Developer agent instance
        site_path: Path to the IIS site root
        backup_path: Path for the backup
        
    Returns:
        CrewAI Task for creating backup
    """
    return Task(
        description=f"""
        Create a backup of the IIS site before rollback.
        
        Source: {site_path}
        Destination: {backup_path}
        
        Steps:
        1. Create destination folder if it doesn't exist
        2. Use robocopy to copy all files and folders
        3. Preserve file attributes and timestamps
        4. Verify backup was created successfully
        
        Use robocopy with appropriate flags:
        - /E (copy subdirectories)
        - /Z (restartable mode)
        - /R:3 (retry 3 times on failure)
        - /W:5 (wait 5 seconds between retries)
        """,
        expected_output="Backup created successfully",
        agent=agent
    )


def restore_site_task(
    agent,
    site_path: str,
    backup_source: str,
    mode: str = "folder"
) -> Task:
    """
    Create a task to restore site from backup.
    
    Args:
        agent: Developer agent instance
        site_path: Path to the IIS site root
        backup_source: Path to the backup source
        mode: Restore mode (folder or zip)
        
    Returns:
        CrewAI Task for restoring site
    """
    return Task(
        description=f"""
        Restore the IIS site from backup.
        
        Site Path: {site_path}
        Backup Source: {backup_source}
        Mode: {mode}
        
        Steps:
        1. Stop the IIS site if running
        2. Delete current site content (keep root folder)
        3. Copy backup files to site path
        4. Start the IIS site
        5. Verify site is running correctly
        
        Use robocopy for reliable file copying.
        Report any errors encountered during restoration.
        """,
        expected_output="Site restored successfully",
        agent=agent
    )