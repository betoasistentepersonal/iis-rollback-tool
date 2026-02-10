"""
Tests for IIS Tool
==================

Unit tests for the IIS management module.
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

from src.tools.iis_tool import IISManager, IISSite


class TestIISSite:
    """Tests for IISSite dataclass."""
    
    def test_create_site(self):
        """Test creating an IISSite object."""
        site = IISSite(
            name="MyWebsite",
            id="1",
            bindings=["*:80:www.example.com", "*:443:www.example.com"],
            state="Started",
            physical_path="E:\\Web Sites\\MyWebsite"
        )
        
        assert site.name == "MyWebsite"
        assert site.id == "1"
        assert len(site.bindings) == 2
        assert site.state == "Started"
        assert site.physical_path == "E:\\Web Sites\\MyWebsite"
    
    def test_site_equality(self):
        """Test IISSite equality comparison."""
        site1 = IISSite(
            name="MyWebsite",
            id="1",
            bindings=[],
            state="Started",
            physical_path="E:\\Web Sites\\MyWebsite"
        )
        site2 = IISSite(
            name="MyWebsite",
            id="1",
            bindings=[],
            state="Started",
            physical_path="E:\\Web Sites\\MyWebsite"
        )
        
        # Dataclasses don't compare equal by default
        assert site1 == site2


class TestIISManager:
    """Tests for IISManager class."""
    
    @pytest.fixture
    def mock_ssh(self):
        """Create a mock SSH executor."""
        ssh = MagicMock()
        ssh.is_connected.return_value = True
        return ssh
    
    def test_init(self, mock_ssh):
        """Test IISManager initialization."""
        manager = IISManager(mock_ssh)
        
        assert manager.ssh == mock_ssh
    
    @pytest.fixture
    def iis_manager(self, mock_ssh):
        """Create an IISManager instance."""
        return IISManager(mock_ssh)
    
    def test_list_sites_empty(self, iis_manager, mock_ssh):
        """Test listing sites when none exist."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': '',
            'stderr': '',
            'return_code': 0
        }
        
        sites = iis_manager.list_sites()
        
        assert sites == []
    
    def test_list_sites_with_data(self, iis_manager, mock_ssh):
        """Test listing sites with data."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Site1|1|Started|E:\\Web Sites\\Site1|*:80:example.com\nSite2|2|Stopped|E:\\Web Sites\\Site2|*:80:example2.com',
            'stderr': '',
            'return_code': 0
        }
        
        sites = iis_manager.list_sites()
        
        assert len(sites) == 2
        assert sites[0].name == "Site1"
        assert sites[1].name == "Site2"
    
    def test_get_site_found(self, iis_manager, mock_ssh):
        """Test getting an existing site."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'MyWebsite|1|Started|E:\\Web Sites\\MyWebsite|*',
            'stderr': '',
            'return_code': 0
        }
        
        site = iis_manager.get_site("MyWebsite")
        
        assert site is not None
        assert site.name == "MyWebsite"
    
    def test_get_site_not_found(self, iis_manager, mock_ssh):
        """Test getting a non-existent site."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': '',
            'stderr': '',
            'return_code': 0
        }
        
        site = iis_manager.get_site("NonexistentSite")
        
        assert site is None
    
    def test_stop_site_success(self, iis_manager, mock_ssh):
        """Test stopping a site successfully."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': ' SITE object "MyWebsite" stopped',
            'stderr': '',
            'return_code': 0
        }
        
        result = iis_manager.stop_site("MyWebsite")
        
        assert result['success'] is True
        mock_ssh.execute_command.assert_called_with(
            'appcmd stop site "MyWebsite"',
            powershell=False
        )
    
    def test_stop_site_failure(self, iis_manager, mock_ssh):
        """Test failing to stop a site."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'ERROR ( message:Site "MyWebsite" could not be found. )',
            'return_code': 1
        }
        
        result = iis_manager.stop_site("MyWebsite")
        
        assert result['success'] is False
    
    def test_start_site_success(self, iis_manager, mock_ssh):
        """Test starting a site successfully."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': ' SITE object "MyWebsite" started',
            'stderr': '',
            'return_code': 0
        }
        
        result = iis_manager.start_site("MyWebsite")
        
        assert result['success'] is True
    
    def test_start_site_failure(self, iis_manager, mock_ssh):
        """Test failing to start a site."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'ERROR ( message:Site "MyWebsite" could not be found. )',
            'return_code': 1
        }
        
        result = iis_manager.start_site("MyWebsite")
        
        assert result['success'] is False
    
    def test_restart_site(self, iis_manager, mock_ssh):
        """Test restarting a site."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': ' SITE object "MyWebsite" stopped',
            'stderr': '',
            'return_code': 0
        }
        
        result = iis_manager.restart_site("MyWebsite")
        
        assert result['success'] is True
        # Should be called twice (stop and start)
        assert mock_ssh.execute_command.call_count == 2
    
    def test_get_site_state(self, iis_manager, mock_ssh):
        """Test getting site state."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Started',
            'stderr': '',
            'return_code': 0
        }
        
        state = iis_manager.get_site_state("MyWebsite")
        
        assert state == "Started"
    
    def test_delete_site_content_success(self, iis_manager, mock_ssh):
        """Test deleting site content successfully."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Content deletion complete',
            'stderr': '',
            'return_code': 0
        }
        
        result = iis_manager.delete_site_content(
            "E:\\Web Sites\\MyWebsite",
            keep_root=True
        )
        
        assert result['success'] is True
    
    def test_delete_site_content_without_keep_root(self, iis_manager, mock_ssh):
        """Test deleting site content without keeping root."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': 'Folder deletion complete',
            'stderr': '',
            'return_code': 0
        }
        
        result = iis_manager.delete_site_content(
            "E:\\Web Sites\\MyWebsite",
            keep_root=False
        )
        
        assert result['success'] is True
    
    def test_copy_files_success(self, iis_manager, mock_ssh):
        """Test copying files with robocopy."""
        mock_ssh.execute_command.return_value = {
            'success': True,
            'stdout': '...',
            'stderr': '',
            'return_code': 1
        }
        
        result = iis_manager.copy_files(
            "E:\\Backups\\Backup20240101",
            "E:\\Web Sites\\MyWebsite"
        )
        
        assert result['success'] is True
        assert "robocopy" in mock_ssh.execute_command.call_args[0][0]
    
    def test_copy_files_failure(self, iis_manager, mock_ssh):
        """Test failing to copy files."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Access is denied',
            'return_code': 8
        }
        
        result = iis_manager.copy_files(
            "E:\\Backups\\Backup20240101",
            "E:\\Web Sites\\MyWebsite"
        )
        
        assert result['success'] is False
    
    def test_repr(self, iis_manager):
        """Test string representation."""
        repr_str = repr(iis_manager)
        
        assert "IISManager" in repr_str


class TestIISManagerEdgeCases:
    """Edge case tests for IISManager."""
    
    @pytest.fixture
    def mock_ssh(self):
        """Create a mock SSH executor."""
        ssh = MagicMock()
        ssh.is_connected.return_value = True
        return ssh
    
    @pytest.fixture
    def iis_manager(self, mock_ssh):
        """Create an IISManager instance."""
        return IISManager(mock_ssh)
    
    def test_list_sites_command_failure(self, iis_manager, mock_ssh):
        """Test list sites when command fails."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Command failed',
            'return_code': 1
        }
        
        sites = iis_manager.list_sites()
        
        assert sites == []
    
    def test_get_site_state_not_found(self, iis_manager, mock_ssh):
        """Test getting state when site doesn't exist."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Error',
            'return_code': 1
        }
        
        state = iis_manager.get_site_state("NonexistentSite")
        
        assert state is None
    
    def test_delete_site_content_failure(self, iis_manager, mock_ssh):
        """Test failing to delete content."""
        mock_ssh.execute_command.return_value = {
            'success': False,
            'stdout': '',
            'stderr': 'Path not found',
            'return_code': 1
        }
        
        result = iis_manager.delete_site_content("E:\\Web Sites\\MyWebsite")
        
        assert result['success'] is False