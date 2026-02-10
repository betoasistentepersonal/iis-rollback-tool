"""
Tests for Backup Tool
=====================

Unit tests for the backup management module.
Requires mocking for remote execution.

Author: CrewAI Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.backup_tool import (
    BackupManager,
    BackupType,
    RollbackMode,
    BackupInfo
)


class TestBackupType:
    """Tests for BackupType enum."""
    
    def test_zip_type(self):
        """Test ZIP backup type."""
        assert BackupType.ZIP.value == "zip"
    
    def test_folder_type(self):
        """Test folder backup type."""
        assert BackupType.FOLDER.value == "folder"
    
    def test_unknown_type(self):
        """Test unknown backup type."""
        assert BackupType.UNKNOWN.value == "unknown"


class TestRollbackMode:
    """Tests for RollbackMode enum."""
    
    def test_zip_mode(self):
        """Test ZIP rollback mode."""
        assert RollbackMode.ZIP.value == "zip"
    
    def test_folder_mode(self):
        """Test folder rollback mode."""
        assert RollbackMode.FOLDER.value == "folder"
    
    def test_none_mode(self):
        """Test none rollback mode."""
        assert RollbackMode.NONE.value == "none"


class TestBackupInfo:
    """Tests for BackupInfo dataclass."""
    
    def test_create_backup_info(self):
        """Test creating BackupInfo object."""
        from datetime import datetime
        
        info = BackupInfo(
            path="E:\\Backups\\MyWebsite",
            type=BackupType.ZIP,
            name="backup.zip",
            timestamp=datetime.now()
        )
        
        assert info.path == "E:\\Backups\\MyWebsite"
        assert info.type == BackupType.ZIP
        assert info.name == "backup.zip"
    
    def test_folder_backup_info(self):
        """Test folder backup info."""
        from datetime import datetime
        
        info = BackupInfo(
            path="E:\\Backups\\MyWebsite\\Backup20240101",
            type=BackupType.FOLDER,
            name="Backup20240101",
            timestamp=datetime.now()
        )
        
        assert info.type == BackupType.FOLDER


class TestBackupManager:
    """Tests for BackupManager class."""
    
    @pytest.fixture
    def mock_ssh(self):
        """Create a mock SSH executor."""
        ssh = MagicMock()
        ssh.is_connected.return_value = True
        return ssh
    
    @pytest.fixture
    def mock_iis(self):
        """Create a mock IIS manager."""
        iis = MagicMock()
        return iis
    
    @pytest.fixture
    def backup_manager(self, mock_ssh, mock_iis):
        """Create a BackupManager instance."""
        return BackupManager(mock_ssh, mock_iis)
    
    def test_init(self, backup_manager):
        """Test BackupManager initialization."""
        assert backup_manager.ssh is not None
        assert backup_manager.iis is not None
        assert backup_manager.temp_folder is None
    
    def test_detect_backup_type_zip(self, backup_manager, mock_ssh):
        """Test detecting ZIP backup type."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': '1',
            'stderr': '',
            'return_code': 0
        }
        
        result = backup_manager.detect_backup_type("E:\\Backups\\MyWebsite")
        
        assert result['type'] == RollbackMode.ZIP
        assert result['zip_count'] == 1
    
    def test_detect_backup_type_folder(self, backup_manager, mock_ssh):
        """Test detecting folder backup type."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': '0',
            'stderr': '',
            'return_code': 0
        }
        
        result = backup_manager.detect_backup_type("E:\\Backups\\MyWebsite")
        
        assert result['type'] == RollbackMode.FOLDER
        assert result['zip_count'] == 0
    
    def test_detect_backup_type_abort(self, backup_manager, mock_ssh):
        """Test detecting multiple ZIP files (abort)."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': '3',
            'stderr': '',
            'return_code': 0
        }
        
        result = backup_manager.detect_backup_type("E:\\Backups\\MyWebsite")
        
        assert result['type'] == RollbackMode.NONE
        assert result['zip_count'] == 3
    
    def test_detect_backup_type_command_failure(self, backup_manager, mock_ssh):
        """Test backup detection when command fails."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Command failed',
            'return_code': 1
        }
        
        result = backup_manager.detect_backup_type("E:\\Backups\\MyWebsite")
        
        assert result['type'] == RollbackMode.NONE
        assert result['zip_count'] == -1
    
    def test_create_temp_folder(self, backup_manager, mock_ssh):
        """Test creating temp folder."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Created',
            'stderr': '',
            'return_code': 0
        }
        
        temp_folder = backup_manager.create_temp_folder("E:\\Temp")
        
        assert "Rollback_" in temp_folder
        assert "E:\\Temp" in temp_folder
        assert backup_manager.temp_folder == temp_folder
    
    def test_extract_zip_success(self, backup_manager, mock_ssh):
        """Test extracting ZIP archive."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Extraction complete',
            'stderr': '',
            'return_code': 0
        }
        
        result = backup_manager.extract_zip(
            "E:\\Backups\\backup.zip",
            "E:\\Temp\\Rollback_20240101"
        )
        
        assert result['success'] is True
        assert "Expand-Archive" in mock_ssh.execute_command.call_args[0][0]
    
    def test_extract_zip_failure(self, backup_manager, mock_ssh):
        """Test failing to extract ZIP."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'ZIP file is corrupt',
            'return_code': 1
        }
        
        result = backup_manager.extract_zip(
            "E:\\Backups\\backup.zip",
            "E:\\Temp\\Rollback_20240101"
        )
        
        assert result['success'] is False
    
    def test_create_preventive_backup_success(self, backup_manager, mock_ssh):
        """Test creating preventive backup."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Backup created',
            'stderr': '',
            'return_code': 0
        }
        
        result = backup_manager.create_preventive_backup(
            "E:\\Web Sites\\MyWebsite",
            "E:\\Web Sites Backups\\MyWebsite",
            "MyWebsite"
        )
        
        assert result['success'] is True
        assert 'backup_path' in result
        assert 'PreRollback_' in result['backup_path']
    
    def test_create_preventive_backup_failure(self, backup_manager, mock_ssh):
        """Test failing to create preventive backup."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Access denied',
            'return_code': 1
        }
        
        result = backup_manager.create_preventive_backup(
            "E:\\Web Sites\\MyWebsite",
            "E:\\Web Sites Backups\\MyWebsite",
            "MyWebsite"
        )
        
        assert result['success'] is False
    
    def test_cleanup_temp_folder_success(self, backup_manager, mock_ssh):
        """Test cleaning up temp folder."""
        backup_manager.temp_folder = "E:\\Temp\\Rollback_20240101"
        
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Cleanup complete',
            'stderr': '',
            'return_code': 0
        }
        
        result = backup_manager.cleanup_temp_folder()
        
        assert result['success'] is True
        assert backup_manager.temp_folder is None
    
    def test_cleanup_temp_folder_none(self, backup_manager, mock_ssh):
        """Test cleaning up when no temp folder exists."""
        result = backup_manager.cleanup_temp_folder()
        
        assert result['success'] is True
        assert "No temp folder" in result['message']
    
    def test_get_rollback_result_success(self, backup_manager):
        """Test generating successful rollback result."""
        details = {
            'mode': 'ZIP',
            'backup_path': 'E:\\Backups\\backup.zip'
        }
        
        result = backup_manager.get_rollback_result(
            site_name="MyWebsite",
            success=True,
            details=details
        )
        
        assert result['success'] is True
        assert result['site_name'] == "MyWebsite"
        assert "successfully" in result['message']
    
    def test_get_rollback_result_failure(self, backup_manager):
        """Test generating failed rollback result."""
        details = {
            'error': 'Failed to copy files'
        }
        
        result = backup_manager.get_rollback_result(
            site_name="MyWebsite",
            success=False,
            details=details
        )
        
        assert result['success'] is False
        assert "failed" in result['message']
    
    def test_repr(self, backup_manager):
        """Test string representation."""
        repr_str = repr(backup_manager)
        
        assert "BackupManager" in repr_str


