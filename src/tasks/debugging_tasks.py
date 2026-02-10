"""
Debugging Tasks - Task Definitions for Debugger Agent
======================================================

This module contains task definitions for the Debugger Agent.

Author: CrewAI Team
Version: 1.0.0
"""

from crewai import Task
from typing import Dict, Any, Optional


def diagnose_error_task(
    agent,
    error_message: str,
    context: Dict[str, Any] = None
) -> Task:
    """
    Create a task to diagnose an error.
    
    Args:
        agent: Debugger agent instance
        error_message: Error message to diagnose
        context: Additional context about the error
        
    Returns:
        CrewAI Task for error diagnosis
    """
    context_str = ""
    if context:
        context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])
    
    return Task(
        description=f"""
        Diagnose the following error:
        
        Error Message: {error_message}
        
        Context:
        {context_str}
        
        Please provide:
        1. Root cause analysis
        2. Possible causes of this error
        3. Suggested fixes or workarounds
        4. Diagnostic commands to run
        5. Prevention recommendations
        
        Be thorough and consider all possible scenarios.
        """,
        expected_output="Error diagnosis and recommendations",
        agent=agent
    )


def run_diagnostics_task(
    agent,
    diagnostics_type: str = "ssh",
    target: str = None
) -> Task:
    """
    Create a task to run diagnostics on the system.
    
    Args:
        agent: Debugger agent instance
        diagnostics_type: Type of diagnostics (ssh, iis, file, all)
        target: Target for diagnostics (e.g., site name, path)
        
    Returns:
        CrewAI Task for running diagnostics
    """
    if diagnostics_type == "ssh":
        description = """
        Run SSH diagnostics on the Windows Server:
        
        1. Test network connectivity to SSH port
        2. Check if SSH service is running
        3. Verify SSH configuration
        4. Check user authentication
        5. Review SSH logs
        
        Return diagnostic results and any issues found.
        """
    elif diagnostics_type == "iis":
        description = f"""
        Run IIS diagnostics for site: {target or 'all sites'}
        
        1. List all IIS sites and their status
        2. Check target site configuration
        3. Verify site bindings
        4. Check application pool status
        5. Review IIS logs
        
        Return diagnostic results and any issues found.
        """
    elif diagnostics_type == "file":
        description = f"""
        Run file system diagnostics for: {target}
        
        1. Check if path exists
        2. List directory contents
        3. Check file/folder permissions
        4. Verify disk space
        5. Check for locked files
        
        Return diagnostic results and any issues found.
        """
    else:
        description = """
        Run comprehensive system diagnostics:
        
        1. SSH connectivity and authentication
        2. IIS site configuration and status
        3. File system paths and permissions
        4. Disk space availability
        5. Windows service status
        
        Return complete diagnostic report.
        """
    
    return Task(
        description=description,
        expected_output="Diagnostic report with findings and recommendations",
        agent=agent
    )