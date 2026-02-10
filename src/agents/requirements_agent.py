"""
Requirements Agent - Identifies and Validates Requirements
==========================================================

This agent is responsible for:
- Identifying all requirements for the IIS rollback operation
- Validating that prerequisites are met
- Checking configuration and connectivity
- Ensuring all necessary resources are available

Author: CrewAI Team
Version: 1.0.0
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from crewai import Agent

logger = logging.getLogger(__name__)


@dataclass
class Requirement:
    """
    Represents a single requirement that must be met.
    
    Attributes:
        name: Human-readable name of the requirement
        category: Category (config, connectivity, resource)
        is_met: Whether the requirement is currently met
        description: Detailed description
        check_command: Command to run for verification
    """
    name: str
    category: str
    is_met: bool = False
    description: str = ""
    check_command: Optional[str] = None
    error_message: str = ""


@dataclass
class RequirementsCheckResult:
    """
    Result of requirements validation.
    
    Attributes:
        all_met: Whether all requirements are met
        total_count: Total number of requirements
        met_count: Number of requirements that are met
        requirements: List of individual requirements
        missing_prerequisites: List of missing prerequisites
    """
    all_met: bool
    total_count: int
    met_count: int
    requirements: List[Requirement]
    missing_prerequisites: List[str]
    recommendations: List[str] = field(default_factory=list)


class RequirementsAgent:
    """
    Agent responsible for identifying and validating requirements.
    
    This agent ensures that all prerequisites are met before
    proceeding with the rollback operation.
    
    Attributes:
        agent: CrewAI Agent instance
        
    Example:
        >>> agent = RequirementsAgent()
        >>> result = agent.check_requirements("MyWebsite", "E:\\Backups")
        >>> if result.all_met:
        ...     print("All requirements met!")
    """
    
    def __init__(self):
        """Initialize the Requirements Agent."""
        self.agent = Agent(
            role="Requirements Analyst",
            goal="Identify and validate all requirements for IIS rollback operations",
            backstory="""You are an expert systems analyst with extensive 
            experience in Windows Server administration and IIS deployment. 
            Your specialty is ensuring all prerequisites are met before 
            executing critical operations like rollbacks. You are thorough, 
            methodical, and never skip a step.""",
            verbose=True
        )
        
        logger.info("RequirementsAgent initialized")
    
    def create_requirements_list(
        self,
        site_name: str,
        backup_path: str
    ) -> List[Requirement]:
        """
        Create a list of requirements for the rollback operation.
        
        Args:
            site_name: Name of the IIS site
            backup_path: Path to the backup directory
            
        Returns:
            List of Requirement objects
        """
        requirements = [
            # Configuration Requirements
            Requirement(
                name="SSH Host Configured",
                category="config",
                description="SSH host address must be configured in environment",
                check_command="SSH_HOST"
            ),
            Requirement(
                name="SSH Username Configured",
                category="config",
                description="SSH username must be configured in environment",
                check_command="SSH_USERNAME"
            ),
            Requirement(
                name="SSH Password or Key Configured",
                category="config",
                description="Either SSH password or SSH key path must be configured",
                check_command="SSH_PASSWORD or SSH_KEY_PATH"
            ),
            Requirement(
                name="IIS Site Name Provided",
                category="config",
                description="IIS site name must be specified",
                check_command="site_name parameter"
            ),
            Requirement(
                name="Backup Path Provided",
                category="config",
                description="Backup path must be specified",
                check_command="backup_path parameter"
            ),
            
            # Connectivity Requirements
            Requirement(
                name="Windows Server Accessible",
                category="connectivity",
                description="Windows Server must be reachable via SSH",
                check_command="ping test"
            ),
            Requirement(
                name="SSH Port Open",
                category="connectivity",
                description="SSH port (default 22) must be open",
                check_command="port connectivity test"
            ),
            
            # Resource Requirements
            Requirement(
                name="Site Path Exists",
                category="resource",
                description="IIS site root path must exist",
                check_command=f"Test-Path '{site_name}'"
            ),
            Requirement(
                name="Backup Path Exists",
                category="resource",
                description="Backup path must exist",
                check_command=f"Test-Path '{backup_path}'"
            ),
            Requirement(
                name="Sufficient Disk Space",
                category="resource",
                description="Sufficient disk space for rollback operation",
                check_command="disk space check"
            ),
        ]
        
        return requirements
    
    def check_config_requirements(self) -> Dict[str, bool]:
        """
        Check configuration requirements from environment.
        
        Returns:
            Dict mapping requirement names to met status
        """
        checks = {
            "SSH_HOST": bool(os.environ.get('SSH_HOST')),
            "SSH_USERNAME": bool(os.environ.get('SSH_USERNAME')),
            "SSH_AUTH": bool(
                os.environ.get('SSH_PASSWORD') or 
                os.environ.get('SSH_KEY_PATH')
            ),
        }
        
        return checks
    
    def check_requirements(
        self,
        site_name: str,
        site_path: str,
        backup_path: str
    ) -> RequirementsCheckResult:
        """
        Perform complete requirements check.
        
        Args:
            site_name: Name of the IIS site
            site_path: Path to the IIS site root
            backup_path: Path to the backup directory
            
        Returns:
            RequirementsCheckResult with all check results
        """
        logger.info(f"Checking requirements for site: {site_name}")
        
        requirements = self.create_requirements_list(site_name, backup_path)
        
        # Check config requirements
        config_checks = self.check_config_requirements()
        
        for req in requirements:
            if req.category == "config":
                if req.check_command == "SSH_HOST":
                    req.is_met = config_checks["SSH_HOST"]
                    req.error_message = "SSH_HOST not set in environment" if not req.is_met else ""
                elif req.check_command == "SSH_USERNAME":
                    req.is_met = config_checks["SSH_USERNAME"]
                    req.error_message = "SSH_USERNAME not set in environment" if not req.is_met else ""
                elif req.check_command in ["SSH_PASSWORD or SSH_KEY_PATH"]:
                    req.is_met = config_checks["SSH_AUTH"]
                    req.error_message = "Neither SSH_PASSWORD nor SSH_KEY_PATH set" if not req.is_met else ""
                elif req.check_command == "site_name parameter":
                    req.is_met = bool(site_name)
                    req.error_message = "site_name not provided" if not req.is_met else ""
                elif req.check_command == "backup_path parameter":
                    req.is_met = bool(backup_path)
                    req.error_message = "backup_path not provided" if not req.is_met else ""
        
        met_count = sum(1 for req in requirements if req.is_met)
        total_count = len(requirements)
        
        missing_prerequisites = [
            req.name for req in requirements 
            if not req.is_met and req.category in ["config", "resource"]
        ]
        
        recommendations = []
        if not config_checks["SSH_HOST"]:
            recommendations.append("Set SSH_HOST in .env file")
        if not config_checks["SSH_USERNAME"]:
            recommendations.append("Set SSH_USERNAME in .env file")
        if not config_checks["SSH_AUTH"]:
            recommendations.append("Set SSH_PASSWORD or SSH_KEY_PATH in .env file")
        
        result = RequirementsCheckResult(
            all_met=met_count == total_count,
            total_count=total_count,
            met_count=met_count,
            requirements=requirements,
            missing_prerequisites=missing_prerequisites,
            recommendations=recommendations
        )
        
        logger.info(
            f"Requirements check complete: {met_count}/{total_count} met"
        )
        
        return result
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI Agent instance.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
    
    def __repr__(self) -> str:
        """String representation of RequirementsAgent."""
        return "RequirementsAgent()"


def create_requirements_agent() -> Agent:
    """
    Factory function to create Requirements Agent.
    
    Returns:
        CrewAI Agent configured for requirements analysis
    """
    agent = RequirementsAgent()
    return agent.get_agent()