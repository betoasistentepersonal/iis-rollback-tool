"""
Testing Agent - Writes and Runs Tests
======================================

This agent is responsible for:
- Writing unit tests for all components
- Writing integration tests
- Running tests and reporting results
- Ensuring code quality and coverage

Author: CrewAI Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from crewai import Agent

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """
    Result of a single test or test suite.
    
    Attributes:
        name: Test name or description
        passed: Whether test passed
        duration: Duration in seconds
        error: Error message if failed
        output: Test output
    """
    name: str
    passed: bool
    duration: float = 0.0
    error: str = ""
    output: str = ""


@dataclass
class TestSuiteResult:
    """
    Result of a complete test suite.
    
    Attributes:
        total_tests: Total number of tests
        passed: Number of tests passed
        failed: Number of tests failed
        skipped: Number of tests skipped
        duration: Total duration in seconds
        results: List of individual test results
        coverage: Code coverage percentage (if available)
    """
    total_tests: int
    passed: int
    failed: int
    skipped: int = 0
    duration: float = 0.0
    results: List[TestResult] = None
    coverage: Optional[float] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    @property
    def success(self) -> bool:
        """Return True if all tests passed."""
        return self.failed == 0


class TestingAgent:
    """
    Agent responsible for testing the rollback functionality.
    
    This agent:
    - Writes unit tests for all components
    - Writes integration tests
    - Executes test suites
    - Reports test results and coverage
    - Validates code quality
    
    Attributes:
        agent: CrewAI Agent instance
        project_root: Root directory of the project
        test_dir: Directory containing tests
    """
    
    def __init__(self, project_root: str = None):
        """
        Initialize the Testing Agent.
        
        Args:
            project_root: Root directory of the project (auto-detected if None)
        """
        self.agent = Agent(
            role="QA Engineer",
            goal="Ensure code quality through comprehensive testing",
            backstory="""You are a senior QA engineer with extensive 
            experience in automated testing, test-driven development, 
            and continuous integration. You believe that well-tested 
            code is reliable code and never compromise on test coverage. 
            You are meticulous about edge cases and error handling.""",
            verbose=True
        )
        
        # Detect project root
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Assume we're in the project root
            self.project_root = Path(__file__).parent.parent.parent
        
        self.test_dir = self.project_root / "tests"
        
        logger.info(f"TestingAgent initialized (project: {self.project_root})")
    
    def run_unit_tests(
        self,
        test_files: List[str] = None,
        verbose: bool = True
    ) -> TestSuiteResult:
        """
        Run unit tests for the project.
        
        Args:
            test_files: Specific test files to run (all if None)
            verbose: Whether to run with verbose output
            
        Returns:
            TestSuiteResult with test outcomes
        """
        import time
        start_time = time.time()
        
        logger.info("Running unit tests...")
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        
        if test_files:
            cmd.extend(test_files)
        else:
            # Run all tests in tests directory
            cmd.extend([str(self.test_dir), "-k", "not integration"])
        
        # Add coverage if configured
        try:
            import pytest_cov
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        except ImportError:
            pass
        
        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        duration = time.time() - start_time
        
        # Parse results
        results = self._parse_pytest_output(result.stdout + result.stderr)
        
        # Count results
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        
        suite_result = TestSuiteResult(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            duration=duration,
            results=results
        )
        
        logger.info(
            f"Unit tests complete: {passed}/{suite_result.total_tests} passed "
            f"in {duration:.2f}s"
        )
        
        return suite_result
    
    def run_integration_tests(
        self,
        verbose: bool = True
    ) -> TestSuiteResult:
        """
        Run integration tests.
        
        Args:
            verbose: Whether to run with verbose output
            
        Returns:
            TestSuiteResult with test outcomes
        """
        import time
        start_time = time.time()
        
        logger.info("Running integration tests...")
        
        cmd = [sys.executable, "-m", "pytest"]
        
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        
        # Run only integration tests
        cmd.extend([str(self.test_dir), "-k", "integration"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        duration = time.time() - start_time
        
        results = self._parse_pytest_output(result.stdout + result.stderr)
        
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        
        suite_result = TestSuiteResult(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            duration=duration,
            results=results
        )
        
        logger.info(
            f"Integration tests complete: {passed}/{suite_result.total_tests} passed "
            f"in {duration:.2f}s"
        )
        
        return suite_result
    
    def run_all_tests(self, verbose: bool = True) -> TestSuiteResult:
        """
        Run all tests (unit and integration).
        
        Args:
            verbose: Whether to run with verbose output
            
        Returns:
            TestSuiteResult with test outcomes
        """
        import time
        start_time = time.time()
        
        logger.info("Running all tests...")
        
        cmd = [sys.executable, "-m", "pytest", str(self.test_dir)]
        
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        duration = time.time() - start_time
        
        results = self._parse_pytest_output(result.stdout + result.stderr)
        
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        
        # Try to extract coverage
        coverage = self._extract_coverage(result.stdout + result.stderr)
        
        suite_result = TestSuiteResult(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            duration=duration,
            results=results,
            coverage=coverage
        )
        
        logger.info(
            f"All tests complete: {passed}/{suite_result.total_tests} passed "
            f"in {duration:.2f}s"
        )
        
        return suite_result
    
    def _parse_pytest_output(self, output: str) -> List[TestResult]:
        """
        Parse pytest output to extract test results.
        
        Args:
            output: Raw pytest output
            
        Returns:
            List of TestResult objects
        """
        results = []
        
        # Parse PASSED lines
        import re
        
        # Match patterns like "tests/test_ssh_tool.py::test_connect PASSED"
        passed_pattern = r'(tests/[\w/]+\.py::\w+) PASSED'
        for match in re.finditer(passed_pattern, output):
            results.append(TestResult(
                name=match.group(1),
                passed=True
            ))
        
        # Match patterns like "tests/test_ssh_tool.py::test_connect FAILED"
        failed_pattern = r'(tests/[\w/]+\.py::\w+) FAILED'
        for match in re.finditer(failed_pattern, output):
            results.append(TestResult(
                name=match.group(1),
                passed=False,
                error="Test failed"
            ))
        
        return results
    
    def _extract_coverage(self, output: str) -> Optional[float]:
        """
        Extract coverage percentage from pytest output.
        
        Args:
            output: Raw pytest output with coverage
            
        Returns:
            Coverage percentage or None
        """
        import re
        
        # Look for coverage summary like "Coverage: 85%"
        pattern = r'Coverage:\s*(\d+(?:\.\d+)?)%'
        match = re.search(pattern, output)
        
        if match:
            return float(match.group(1))
        
        return None
    
    def write_test(
        self,
        test_name: str,
        test_code: str,
        test_file: str = None
    ) -> str:
        """
        Write a new test file.
        
        Args:
            test_name: Name of the test
            test_code: Python test code
            test_file: Target file path (auto-generated if None)
            
        Returns:
            Path to created test file
        """
        if not test_file:
            # Generate filename from test name
            filename = test_name.lower().replace(' ', '_') + '.py'
            test_file = self.test_dir / filename
        
        # Ensure test directory exists
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        logger.info(f"Test file created: {test_file}")
        
        return str(test_file)
    
    def generate_test_template(
        self,
        module_name: str,
        class_name: str = None
    ) -> str:
        """
        Generate a test file template for a module.
        
        Args:
            module_name: Name of the module to test
            class_name: Optional class name to test
            
        Returns:
            Test file template as string
        """
        template = f'''"""
