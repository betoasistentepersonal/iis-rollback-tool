"""
Requirements Tasks - Task Definitions for Requirements Agent
============================================================

This module contains task definitions for the Requirements Agent.

Author: CrewAI Team
Version: 1.0.0
"""

from crewai import Task
from typing import Dict, Any, Optional


def validate_requirements_task(
    agent,
    site_name: str,
    site_path: str,
    backup_path: str,
    expected_output: str = "requirements_report"
) -> Task:
    """
    Create a task to validate requirements for rollback operation.
    
    This task checks that all prerequisites are met before
    proceeding with the rollback operation.
    
    Args:
        agent: Requirements agent instance
        site_name: Name of the IIS site
        site_path: Path to the IIS site root
        backup_path: Path to the backup directory
        expected_output: Expected output description
        
    Returns:
        CrewAI Task for requirements validation
    """
    return Task(
        description=f"""
        Validate all requirements for IIS rollback operation.
        
        Site Name: {site_name}
        Site Path: {site_path}
        Backup Path: {backup_path}
        
        Please perform the following checks:
        1. Verify SSH configuration is complete (host, username, auth)
        2. Verify site path exists on remote server
        3. Verify backup path exists on remote server
        4. Check available disk space
        5. Verify IIS site exists
        6. Ensure all prerequisites are met
        
        Return a detailed report of:
        - Which requirements are met
        - Which requirements are missing
        - Recommendations for fixing any issues
        - Go/No-Go decision for proceeding with rollback
        """,
        expected_output=expected_output,
        agent=agent
    )


def create_requirements_report_task(
    agent,
    context: Dict[str, Any] = None
) -> Task:
    """
    Create a task to generate a requirements report.
    
    Args:
        agent: Requirements agent instance
        context: Context from previous tasks
        
    Returns:
        CrewAI Task for generating requirements report
    """
    return Task(
        description="""
        Generate a comprehensive requirements report documenting:
        
        1. System Requirements
           - Minimum Windows Server version
           - Required Windows features (IIS, OpenSSH)
           - Network requirements
           - Disk space requirements
        
        2. Configuration Requirements
           - Environment variables needed
           - SSH configuration
           - IIS site configuration
           - Backup directory structure
        
        3. Operational Requirements
           - User permissions needed
           - Pre-rollback checklist
           - Post-rollback verification steps
        
        Format the report as markdown documentation.
        """,
        expected_output="Markdown requirements report",
        agent=agent
    )