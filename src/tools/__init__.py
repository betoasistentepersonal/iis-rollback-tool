"""
Tools Package - Core Functionality Modules
==========================================

This package contains the core tools for IIS rollback operations:

1. SSH Tool (ssh_tool.py)
   - Remote command execution via SSH
   - Connection management and retry logic
   - PowerShell command execution

2. IIS Tool (iis_tool.py)
   - IIS website management
   - Site start/stop operations
   - Content management with robocopy

3. Backup Tool (backup_tool.py)
   - Backup type detection
   - ZIP extraction
   - Preventive backup creation
   - Rollback result logging

4. Email Tool (email_tool.py)
   - Gmail SMTP integration
   - Progress notifications
   - Completion/error alerts
"""

from .ssh_tool import SSHExecutor, SSHConfig
from .iis_tool import IISManager, IISSite
from .backup_tool import (
    BackupManager,
    BackupType,
    RollbackMode,
    BackupInfo
)
from .email_tool import EmailNotifier, EmailConfig

__all__ = [
    # SSH
    "SSHExecutor",
    "SSHConfig",
    
    # IIS
    "IISManager",
    "IISSite",
    
    # Backup
    "BackupManager",
    "BackupType",
    "RollbackMode",
    "BackupInfo",
    
    # Email
    "EmailNotifier",
    "EmailConfig",
]