Tests for {module_name}
=======================

Auto-generated test template.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class Test{class_name or module_name.title().replace('_', '')}:
    """Test cases for {module_name}."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pass
    
    def teardown_method(self):
        """Clean up after tests."""
        pass
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # TODO: Implement test
        pass
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # TODO: Implement test
        pass
    
    def test_error_handling(self):
        """Test error handling."""
        # TODO: Implement test
        pass
'''
        return template
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        Check if all required dependencies are installed.
        
        Returns:
            Dict mapping package names to installation status
        """
        required_packages = [
            'pytest',
            'paramiko',
            'tenacity',
            'crewai',
            'langchain',
            'openai'
        ]
        
        installed = {}
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                installed[package] = True
            except ImportError:
                installed[package] = False
        
        missing = [p for p, installed_flag in installed.items() if not installed_flag]
        
        if missing:
            logger.warning(f"Missing dependencies: {', '.join(missing)}")
        else:
            logger.info("All required dependencies are installed")
        
        return installed
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI Agent instance.
        
        Returns:
            CrewAI Agent instance
        """
        return self.agent
    
    def __repr__(self) -> str:
        """String representation of TestingAgent."""
        return f"TestingAgent(project={self.project_root})"


def create_testing_agent(project_root: str = None) -> Agent:
    """
    Factory function to create Testing Agent.
    
    Args:
        project_root: Optional project root path
        
    Returns:
        CrewAI Agent configured for testing
    """
    agent = TestingAgent(project_root)
    return agent.get_agent()