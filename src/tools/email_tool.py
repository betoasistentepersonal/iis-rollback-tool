"""
Email Tool - Gmail Integration for Notifications
================================================

This module provides functionality for sending email notifications via Gmail
using SMTP or Google App Passwords for secure authentication.

Author: CrewAI Team
Version: 1.0.0
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import smtplib

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """
    Configuration for email/Gmail notifications.
    
    Attributes:
        smtp_server: SMTP server address
        smtp_port: SMTP port number
        sender_email: Sender email address
        sender_password: Sender app password or password
        use_tls: Whether to use TLS encryption
    """
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str
    sender_password: str
    use_tls: bool = True


class EmailNotifier:
    """
    Sends email notifications via Gmail SMTP.
    
    This class provides methods for:
    - Sending progress updates
    - Sending completion notifications
    - Sending error alerts
    
    Attributes:
        config: Email configuration
        recipient_emails: List of recipient email addresses
        
    Example:
        >>> config = EmailConfig(sender_email="my@gmail.com", sender_password="app_pass")
        >>> email = EmailNotifier(config, ["recipient@example.com"])
        >>> email.send_progress("Rollback started", "MyWebsite")
    """
    
    def __init__(
        self,
        config: EmailConfig,
        recipient_emails: List[str]
    ):
        """
        Initialize Email Notifier with configuration.
        
        Args:
            config: EmailConfig instance with SMTP settings
            recipient_emails: List of email addresses to receive notifications
        """
        self.config = config
        self.recipient_emails = recipient_emails
        
        logger.info(
            f"EmailNotifier initialized for {len(recipient_emails)} recipient(s)"
        )
    
    def _create_message(
        self,
        subject: str,
        body_html: str,
        body_text: str
    ) -> MIMEMultipart:
        """
        Create a MIME email message.
        
        Args:
            subject: Email subject line
            body_html: HTML formatted body
            body_text: Plain text body
            
        Returns:
            MIMEMultipart message ready to send
        """
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = formataddr(
            ("IIS Rollback POC", self.config.sender_email)
        )
        message['To'] = ', '.join(self.recipient_emails)
        
        # Attach plain text and HTML versions
        part1 = MIMEText(body_text, 'plain')
        part2 = MIMEText(body_html, 'html')
        
        message.attach(part1)
        message.attach(part2)
        
        return message
    
    def _format_html_body(
        self,
        title: str,
        status: str,
        site_name: str,
        details: Dict[str, Any],
        timestamp: str
    ) -> str:
        """
        Format HTML email body.
        
        Args:
            title: Email title
            status: Status message
            site_name: IIS site name
            details: Additional details dictionary
            timestamp: Operation timestamp
            
        Returns:
            HTML formatted email body
        """
        status_color = "#28a745" if "success" in status.lower() else "#dc3545"
        
        details_html = ""
        for key, value in details.items():
            details_html += f"<tr><td style='padding: 8px;'><strong>{key}:</strong></td><td style='padding: 8px;'>{value}</td></tr>"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .status {{ padding: 10px; background-color: {status_color}; color: white; text-align: center; border-radius: 5px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    <div class="status">
                        <strong>{status}</strong>
                    </div>
                    <table>
                        <tr><td style='padding: 8px;'><strong>Site Name:</strong></td><td style='padding: 8px;'>{site_name}</td></tr>
                        <tr><td style='padding: 8px;'><strong>Timestamp:</strong></td><td style='padding: 8px;'>{timestamp}</td></tr>
                        {details_html}
                    </table>
                </div>
                <div class="footer">
                    <p>This is an automated message from IIS Rollback POC</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_text_body(
        self,
        title: str,
        status: str,
        site_name: str,
        details: Dict[str, Any],
        timestamp: str
    ) -> str:
        """
        Format plain text email body.
        
        Args:
            title: Email title
            status: Status message
            site_name: IIS site name
            details: Additional details dictionary
            timestamp: Operation timestamp
            
        Returns:
            Plain text email body
        """
        details_text = "\n".join([f"  {key}: {value}" for key, value in details.items()])
        
        text = f"""
{title}
{'=' * len(title)}

Status: {status}

Site Name: {site_name}
Timestamp: {timestamp}

