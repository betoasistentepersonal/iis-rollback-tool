# IIS Rollback Tool

**Production-ready IIS Rollback Tool via SSH on Windows Server**

Built with CrewAI for intelligent orchestration of rollback operations.

---

**Repository:** https://github.com/betoasistentepersonal/iis-rollback-tool

## Overview

This project automates the rollback process for IIS websites by:
- Connecting to Windows Server via SSH
- Detecting backup type (ZIP or folder)
- Creating preventive backups
- Stopping IIS site
- Rolling back content
- Starting IIS site
- Logging results
- Sending email notifications

## Features

- **SSH Remote Execution**: Execute PowerShell commands on Windows Server remotely
- **ZIP and Folder Support**: Handles both ZIP archives and direct folder backups
- **Preventive Backup**: Creates automatic backup before rollback
- **Comprehensive Logging**: Detailed logging of all operations
- **Email Notifications**: Gmail integration for progress updates
- **Error Handling**: Robust error handling with graceful failure recovery

## Project Structure

```
crewai_iis_rollback/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── requirements_agent.py
│   │   ├── documentation_agent.py
│   │   ├── developer_agent.py
│   │   ├── debugger_agent.py
│   │   └── testing_agent.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── requirements_tasks.py
│   │   ├── documentation_tasks.py
│   │   ├── development_tasks.py
│   │   ├── debugging_tasks.py
│   │   └── testing_tasks.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── ssh_tool.py
│   │   ├── iis_tool.py
│   │   ├── backup_tool.py
│   │   └── email_tool.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_ssh_tool.py
│   ├── test_iis_tool.py
│   ├── test_backup_tool.py
│   └── test_integration.py
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## Installation

```bash
# Clone the repository
git clone https://github.com/betoasistentepersonal/iis-rollback-tool.git
cd iis-rollback-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Edit the `.env` file with your settings:

```env
# SSH Connection
SSH_HOST=192.168.1.100
SSH_PORT=22
SSH_USERNAME=admin
SSH_PASSWORD=your_password

# IIS Settings
IIS_SITE_NAME=MyWebsite
SITE_PATH=E:\Web Sites\MyWebsite
BACKUP_PATH=E:\Web Sites Backups\MyWebsite\Backup20240101

# Gmail (optional)
GMAIL_SENDER_EMAIL=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password
GMAIL_RECIPIENT_EMAIL=miretti20@gmail.com
```

## Rollback Flow

1. **SSH Connect**: Establish SSH connection to Windows Server
2. **Backup Detection**: Check backup path for ZIP files
   - 1 ZIP file → ZIP mode
   - >1 ZIP files → Abort (ambiguous)
   - 0 ZIP files → Folder mode
3. **ZIP Mode**:
   - Create temp folder: `E:\Temp\Rollback_[timestamp]`
   - Expand-Archive ZIP to temp folder
4. **Preventive Backup**: Create `E:\Web Sites Backups\[Sitio]\PreRollback_[timestamp]`
5. **Stop IIS**: Execute `appcmd stop site "IIS_SITE_NAME"`
6. **Delete Content**: Remove site content (keep root folder)
7. **Copy Backup**: Use robocopy to restore files
8. **Start IIS**: Execute `appcmd start site "IIS_SITE_NAME"`
9. **Cleanup**: Remove temp folder
10. **Log**: Record results

## Usage

### Basic Usage

```python
from main import run_rollback

# Run rollback with default settings
result = run_rollback(
    site_name="MyWebsite",
    backup_path="E:\\Web Sites Backups\\MyWebsite\\Backup20240101"
)
print(result)
```

### Using CrewAI Agents

```python
from crewai import Agent, Task, Crew
from src.agents.developer_agent import create_developer_agent

# Create agents
developer = create_developer_agent()

# Create tasks
task = Task(
    description="Execute IIS rollback for MyWebsite",
    agent=developer
)

# Run crew
crew = Crew(agents=[developer], tasks=[task])
result = crew.kickoff()
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_ssh_tool.py -v
```

## API Reference

### SSH Tool

```python
from src.tools.ssh_tool import SSHExecutor

# Create executor
ssh = SSHExecutor(
    host="192.168.1.100",
    username="admin",
    password="password"
)

# Execute command
result = ssh.execute_command("powershell Get-Process")
print(result.stdout)
```

### IIS Tool

```python
from src.tools.iis_tool import IISManager

iis = IISManager(ssh_executor=ssh)

# Stop site
iis.stop_site("MyWebsite")

# Start site
iis.start_site("MyWebsite")
```

## Agents

### Requirements Agent
Analyzes and identifies requirements for the rollback operation.

### Documentation Agent
Documents the process and sends progress updates via Gmail.

### Developer Agent
Implements and executes the rollback functionality.

### Debugger Agent
Troubleshoots issues during execution.

### Testing Agent
Writes and runs tests to ensure reliability.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open GitHub issue
- Email: miretti20@gmail.com
