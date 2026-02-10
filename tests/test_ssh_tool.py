"""
Tests for SSH Tool
==================

Unit tests for the SSH executor module.
Requires mock SSH server or mocking library.

Author: CrewAI Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.ssh_tool import SSHExecutor, SSHConfig


class TestSSHConfig:
    """Tests for SSHConfig dataclass."""
    
    def test_default_values(self):
        """Test SSHConfig default values."""
        config = SSHConfig(
            host="192.168.1.100",
            username="admin"
        )
        
        assert config.host == "192.168.1.100"
        assert config.port == 22  # default
        assert config.username == "admin"
        assert config.password is None  # default
        assert config.key_path is None  # default
        assert config.timeout == 30  # default
    
    def test_with_password(self):
        """Test SSHConfig with password."""
        config = SSHConfig(
            host="192.168.1.100",
            username="admin",
            password="secret"
        )
        
        assert config.password == "secret"
    
    def test_with_key_path(self):
        """Test SSHConfig with key path."""
        config = SSHConfig(
            host="192.168.1.100",
            username="admin",
            key_path="~/.ssh/id_rsa"
        )
        
        assert config.key_path == "~/.ssh/id_rsa"


class TestSSHExecutor:
    """Tests for SSHExecutor class."""
    
    @pytest.fixture
    def mock_ssh_client(self):
        """Create a mock SSH client."""
        with patch('src.tools.ssh_tool.SSHClient') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def valid_config(self):
        """Create a valid SSH configuration."""
        return SSHConfig(
            host="192.168.1.100",
            username="admin",
            password="secret"
        )
    
    def test_init_without_auth(self, valid_config):
        """Test SSHExecutor initialization without authentication."""
        config = SSHConfig(
            host="192.168.1.100",
            username="admin"
        )
        
        with pytest.raises(ValueError) as exc_info:
            SSHExecutor(config)
        
        assert "password" in str(exc_info.value).lower() or "key" in str(exc_info.value).lower()
    
    def test_init_with_password(self, valid_config):
        """Test SSHExecutor initialization with password."""
        executor = SSHExecutor(valid_config)
        
        assert executor.config.host == "192.168.1.100"
        assert executor.connected is False
    
    def test_init_with_key(self, valid_config):
        """Test SSHExecutor initialization with key path."""
        config = SSHConfig(
            host="192.168.1.100",
            username="admin",
            key_path="~/.ssh/id_rsa"
        )
        
        # Mock os.path.exists to return True
        with patch('os.path.exists', return_value=True):
            executor = SSHExecutor(config)
        
        assert executor.connected is False
    
    def test_init_with_invalid_key_path(self, valid_config):
        """Test SSHExecutor with invalid key path."""
        config = SSHConfig(
            host="192.168.1.100",
            username="admin",
            key_path="/nonexistent/path/id_rsa"
        )
        
        with pytest.raises(ValueError) as exc_info:
            SSHExecutor(config)
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_connect_success(self, mock_client_class, valid_config):
        """Test successful SSH connection."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        result = executor.connect()
        
        assert result is True
        assert executor.connected is True
        mock_client.connect.assert_called_once()
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_connect_already_connected(self, mock_client_class, valid_config):
        """Test connecting when already connected."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        executor.connect()  # First connection
        result = executor.connect()  # Second connection attempt
        
        assert result is True
        # Should only call connect once
        assert mock_client.connect.call_count == 1
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_disconnect(self, mock_client_class, valid_config):
        """Test SSH disconnection."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        executor.connect()
        executor.disconnect()
        
        assert executor.connected is False
        mock_client.close.assert_called_once()
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_disconnect_not_connected(self, mock_client_class, valid_config):
        """Test disconnection when not connected."""
        executor = SSHExecutor(valid_config)
        executor.disconnect()  # Should not raise
        
        assert executor.connected is False
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_execute_command_success(self, mock_client_class, valid_config):
        """Test successful command execution."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value = b"process output"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        executor.connect()
        
        result = executor.execute_command("Get-Process", powershell=True)
        
        assert result['success'] is True
        assert result['stdout'] == "process output"
        assert result['stderr'] == ""
        assert result['return_code'] == 0
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_execute_command_failure(self, mock_client_class, valid_config):
        """Test failed command execution."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"error occurred"
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        executor.connect()
        
        result = executor.execute_command("Get-Process", powershell=True)
        
        assert result['success'] is False
        assert result['return_code'] == 1
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_execute_command_not_connected(self, mock_client_class, valid_config):
        """Test command execution without connection."""
        executor = SSHExecutor(valid_config)
        
        with pytest.raises(RuntimeError) as exc_info:
            executor.execute_command("Get-Process")
        
        assert "Not connected" in str(exc_info.value)
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_context_manager(self, mock_client_class, valid_config):
        """Test SSHExecutor as context manager."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        with SSHExecutor(valid_config) as executor:
            assert executor.is_connected() is True
        
        assert executor.is_connected() is False
        mock_client.close.assert_called_once()
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_is_connected(self, mock_client_class, valid_config):
        """Test is_connected method."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        
        assert executor.is_connected() is False
        
        executor.connect()
        assert executor.is_connected() is True
        
        executor.disconnect()
        assert executor.is_connected() is False
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_repr(self, mock_client_class, valid_config):
        """Test string representation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        repr_str = repr(executor)
        
        assert "SSHExecutor" in repr_str
        assert "192.168.1.100" in repr_str


class TestSSHExecutorEdgeCases:
    """Edge case tests for SSHExecutor."""
    
    @pytest.fixture
    def valid_config(self):
        """Create a valid SSH configuration."""
        return SSHConfig(
            host="192.168.1.100",
            username="admin",
            password="secret"
        )
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_command_with_special_chars(self, mock_client_class, valid_config):
        """Test command execution with special characters."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value = b"output with \"quotes\" and 'apostrophes'"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        executor.connect()
        
        result = executor.execute_command("Test-Path 'C:\\Program Files\\'", powershell=True)
        
        assert result['success'] is True
    
    @patch('src.tools.ssh_tool.SSHClient')
    def test_empty_output(self, mock_client_class, valid_config):
        """Test command with empty output."""
        mock_client = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        mock_client_class.return_value = mock_client
        
        executor = SSHExecutor(valid_config)
        executor.connect()
        
        result = executor.execute_command("echo", powershell=True)
        
        assert result['success'] is True
        assert result['stdout'] == ""