class TestBackupManagerEdgeCases:
    """Edge case tests for BackupManager."""
    
    @pytest.fixture
    def mock_ssh(self):
        """Create a mock SSH executor."""
        ssh = MagicMock()
        ssh.is_connected.return_value = True
        return ssh
    
    @pytest.fixture
    def mock_iis(self):
        """Create a mock IIS manager."""
        iis = MagicMock()
        return iis
    
    @pytest.fixture
    def backup_manager(self, mock_ssh, mock_iis):
        """Create a BackupManager instance."""
        return BackupManager(mock_ssh, mock_iis)
    
    def test_create_temp_folder_failure(self, backup_manager, mock_ssh):
        """Test failing to create temp folder."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Access denied',
            'return_code': 1
        }
        
        with pytest.raises(RuntimeError):
            backup_manager.create_temp_folder("E:\\Temp")
    
    def test_cleanup_temp_folder_failure(self, backup_manager, mock_ssh):
        """Test failing to clean up temp folder."""
        backup_manager.temp_folder = "E:\\Temp\\Rollback_20240101"
        
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Folder in use',
            'return_code': 1
        }
        
        result = backup_manager.cleanup_temp_folder()
        
        assert result['success'] is False
        # Temp folder should still be set (cleanup failed)
        assert backup_manager.temp_folder is not None