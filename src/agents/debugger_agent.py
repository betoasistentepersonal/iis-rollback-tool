"""
Debugger Agent - Troubleshooting and Error Analysis
====================================================

This agent is responsible for:
- Analyzing errors and failures
- Providing diagnostic information
- Suggesting solutions and fixes
- Troubleshooting SSH and IIS issues

Author: CrewAI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from crewai import Agent

from ..tools.ssh_tool import SSHExecutor

# Configure module logger
logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur."""
    SSH_CONNECTION = "ssh_connection"
    AUTHENTICATION = "authentication"
    IIS_OPERATION = "iis_operation"
    FILE_OPERATION = "file_operation"
    BACKUP_DETECTION = "backup_detection"
    EMAIL = "email"
    UNKNOWN = "unknown"


@dataclass
class ErrorAnalysis:
    """
    Analysis of a single error.
    
    Attributes:
        category: Error category
        message: Error message
        possible_causes: List of possible causes
        suggested_fixes: List of suggested fixes
        severity: Error severity (low, medium, high, critical)
        diagnostic_command: Command to run for diagnostics
    """
    category: ErrorCategory
    message: str
    possible_causes: List[str] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    severity: str = "medium"
    diagnostic_command: Optional[str] = None


@dataclass
class DiagnosticReport:
    """
    Complete diagnostic report.
    
    Attributes:
        errors: List of analyzed errors
        overall_health: Overall system health status
        recommendations: List of recommendations
        requires_attention: Whether immediate attention is needed
    """
    errors: List[ErrorAnalysis]
    overall_health: str
    recommendations: List[str]
    requires_attention: bool


