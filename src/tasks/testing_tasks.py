"""
Testing Tasks - Task Definitions for Testing Agent
===================================================

This module contains task definitions for the Testing Agent.

Author: CrewAI Team
Version: 1.0.0
"""

from crewai import Task
from typing import Dict, Any, Optional


def run_tests_task(
    agent,
    test_type: str = "all",
    verbose: bool = True
) -> Task:
    """
    Create a task to run tests.
    
    Args:
        agent: Testing agent instance
        test_type: Type of tests to run (unit, integration, all)
        verbose: Whether to run with verbose output
        
    Returns:
        CrewAI Task for running tests
    """
    if test_type == "unit":
        description = """
        Run unit tests for the IIS Rollback POC:
        
        1. Test SSH tool functionality
        2. Test IIS tool functionality
        3. Test backup tool functionality
        4. Test email tool functionality
        5. Test agent functionality
        
        Exclude integration tests that require live server.
        Report test results with pass/fail status.
        """
    elif test_type == "integration":
        description = """
        Run integration tests for the IIS Rollback POC:
        
        1. Test end-to-end rollback flow
        2. Test error handling scenarios
        3. Test recovery procedures
        4. Test with mock SSH server
        
        Note: These tests may require environment configuration.
        Report test results with any setup requirements.
        """
    else:
        description = """
        Run all tests for the IIS Rollback POC:
        
        1. Run all unit tests
        2. Run all integration tests
        3. Check code coverage
        4. Generate test report
        
        Ensure all tests pass before proceeding.
        Report comprehensive test results.
        """
    
    return Task(
        description=description,
        expected_output="Test results with pass/fail status and coverage",
        agent=agent
    )


def write_test_task(
    agent,
    module_name: str,
    test_type: str = "unit",
    examples: bool = True
) -> Task:
    """
    Create a task to write tests for a module.
    
    Args:
        agent: Testing agent instance
        module_name: Name of the module to test
        test_type: Type of tests (unit, integration)
        examples: Whether to include example tests
        
    Returns:
        CrewAI Task for writing tests
    """
    return Task(
        description=f"""
        Write comprehensive tests for the {module_name} module.
        
        Include:
        1. Unit tests for all public functions
        2. Tests for edge cases and error conditions
        3. Tests for boundary conditions
        4. Mock external dependencies
        
        Generate test file in the tests/ directory.
        Ensure tests are well-documented and follow pytest conventions.
        """,
        expected_output=f"Test file for {module_name}",
        agent=agent
    )