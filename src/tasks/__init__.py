"""
Tasks Package - CrewAI Task Definitions
========================================

This package contains task definitions for each CrewAI agent:

1. Requirements Tasks (requirements_tasks.py)
   - Task to validate requirements before rollback

2. Documentation Tasks (documentation_tasks.py)
   - Task to document process and send updates

3. Development Tasks (development_tasks.py)
   - Task to execute the rollback operation

4. Debugging Tasks (debugging_tasks.py)
   - Task to troubleshoot issues

5. Testing Tasks (testing_tasks.py)
   - Task to run tests and validate functionality
"""

from .requirements_tasks import (
    validate_requirements_task,
    create_requirements_report_task
)
from .documentation_tasks import (
    document_process_task,
    send_progress_update_task,
    generate_report_task
)
from .development_tasks import (
    execute_rollback_task,
    create_backup_task,
    restore_site_task
)
from .debugging_tasks import (
    diagnose_error_task,
    run_diagnostics_task
)
from .testing_tasks import (
    run_tests_task,
    write_test_task
)

__all__ = [
    # Requirements
    "validate_requirements_task",
    "create_requirements_report_task",
    
    # Documentation
    "document_process_task",
    "send_progress_update_task",
    "generate_report_task",
    
    # Development
    "execute_rollback_task",
    "create_backup_task",
    "restore_site_task",
    
    # Debugging
    "diagnose_error_task",
    "run_diagnostics_task",
    
    # Testing
    "run_tests_task",
    "write_test_task",
]