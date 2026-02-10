"""
Agents Package - CrewAI Agents for IIS Rollback
===============================================

This package contains CrewAI agents for the IIS rollback POC:

1. Requirements Agent (requirements_agent.py)
   - Identifies and validates requirements
   - Ensures all prerequisites are met

2. Documentation Agent (documentation_agent.py)
   - Documents the process
   - Sends progress updates via Gmail

3. Developer Agent (developer_agent.py)
   - Implements rollback functionality
   - Executes the main rollback flow

4. Debugger Agent (debugger_agent.py)
   - Troubleshoots issues
   - Provides error analysis and solutions

5. Testing Agent (testing_agent.py)
   - Writes and runs tests
   - Validates functionality
"""

from .requirements_agent import RequirementsAgent
from .documentation_agent import DocumentationAgent
from .developer_agent import DeveloperAgent
from .debugger_agent import DebuggerAgent
from .testing_agent import TestingAgent

__all__ = [
    "RequirementsAgent",
    "DocumentationAgent",
    "DeveloperAgent",
    "DebuggerAgent",
    "TestingAgent",
]