Details:
{details_text}

---
This is an automated message from IIS Rollback POC
"""
        return text
    
    def send_notification(
        self,
        title: str,
        status: str,
        site_name: str,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a notification email.
        
        Args:
            title: Email title
            status: Status message (e.g., "Success" or "Failed")
            site_name: IIS site name
            details: Additional details to include
            
        Returns:
            Dict with send result
        """
        if details is None:
            details = {}
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Sending notification email: {title} - {status}")
        
        # Format email content
        body_html = self._format_html_body(title, status, site_name, details, timestamp)
        body_text = self._format_text_body(title, status, site_name, details, timestamp)
        
        message = self._create_message(
            f"[IIS Rollback] {title} - {status}",
            body_html,
            body_text
        )
        
        return self._send_email(message)
    
    def send_progress_update(
        self,
        site_name: str,
        step: str,
        progress: int,
        total_steps: int
    ) -> Dict[str, Any]:
        """
        Send a progress update email.
        
        Args:
            site_name: IIS site name
            step: Current step description
            progress: Current step number
            total_steps: Total number of steps
            
        Returns:
            Dict with send result
        """
        percentage = (progress / total_steps) * 100
        
        return self.send_notification(
            title="Rollback Progress Update",
            status=f"Step {progress}/{total_steps} ({percentage:.0f}%)",
            site_name=site_name,
            details={
                "Current Step": step,
                "Progress": f"{percentage:.0f}%",
                "Completed": f"{progress}/{total_steps} steps"
            }
        )
    
    def send_completion_notification(
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
            success: Whether operation completed successfully
            backup_path: Path to backup (if created)
            error_message: Error message (if failed)
            
        Returns:
            Dict with send result
        """
        status = "SUCCESS" if success else "FAILED"
        
        details = {}
        if backup_path:
            details["Backup Path"] = backup_path
        if error_message:
            details["Error"] = error_message
        
        return self.send_notification(
            title="Rollback Operation Completed",
            status=status,
            site_name=site_name,
            details=details
        )
    
    def _send_email(self, message: MIMEMultipart) -> Dict[str, Any]:
        """
        Internal method to send email via SMTP.
        
        Args:
            message: MIMEMultipart message to send
            
        Returns:
            Dict with send result
        """
        try:
            # Connect to SMTP server
            with smtplib.SMTP(
                self.config.smtp_server,
                self.config.smtp_port
            ) as server:
                server.ehlo()
                
                # Use TLS if configured
                if self.config.use_tls:
                    server.starttls()
                    server.ehlo()
                
                # Login
                server.login(
                    self.config.sender_email,
                    self.config.sender_password
                )
                
                # Send email
                server.sendmail(
                    self.config.sender_email,
                    self.recipient_emails,
                    message.as_string()
                )
            
            logger.info(f"Email sent successfully to {self.recipient_emails}")
            return {
                'success': True,
                'message': f"Email sent to {', '.join(self.recipient_emails)}"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {
                'success': False,
                'message': f"Authentication failed: {str(e)}"
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                'success': False,
                'message': f"SMTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                'success': False,
                'message': f"Failed to send email: {str(e)}"
            }
    
    @classmethod
    def from_env(cls) -> 'EmailNotifier':
        """
        Create EmailNotifier from environment variables.
        
        Requires:
        - GMAIL_SENDER_EMAIL
        - GMAIL_APP_PASSWORD
        - GMAIL_RECIPIENT_EMAIL (comma-separated for multiple recipients)
        
        Returns:
            EmailNotifier instance
        """
        config = EmailConfig(
            sender_email=os.environ.get('GMAIL_SENDER_EMAIL', ''),
            sender_password=os.environ.get('GMAIL_APP_PASSWORD', '')
        )
        
        recipients_str = os.environ.get('GMAIL_RECIPIENT_EMAIL', '')
        recipient_emails = [
            email.strip() for email in recipients_str.split(',')
            if email.strip()
        ]
        
        return cls(config, recipient_emails)
    
    def __repr__(self) -> str:
        """String representation of EmailNotifier instance."""
        return (
            f"EmailNotifier(recipients={len(self.recipient_emails)}, "
            f"sender={self.config.sender_email})"
        )