"""
IIS Rollback POC - Main Entry Point
====================================

This module provides the main entry point for the IIS Rollback POC,
orchestrating CrewAI agents to execute the rollback operation.

Usage:
    python main.py --site <site_name> --backup <backup_path> [--host <ssh_host>] [--user <ssh_user>]

Author: CrewAI Team
Version: 1.0.0
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from crewai import Crew, Agent, Task

from .agents import (
    RequirementsAgent,
    DocumentationAgent,
    DeveloperAgent,
    DebuggerAgent,
    TestingAgent
)
from .tasks import (
    validate_requirements_task,
    document_process_task,
    execute_rollback_task,
    diagnose_error_task,
    run_tests_task
)
from .tools import (
    SSHConfig,
    RollbackConfig,
    EmailConfig,
    RollbackMode
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IISRollbackOrchestrator:
    """
    Orchestrates the IIS Rollback operation using CrewAI agents.
    
    This class coordinates multiple agents to perform a complete
    rollback operation with documentation and error handling.
    
    Attributes:
        agents: Dictionary of CrewAI agents
        config: Rollback configuration
    """
    
    def __init__(
        self,
        site_name: str,
        site_path: str,
        backup_path: str,
        ssh_config: SSHConfig
    ):
        """
        Initialize the orchestrator.
        
        Args:
            site_name: Name of the IIS site
            site_path: Path to the IIS site root
            backup_path: Path to the backup directory
            ssh_config: SSH connection configuration
        """
        self.site_name = site_name
        self.site_path = site_path
        self.backup_path = backup_path
        self.ssh_config = ssh_config
        
        # Initialize agents
        self._init_agents()
        
        logger.info("IISRollbackOrchestrator initialized")
    
    def _init_agents(self) -> None:
        """Initialize all CrewAI agents."""
        # Create agent instances
        self.requirements_agent = RequirementsAgent()
        self.documentation_agent = DocumentationAgent()
        self.developer_agent = DeveloperAgent()
        self.debugger_agent = DebuggerAgent()
        self.testing_agent = TestingAgent()
        
        logger.info("All agents initialized")
    
    def run_requirements_check(self) -> Dict[str, Any]:
        """
        Run requirements validation.
        
        Returns:
            Dict with requirements check results
        """
        logger.info("Running requirements check...")
        
        # Create validation task
        task = validate_requirements_task(
            agent=self.requirements_agent.get_agent(),
            site_name=self.site_name,
            site_path=self.site_path,
            backup_path=self.backup_path
        )
        
        # Execute with single agent
        crew = Crew(
            agents=[self.requirements_agent.get_agent()],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        
        logger.info("Requirements check completed")
        return {'result': result}
    
    def run_rollback(self) -> Dict[str, Any]:
        """
        Execute the complete rollback operation.
        
        Returns:
            Dict with rollback results
        """
        logger.info(f"Starting rollback for site: {self.site_name}")
        
        # Document the process
        doc_task = document_process_task(
            agent=self.documentation_agent.get_agent(),
            site_name=self.site_name,
            site_path=self.site_path,
            backup_path=self.backup_path
        )
        
        # Create rollback config
        rollback_config = RollbackConfig(
            site_name=self.site_name,
            site_path=self.site_path,
            backup_path=self.backup_path,
            ssh_config=self.ssh_config
        )
        
        # Execute rollback
        execute_task = execute_rollback_task(
            agent=self.developer_agent.get_agent(),
            site_name=self.site_name,
            site_path=self.site_path,
            backup_path=self.backup_path,
            ssh_host=self.ssh_config.host,
            ssh_username=self.ssh_config.username,
            ssh_password=self.ssh_config.password,
            ssh_key_path=self.ssh_config.key_path
        )
        
        # Run with developer agent
        crew = Crew(
            agents=[self.developer_agent.get_agent()],
            tasks=[execute_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        logger.info(f"Rollback completed with result: {result}")
        return {'result': result}
    
    def run_diagnostics(self, error_message: str) -> Dict[str, Any]:
        """
        Run diagnostics on an error.
        
        Args:
            error_message: Error message to diagnose
            
        Returns:
            Dict with diagnostic results
        """
        logger.info("Running diagnostics...")
        
        task = diagnose_error_task(
            agent=self.debugger_agent.get_agent(),
            error_message=error_message,
            context={
                'site_name': self.site_name,
                'site_path': self.site_path,
                'backup_path': self.backup_path
            }
        )
        
        crew = Crew(
            agents=[self.debugger_agent.get_agent()],
            tasks=[task],
            verbose=False
        )
        
        result = crew.kickoff()
        
        logger.info("Diagnostics completed")
        return {'result': result}
    
    def run_tests(self, test_type: str = "all") -> Dict[str, Any]:
        """
        Run tests.
        
        Args:
            test_type: Type of tests to run
            
        Returns:
            Dict with test results
        """
        logger.info(f"Running {test_type} tests...")
        
        # Note: Testing agent uses subprocess, so we run it directly
        result = self.testing_agent.run_all_tests()
        
        return {
            'total_tests': result.total_tests,
            'passed': result.passed,
            'failed': result.failed,
            'coverage': result.coverage
        }


def run_rollback(
    site_name: str,
    site_path: str,
    backup_path: str,
    ssh_host: str,
    ssh_username: str,
    ssh_password: str = None,
    ssh_key_path: str = None
) -> Dict[str, Any]:
    """
    Convenience function to run rollback operation.
    
    Args:
        site_name: Name of the IIS site
        site_path: Path to the IIS site root
        backup_path: Path to the backup directory
        ssh_host: SSH server hostname/IP
        ssh_username: SSH username
        ssh_password: SSH password (optional)
        ssh_key_path: Path to SSH private key (optional)
        
    Returns:
        Dict with rollback results
    """
    # Create SSH config
    ssh_config = SSHConfig(
        host=ssh_host,
        username=ssh_username,
        password=ssh_password,
        key_path=ssh_key_path
    )
    
    # Create orchestrator
    orchestrator = IISRollbackOrchestrator(
        site_name=site_name,
        site_path=site_path,
        backup_path=backup_path,
        ssh_config=ssh_config
    )
    
    # Run rollback
    return orchestrator.run_rollback()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='IIS Rollback POC - Execute rollback via SSH'
    )
    
    parser.add_argument(
        '--site', '-s',
        required=True,
        help='Name of the IIS site'
    )
    
    parser.add_argument(
        '--path', '-p',
        required=True,
        help='Path to the IIS site root'
    )
    
    parser.add_argument(
        '--backup', '-b',
        required=True,
        help='Path to the backup directory'
    )
    
    parser.add_argument(
        '--host', '-H',
        default=os.environ.get('SSH_HOST'),
        help='SSH server hostname/IP'
    )
    
    parser.add_argument(
        '--user', '-u',
        default=os.environ.get('SSH_USERNAME'),
        help='SSH username'
    )
    
    parser.add_argument(
        '--password', '-P',
        default=os.environ.get('SSH_PASSWORD'),
        help='SSH password'
    )
    
    parser.add_argument(
        '--key', '-k',
        default=os.environ.get('SSH_KEY_PATH'),
        help='Path to SSH private key'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run tests instead of rollback'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate required arguments
    if not args.host:
        parser.error("--host or SSH_HOST is required")
    if not args.user:
        parser.error("--user or SSH_USERNAME is required")
    if not args.password and not args.key:
        parser.error("Either --password or --key is required")
    
    if args.test:
        # Run tests
        from .agents import TestingAgent
        agent = TestingAgent()
        result = agent.run_all_tests()
        print(f"Tests: {result.passed}/{result.total_tests} passed")
        if result.coverage:
            print(f"Coverage: {result.coverage}%")
        return 0 if result.success else 1
    
    # Run rollback
    try:
        result = run_rollback(
            site_name=args.site,
            site_path=args.path,
            backup_path=args.backup,
            ssh_host=args.host,
            ssh_username=args.user,
            ssh_password=args.password,
            ssh_key_path=args.key
        )
        
        print(f"Rollback completed: {result}")
        return 0
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())