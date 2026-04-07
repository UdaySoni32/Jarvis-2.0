# JARVIS 2.0 Setup Guide - Ubuntu/Linux

Complete setup instructions for installing and testing JARVIS 2.0 on a fresh Ubuntu machine.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.10 or higher
- Git
- Internet connection

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/UdaySoni32/Jarvis-2.0.git

# Navigate to the project directory
cd Jarvis-2.0
```

## Step 2: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies for plugins
sudo apt install -y \
    scrot \
    tesseract-ocr \
    tesseract-ocr-eng \
    xclip \
    xsel \
    curl \
    wget \
    git

# Optional: Install Docker (if you want Docker integration)
# sudo apt install -y docker.io
# sudo systemctl start docker
# sudo systemctl enable docker
# sudo usermod -aG docker $USER  # Add your user to docker group
```

## Step 3: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 4: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter permission issues on some systems, use:
# pip install -r requirements.txt --user
```

## Step 5: Configure JARVIS

```bash
# Run the setup wizard
python -m src.setup_wizard

# Follow the prompts to:
# - Enter your OpenAI API key
# - Configure AI model preferences
# - Set up plugin preferences
# - Configure voice settings (optional)
```

### Manual Configuration (Alternative)

If you prefer manual setup, create `config/settings.json`:

```bash
mkdir -p config
cat > config/settings.json << 'EOF'
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your-openai-api-key-here",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "plugins": {
    "enabled": [
      "file_operations",
      "system_info",
      "web_search",
      "code_analyzer",
      "task_manager",
      "learning_system",
      "automation_engine",
      "database_integration",
      "github_integration",
      "docker_integration",
      "clipboard_manager",
      "api_testing",
      "screen_capture_ocr"
    ]
  },
  "voice": {
    "enabled": false,
    "engine": "pyttsx3",
    "rate": 150,
    "volume": 0.9
  },
  "context": {
    "max_history": 50,
    "save_conversations": true
  }
}
EOF
```

## Step 6: Run Tests

```bash
# Run all tests to verify installation
python -m pytest tests/ -v

# Run specific plugin tests
python -m pytest tests/test_database_integration.py -v
python -m pytest tests/test_github_integration.py -v
python -m pytest tests/test_docker_integration.py -v
python -m pytest tests/test_clipboard_manager.py -v
python -m pytest tests/test_api_testing.py -v
python -m pytest tests/test_screen_capture_ocr.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

## Step 7: Start JARVIS

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start JARVIS in interactive mode
python main.py

# Or start with specific mode
python main.py --mode interactive
python main.py --mode voice  # Requires voice setup
```

## Quick Test Commands

Once JARVIS is running, try these commands:

```
# Basic AI interaction
> Hello JARVIS, introduce yourself

# System information
> What's my system status?

# File operations
> List files in my home directory

# Web search
> Search for "Python async programming"

# Task management
> Create a task to review code at 3 PM today

# Code analysis (if you have Python files)
> Analyze the code in src/main.py

# Database operations (after setting up a connection)
> Connect to SQLite database at ./test.db
> Show me the database schema

# GitHub operations (after auth)
> List my GitHub repositories
```

## Testing Individual Plugins

### 1. Database Integration

```bash
# Install PostgreSQL (optional)
sudo apt install -y postgresql postgresql-contrib

# Or test with SQLite (no installation needed)
python << 'EOF'
import asyncio
from src.plugins.database_integration import DatabaseIntegrationTool

async def test_db():
    tool = DatabaseIntegrationTool()
    # Create SQLite connection
    result = await tool.execute(
        action="create_connection",
        connection_name="test",
        database_type="sqlite",
        database="test.db"
    )
    print(result)

asyncio.run(test_db())
EOF
```

### 2. GitHub Integration

```bash
# Test GitHub plugin
python << 'EOF'
import asyncio
from src.plugins.github_integration import GitHubIntegrationTool

async def test_github():
    tool = GitHubIntegrationTool()
    # Test without auth (limited access)
    result = await tool.execute(
        action="get_repo",
        repo="UdaySoni32/Jarvis-2.0"
    )
    print(result)

asyncio.run(test_github())
EOF
```

### 3. Docker Integration

```bash
# Test Docker plugin (requires Docker installed)
python << 'EOF'
import asyncio
from src.plugins.docker_integration import DockerIntegrationTool

