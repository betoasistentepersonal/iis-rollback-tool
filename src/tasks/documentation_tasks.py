"""
Documentation Tasks - Task Definitions for Documentation Agent
==============================================================

This module contains task definitions for the Documentation Agent.

Author: CrewAI Team
Version: 1.0.0
"""

from crewai import Task
from typing import Dict, Any, Optional


def document_process_task(
    agent,
    site_name: str,
    site_path: str,
    backup_path: str
) -> Task:
    """
    Create a task to document the rollback process.
    
    Args:
        agent: Documentation agent instance
        site_name: Name of the IIS site
        site_path: Path to the IIS site root
        backup_path: Path to the backup directory
        
    Returns:
        CrewAI Task for documenting the process
    """
    return Task(
        description=f"""
        Document the complete IIS rollback process for:
        
        Site Name: {site_name}
        Site Path: {site_path}
        Backup Path: {backup_path}
        
        Include:
        1. Process overview and workflow
        2. Step-by-step procedure
        3. Expected outcomes at each step
        4. Error handling procedures
        5. Verification steps
        6. Rollback timeline and duration
        
        Send a progress update email to stakeholders.
        """,
        expected_output="Documented process and email sent",
        agent=agent
    )


def send_progress_update_task(
    agent,
    site_name: str,
    step: str,
    progress: int,
    total_steps: int,
    details: Dict[str, Any] = None
) -> Task:
    """
    Create a task to send a progress update.
    
    Args:
        agent: Documentation agent instance
        site_name: Name of the IIS site
        step: Current step description
        progress: Current step number
        total_steps: Total number of steps
        details: Additional details to include
        
    Returns:
        CrewAI Task for sending progress update
    """
    details_str = ""
    if details:
        details_str = "\n".join([f"- {k}: {v}" for k, v in details.items()])
    
    return Task(
        description=f"""
        Send a progress update for IIS rollback operation:
        
        Site: {site_name}
        Current Step: {step}
        Progress: {progress}/{total_steps} steps completed
        
        Additional Details:
        {details_str}
        
        Please send this update via email to all stakeholders.
        """,
        expected_output="Progress email sent",
        agent=agent
    )


def generate_report_task(
    agent,
    site_name: str,
    backup_type: str,
    success: bool,
    errors: list = None,
    duration: float = 0.0
) -> Task:
    """
    Create a task to generate a rollback report.
    
    Args:
        agent: Documentation agent instance
        site_name: Name of the IIS site
        backup_type: Type of backup used (ZIP or folder)
        success: Whether operation succeeded
        errors: List of errors encountered
        duration: Duration of operation in seconds
        
    Returns:
        CrewAI Task for generating report
    """
    errors_str = ""
    if errors:
        errors_str = "\n".join([f"- {e}" for e in errors])
    else:
        errors_str = "No errors encountered"
    
    return Task(
        description=f"""
        Generate a comprehensive rollback report for:
        
        Site: {site_name}
        Backup Type: {backup_type}
        Success: {success}
        Duration: {duration:.2f} seconds
        
        Errors:
        {errors_str}
        
        The report should include:
        1. Executive summary
        2. Timeline of operations
        3. Detailed step results
        4. Error analysis (if any)
        5. Recommendations
        6. Post-rollback verification status
        
        Save the report as a JSON file and notify stakeholders.
        """,
        expected_output="Report generated and saved",
        agent=agent
    )