"""
Documentation Agent - Documents Process and Sends Gmail Updates
===============================================================

This agent is responsible for:
- Documenting the rollback process
- Sending progress updates via Gmail
- Recording results and creating reports
- Maintaining operation logs

Author: CrewAI Team
Version: 1.0.0
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from crewai import Agent

from ..tools.email_tool import EmailNotifier, EmailConfig

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class ProgressEntry:
    """
    Represents a progress entry in the operation log.
    
    Attributes:
        timestamp: When the entry was created
        step: Step name or number
        status: Status (started, completed, failed)
        message: Detailed message
        details: Additional details dictionary
    """
    timestamp: str
    step: str
    status: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackReport:
    """
    Complete report of a rollback operation.
    
    Attributes:
        site_name: Name of the IIS site
        start_time: Operation start time
        end_time: Operation end time
        success: Whether operation succeeded
        backup_type: Type of backup (ZIP or folder)
        steps: List of progress entries
        errors: List of errors encountered
        total_duration_seconds: Duration in seconds
    """
    site_name: str
    start_time: str
    end_time: str
    success: bool
    backup_type: str
    steps: List[ProgressEntry]
    errors: List[str]
    total_duration_seconds: float
    report_path: Optional[str] = None


class DocumentationAgent:
    """
    Agent responsible for documentation and notifications.
    
    This agent:
    - Tracks progress throughout the rollback operation
    - Sends email notifications via Gmail
    - Generates detailed operation reports
    - Maintains logs for audit purposes
    
    Attributes:
        agent: CrewAI Agent instance
        progress_log: List of progress entries
        email_notifier: Email notifier instance (optional)
    """
    
    def __init__(self, email_notifier: Optional[EmailNotifier] = None):
        """
        Initialize the Documentation Agent.
        
        Args:
            email_notifier: Optional EmailNotifier instance for Gmail notifications
        """
        self.agent = Agent(
            role="Documentation Specialist",
            goal="Document the rollback process and keep stakeholders informed",
            backstory="""You are a technical writer and documentation expert 
            with experience in IT operations. You excel at creating clear, 
            comprehensive documentation and keeping stakeholders informed 
            through regular updates. You are meticulous about details and 
            never miss a status change.""",
            verbose=True
        )
        
        self.progress_log: List[ProgressEntry] = []
        self.email_notifier = email_notifier
        self.start_time = datetime.now()
        
        logger.info("DocumentationAgent initialized")
    
    def log_progress(
        self,
        step: str,
        status: str,
        message: str,
        details: Dict[str, Any] = None
    ) -> ProgressEntry:
        """
        Log a progress entry.
        
        Args:
            step: Step name or number
            status: Status (started, completed, failed)
            message: Detailed message
            details: Additional details dictionary
            
        Returns:
            ProgressEntry object
        """
        entry = ProgressEntry(
            timestamp=datetime.now().isoformat(),
            step=step,
            status=status,
            message=message,
            details=details or {}
        )
        
        self.progress_log.append(entry)
        
        if status == "completed":
            logger.info(f"[{step}] {message}")
        elif status == "failed":
            logger.error(f"[{step}] {message}")
        else:
            logger.debug(f"[{step}] {message}")
        
        return entry
    
    def send_progress_email(
        self,
        site_name: str,
        step: str,
        progress: int,
        total_steps: int,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a progress update email.
        
        Args:
            site_name: IIS site name
            step: Current step
            progress: Current step number
            total_steps: Total number of steps
            details: Additional details
            
        Returns:
            Dict with send result
        """
        if not self.email_notifier:
            logger.warning("Email notifier not configured, skipping email")
            return {'success': False, 'message': 'Email notifier not configured'}
        
        return self.email_notifier.send_progress_update(
            site_name=site_name,
            step=step,
            progress=progress,
            total_steps=total_steps
        )
    
    def send_completion_email(
        self,
        site_name: str,
        success: bool,
        backup_path: str = None,
        error_message: str = None
    ) -> Dict[str, Any]:
        """
        Send completion notification email.
        
        Args:
            site_name: IIS site name
            success: Whether operation succeeded
            backup_path: Path to backup (if created)
            error_message: Error message (if failed)
            
        Returns:
            Dict with send result
        """
        if not self.email_notifier:
            logger.warning("Email notifier not configured, skipping email")
            return {'success': False, 'message': 'Email notifier not configured'}
        
        return self.email_notifier.send_completion_notification(
            site_name=site_name,
            success=success,
            backup_path=backup_path,
            error_message=error_message
        )
    
    def generate_report(
        self,
        site_name: str,
        backup_type: str,
        success: bool,
        errors: List[str] = None
    ) -> RollbackReport:
        """
        Generate a complete rollback report.
        
        Args:
            site_name: Name of the IIS site
            backup_type: Type of backup used
            success: Whether operation succeeded
            errors: List of errors encountered
            
        Returns:
            RollbackReport object
        """
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = RollbackReport(
            site_name=site_name,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            success=success,
            backup_type=backup_type,
            steps=self.progress_log,
            errors=errors or [],
            total_duration_seconds=total_duration
        )
        
        logger.info(
            f"Report generated for {site_name}: "
            f"success={success}, duration={total_duration:.2f}s"
        )
        
        return report
    
    def save_report(
        self,
        report: RollbackReport,
        output_dir: str = "."
    ) -> str:
        """
        Save the report to a JSON file.
        
        Args:
            report: RollbackReport to save
            output_dir: Output directory for the report
            
        Returns:
            Path to saved report file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Convert report to dict
        report_dict = {
            'site_name': report.site_name,
            'start_time': report.start_time,
            'end_time': report.end_time,
            'success': report.success,
            'backup_type': report.backup_type,
            'total_duration_seconds': report.total_duration_seconds,
            'errors': report.errors,
            'steps': [
                {
                    'timestamp': step.timestamp,
                    'step': step.step,
                    'status': step.status,
                    'message': step.message,
                    'details': step.details
                }
                for step in report.steps
            ]
        }
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rollback_report_{report.site_name}_{timestamp}.json"
        file_path = output_path / filename
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        report.report_path = str(file_path)
        
        logger.info(f"Report saved to: {file_path}")
        
        return str(file_path)
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI Agent instance.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
    
    def get_progress_log(self) -> List[ProgressEntry]:
        """
        Get the current progress log.
        
        Returns:
            List of ProgressEntry objects
        """
        return self.progress_log
    
    def clear_log(self) -> None:
        """Clear the progress log."""
        self.progress_log = []
        self.start_time = datetime.now()
        logger.info("Progress log cleared")
    
    def __repr__(self) -> str:
        """String representation of DocumentationAgent."""
        email_status = "configured" if self.email_notifier else "not configured"
        return f"DocumentationAgent(email={email_status}, log_entries={len(self.progress_log)})"


def create_documentation_agent(
    sender_email: str = None,
    sender_password: str = None,
    recipient_emails: List[str] = None
) -> DocumentationAgent:
    """
    Factory function to create Documentation Agent with email support.
    
    Args:
        sender_email: Gmail sender email (defaults to env var)
        sender_password: Gmail app password (defaults to env var)
        recipient_emails: List of recipient emails (defaults to env var)
        
    Returns:
        DocumentationAgent instance
    """
    email_notifier = None
    
    # Try to create email notifier from environment or parameters
    if sender_email and sender_password and recipient_emails:
        config = EmailConfig(
            sender_email=sender_email,
            sender_password=sender_password
        )
        email_notifier = EmailNotifier(config, recipient_emails)
    else:
        # Try to create from environment
        try:
            email_notifier = EmailNotifier.from_env()
        except Exception as e:
            logger.warning(f"Could not create email notifier from env: {e}")
    
    return DocumentationAgent(email_notifier=email_notifier)