async def test_docker():
    tool = DockerIntegrationTool()
    result = await tool.execute(action="list_containers")
    print(result)

asyncio.run(test_docker())
EOF
```

### 4. Clipboard Manager

```bash
# Test clipboard
python << 'EOF'
import asyncio
from src.plugins.clipboard_manager import ClipboardManagerTool

async def test_clipboard():
    tool = ClipboardManagerTool()
    # Copy text
    result = await tool.execute(
        action="copy",
        text="Hello from JARVIS!"
    )
    print(result)
    # Paste text
    result = await tool.execute(action="paste")
    print(result)

asyncio.run(test_clipboard())
EOF
```

### 5. Screen Capture & OCR

```bash
# Test screen capture
python << 'EOF'
import asyncio
from src.plugins.screen_capture_ocr import ScreenCaptureOCRTool

async def test_screenshot():
    tool = ScreenCaptureOCRTool()
    # Capture screen
    result = await tool.execute(action="capture_screen")
    print(result)

asyncio.run(test_screenshot())
EOF
```

### 6. API Testing

```bash
# Test API testing plugin
python << 'EOF'
import asyncio
from src.plugins.api_testing import APITestingTool

async def test_api():
    tool = APITestingTool()
    result = await tool.execute(
        action="send_request",
        method="GET",
        url="https://api.github.com"
    )
    print(result)

asyncio.run(test_api())
EOF
```

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python3 --version  # Should be 3.10+

# If version is too old, install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### Permission Errors

```bash
# If you get permission errors with pip
pip install -r requirements.txt --user

# If Docker permission denied
sudo usermod -aG docker $USER
newgrp docker  # Refresh groups without logging out
```

### Missing Dependencies

```bash
# If scrot not found
sudo apt install -y scrot

# If tesseract not found
sudo apt install -y tesseract-ocr tesseract-ocr-eng

# If xclip/xsel not found
sudo apt install -y xclip xsel
```

### Virtual Environment Issues

```bash
# If venv creation fails
sudo apt install -y python3-venv

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Database Connection Issues

```bash
# For PostgreSQL
sudo apt install -y libpq-dev

# For MySQL
sudo apt install -y default-libmysqlclient-dev

# Reinstall database drivers
pip install psycopg2-binary pymysql motor aiosqlite
```

## Verification Checklist

- [ ] Repository cloned successfully
- [ ] System dependencies installed
- [ ] Python virtual environment created
- [ ] Python dependencies installed
- [ ] Configuration file created
- [ ] All tests passing
- [ ] JARVIS starts without errors
- [ ] Can interact with JARVIS
- [ ] Plugins respond correctly

## Environment Variables (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc for convenience

# JARVIS aliases
alias jarvis='cd ~/Jarvis-2.0 && source venv/bin/activate && python main.py'
alias jarvis-test='cd ~/Jarvis-2.0 && source venv/bin/activate && python -m pytest tests/ -v'

# OpenAI API Key (if not in config)
export OPENAI_API_KEY="your-api-key-here"

# GitHub Token (for GitHub integration)
export GITHUB_TOKEN="your-github-token-here"
```

## Next Steps

After setup:
1. Explore the plugins in `src/plugins/`
2. Read the documentation in `PHASE_*.md` files
3. Check out the project plan in `PROJECT_PLAN.md`
4. Join the development by creating issues or PRs

## Getting Help

- **Documentation**: Check `README.md` and phase documentation
- **Issues**: https://github.com/UdaySoni32/Jarvis-2.0/issues
- **Tests**: Run `pytest tests/ -v` to see what's working

## System Requirements

**Minimum:**
- 2 GB RAM
- 1 GB disk space
- Ubuntu 20.04+
- Python 3.10+

**Recommended:**
- 4 GB RAM
- 2 GB disk space
- Ubuntu 22.04+
- Python 3.11+
- Docker installed
- PostgreSQL/MySQL for database features

## Quick Start Script

Save this as `quick_setup.sh` and run `bash quick_setup.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 JARVIS 2.0 Quick Setup"
echo "=========================="

# Clone repository
echo "📦 Cloning repository..."
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0

# Install system dependencies
echo "📥 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv scrot tesseract-ocr xclip xsel

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start JARVIS:"
echo "  cd Jarvis-2.0"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "First run the setup wizard:"
echo "  python -m src.setup_wizard"
```

---

**Ready to use JARVIS 2.0!** 🎉