class DebuggerAgent:
    """
    Agent responsible for debugging and troubleshooting.
    
    This agent:
    - Analyzes error messages and log entries
    - Identifies root causes of failures
    - Provides diagnostic commands
    - Suggests remediation steps
    
    Attributes:
        agent: CrewAI Agent instance
    """
    
    def __init__(self):
        """Initialize the Debugger Agent."""
        self.agent = Agent(
            role="System Debugger",
            goal="Diagnose issues and provide solutions for IIS rollback operations",
            backstory="""You are a senior systems administrator and 
            troubleshooting expert. You have deep knowledge of Windows Server, 
            IIS, PowerShell, and SSH. Your specialty is quickly identifying 
            the root cause of problems and providing clear, actionable 
            solutions. You are calm under pressure and methodical in your 
            approach.""",
            verbose=True
        )
        
        # Error patterns and their solutions
        self.error_patterns = {
            'connection_refused': {
                'category': ErrorCategory.SSH_CONNECTION,
                'causes': [
                    "SSH service not running on Windows Server",
                    "Firewall blocking SSH port (22)",
                    "Wrong IP address or hostname",
                    "Network connectivity issues"
                ],
                'fixes': [
                    "Ensure OpenSSH service is installed and running: Get-Service sshd",
                    "Configure firewall to allow port 22",
                    "Verify IP address and hostname",
                    "Check network connectivity with ping"
                ],
                'severity': 'high',
                'diagnostic': 'Test-NetConnection -Port 22 -ComputerName <host>'
            },
            'authentication_failed': {
                'category': ErrorCategory.AUTHENTICATION,
                'causes': [
                    "Incorrect username or password",
                    "SSH key not configured properly",
                    "Account locked out",
                    "Authentication method not allowed"
                ],
                'fixes': [
                    "Verify username and password in .env file",
                    "Check SSH key path and permissions",
                    "Unlock account if locked",
                    "Ensure password authentication is enabled in sshd_config"
                ],
                'severity': 'high',
                'diagnostic': 'Get-LocalUser | Where-Object Enabled -eq True'
            },
            'site_not_found': {
                'category': ErrorCategory.IIS_OPERATION,
                'causes': [
                    "Site name doesn't exist in IIS",
                    "Site name typo",
                    "Site is in different IIS server"
                ],
                'fixes': [
                    "List IIS sites: appcmd list site",
                    "Verify exact site name",
                    "Check correct IIS server"
                ],
                'severity': 'medium',
                'diagnostic': 'appcmd list site'
            },
            'path_not_found': {
                'category': ErrorCategory.FILE_OPERATION,
                'causes': [
                    "Incorrect path provided",
                    "Path doesn't exist on remote server",
                    "Drive letter issue on Windows",
                    "Permissions issue"
                ],
                'fixes': [
                    "Verify path exists on remote server",
                    "Use correct Windows path format (E:\\...)",
                    "Check permissions on parent folders",
                    "Use PowerShell to test path: Test-Path"
                ],
                'severity': 'medium',
                'diagnostic': 'Test-Path "<path>"'
            },
            'access_denied': {
                'category': ErrorCategory.FILE_OPERATION,
                'causes': [
                    "Insufficient permissions on files/folders",
                    "File in use by another process",
                    "Antivirus blocking access"
                ],
                'fixes': [
                    "Run with elevated privileges",
                    "Close applications using the files",
                    "Temporarily disable antivirus",
                    "Take ownership of files"
                ],
                'severity': 'high',
                'diagnostic': 'icacls "<path>"'
            },
            'no_zip_found': {
                'category': ErrorCategory.BACKUP_DETECTION,
                'causes': [
                    "No .zip file in backup directory",
                    "Backup directory empty",
                    "Wrong backup path specified"
                ],
                'fixes': [
                    "Verify backup directory has .zip file",
                    "Check backup path is correct",
                    "List files in backup directory"
                ],
                'severity': 'medium',
                'diagnostic': 'Get-ChildItem -Path "<path>" -Filter *.zip'
            },
            'multiple_zips_found': {
                'category': ErrorCategory.BACKUP_DETECTION,
                'causes': [
                    "Multiple .zip files in backup directory",
                    "Backup directory not cleaned up",
                    "Old backup files not removed"
                ],
                'fixes': [
                    "Use folder mode for multiple backups",
                    "Remove extra .zip files",
                    "Specify exact backup file path"
                ],
                'severity': 'medium',
                'diagnostic': 'Get-ChildItem -Path "<path>" -Filter *.zip | Select-Object Name'
            }
        }
        
        logger.info("DebuggerAgent initialized")
    
    def analyze_error(
        self,
        error_message: str,
        context: Dict[str, Any] = None
    ) -> ErrorAnalysis:
        """
        Analyze a single error message.
        
        Args:
            error_message: Error message to analyze
            context: Additional context about the error
            
        Returns:
            ErrorAnalysis with diagnosis and fixes
        """
        error_lower = error_message.lower()
        context = context or {}
        
        # Match error pattern
        matched_pattern = None
        
        for pattern_name, pattern_data in self.error_patterns.items():
            if pattern_name in error_lower:
                matched_pattern = pattern_data
                break
        
        if matched_pattern:
            return ErrorAnalysis(
                category=matched_pattern['category'],
                message=error_message,
                possible_causes=matched_pattern['causes'],
                suggested_fixes=matched_pattern['fixes'],
                severity=matched_pattern['severity'],
                diagnostic_command=matched_pattern['diagnostic']
            )
        
        # Generic analysis for unknown errors
        return ErrorAnalysis(
            category=ErrorCategory.UNKNOWN,
            message=error_message,
            possible_causes=[
                "Unexpected error condition",
                "Resource exhaustion",
                "Software bug or limitation"
            ],
            suggested_fixes=[
                "Review detailed error logs",
                "Try with verbose logging enabled",
                "Check system resources (memory, disk space)"
            ],
            severity="medium",
            diagnostic_command=None
        )
    
    def analyze_errors(
        self,
        errors: List[str],
        context: Dict[str, Any] = None
    ) -> DiagnosticReport:
        """
        Analyze multiple errors and generate diagnostic report.
        
        Args:
            errors: List of error messages
            context: Additional context
            
        Returns:
            DiagnosticReport with complete analysis
        """
        analyses = []
        recommendations = []
        severity_scores = []
        
        for error in errors:
            analysis = self.analyze_error(error, context)
            analyses.append(analysis)
            
            if analysis.severity in ['high', 'critical']:
                severity_scores.append(2)
            elif analysis.severity == 'medium':
                severity_scores.append(1)
            else:
                severity_scores.append(0)
        
        # Generate recommendations
        for analysis in analyses:
            if analysis.suggested_fixes:
                recommendations.append(
                    f"[{analysis.category.value}] {analysis.suggested_fixes[0]}"
                )
        
        # Determine overall health
        if not severity_scores:
            overall_health = "healthy"
        elif max(severity_scores) >= 2:
            overall_health = "critical"
        elif sum(severity_scores) > len(severity_scores):
            overall_health = "degraded"
        else:
            overall_health = "warning"
        
        requires_attention = overall_health in ['critical', 'degraded']
        
        logger.info(
            f"Diagnostic report: {len(analyses)} errors, "
            f"health={overall_health}"
        )
        
        return DiagnosticReport(
            errors=analyses,
            overall_health=overall_health,
            recommendations=recommendations,
            requires_attention=requires_attention
        )
    
    def run_diagnostics(
        self,
        ssh: SSHExecutor,
        diagnostics: List[str]
    ) -> Dict[str, Any]:
        """
        Run diagnostic commands on the remote server.
        
        Args:
            ssh: SSH executor instance
            diagnostics: List of diagnostic commands to run
            
        Returns:
            Dict with diagnostic results
        """
        results = {}
        
        for diag in diagnostics:
            try:
                result = ssh.execute_command(diag, powershell=True)
                results[diag] = {
                    'success': result['success'],
                    'output': result['stdout'],
                    'error': result['stderr']
                }
            except Exception as e:
                results[diag] = {
                    'success': False,
                    'output': '',
                    'error': str(e)
                }
        
        return results
    
    def get_ssh_diagnostics(self) -> List[str]:
        """
        Get recommended SSH diagnostic commands.
        
        Returns:
            List of diagnostic PowerShell commands
        """
        return [
            # Connection tests
            'Test-NetConnection -ComputerName $env:SSH_HOST -Port 22',
            # Service status
            'Get-Service -Name sshd | Select-Object Name, Status',
            # SSH config check
            'Get-Content $env:ProgramData/ssh/sshd_config | Select-String -Pattern "Port|PasswordAuthentication"',
            # User check
            'Get-LocalUser | Where-Object Enabled -eq True | Select-Object Name',
        ]
    
    def get_iis_diagnostics(self, site_name: str) -> List[str]:
        """
        Get recommended IIS diagnostic commands.
        
        Args:
            site_name: Name of the IIS site
            
        Returns:
            List of diagnostic PowerShell commands
        """
        return [
            # List all sites
            'appcmd list site',
            # Site status
            f'Get-Website -Name "{site_name}" | Select-Object Name, State, PhysicalPath',
            # Application pools
            'appcmd list apppool',
            # Site bindings
            f'Get-WebBinding -Name "{site_name}"',
        ]
    
    def get_file_diagnostics(self, path: str) -> List[str]:
        """
        Get recommended file system diagnostic commands.
        
        Args:
            path: Path to check
            
        Returns:
            List of diagnostic PowerShell commands
        """
        return [
            # Check path exists
            f'Test-Path -Path "{path}"',
            # List directory contents
            f'Get-ChildItem -Path "{path}" | Select-Object Name',
            # Check permissions
            f'icacls "{path}"',
            # Check disk space
            'Get-Volume | Select-Object DriveLetter, Size, FreeSpace',
        ]
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI Agent instance.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
    
    def __repr__(self) -> str:
        """String representation of DebuggerAgent."""
        return f"DebuggerAgent(patterns={len(self.error_patterns)})"


def create_debugger_agent() -> Agent:
    """
    Factory function to create Debugger Agent.
    
    Returns:
        CrewAI Agent configured for debugging
    """
    agent = DebuggerAgent()
    return agent.get_agent()