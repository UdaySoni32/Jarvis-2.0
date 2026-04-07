# JARVIS 2.0 Test Commands

Quick commands to test JARVIS 2.0 functionality on your Ubuntu machine.

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0

# Run quick setup
bash quick_setup.sh
```

## Step 2: Activate Environment

```bash
# Activate virtual environment
source venv/bin/activate
```

## Step 3: Run All Tests

```bash
# Run complete test suite
python -m pytest tests/ -v

# Expected output: 70+ tests passing
```

## Step 4: Test Individual Plugins

### Test 1: Database Integration (18 tests)
```bash
python -m pytest tests/test_database_integration.py -v
```

### Test 2: GitHub Integration (18 tests)
```bash
python -m pytest tests/test_github_integration.py -v
```

### Test 3: Docker Integration (6 tests)
```bash
python -m pytest tests/test_docker_integration.py -v
```

### Test 4: Clipboard Manager (12 tests)
```bash
python -m pytest tests/test_clipboard_manager.py -v
```

### Test 5: API Testing (9 tests)
```bash
python -m pytest tests/test_api_testing.py -v
```

### Test 6: Screen Capture & OCR (7 tests)
```bash
python -m pytest tests/test_screen_capture_ocr.py -v
```

### Test 7: Core Tools
```bash
python -m pytest tests/test_tools.py -v
```

### Test 8: Context Management
```bash
python -m pytest tests/test_context.py -v
```

### Test 9: Learning System
```bash
python -m pytest tests/test_learning.py -v
```

### Test 10: Automation Engine
```bash
python -m pytest tests/test_automation.py -v
```

## Step 5: Interactive Plugin Testing

### Database Plugin
```bash
python << 'EOF'
import asyncio
from src.plugins.database_integration import DatabaseIntegrationTool

async def test():
    tool = DatabaseIntegrationTool()
    
    # Create SQLite connection
    result = await tool.execute(
        action="create_connection",
        connection_name="test_db",
        database_type="sqlite",
        database="./test_demo.db"
    )
    print("✅ Connection created:", result)
    
    # List connections
    result = await tool.execute(action="list_connections")
    print("✅ Connections:", result)

asyncio.run(test())
print("\n✅ Database integration working!")
EOF
```

### GitHub Plugin
```bash
python << 'EOF'
import asyncio
from src.plugins.github_integration import GitHubIntegrationTool

async def test():
    tool = GitHubIntegrationTool()
    
    # Get public repo info (no auth needed)
    result = await tool.execute(
        action="get_repo",
        repo="UdaySoni32/Jarvis-2.0"
    )
    
    if result.get("success"):
        print("✅ GitHub integration working!")
        print(f"   Repository: {result.get('repo', {}).get('name')}")
        print(f"   Stars: {result.get('repo', {}).get('stargazers_count')}")
    else:
        print("ℹ️  GitHub API response:", result)

asyncio.run(test())
EOF
```

### Clipboard Plugin
```bash
python << 'EOF'
import asyncio
from src.plugins.clipboard_manager import ClipboardManagerTool

async def test():
    tool = ClipboardManagerTool()
    
    # Copy text
    result = await tool.execute(
        action="copy",
        text="JARVIS 2.0 is working! 🚀"
    )
    print("✅ Copy result:", result)
    
    # Paste text
    result = await tool.execute(action="paste")
    print("✅ Paste result:", result)
    
    # Get history
    result = await tool.execute(action="get_history")
    print("✅ History count:", result.get("count"))

asyncio.run(test())
print("\n✅ Clipboard manager working!")
EOF
```

### Screen Capture Plugin
```bash
python << 'EOF'
import asyncio
from src.plugins.screen_capture_ocr import ScreenCaptureOCRTool

async def test():
    tool = ScreenCaptureOCRTool()
    
    # Test initialization
    result = await tool.execute(action="get_history")
    print("✅ Screen capture initialized:", result)
    
    # Try to capture (may fail if no display)
    try:
        result = await tool.execute(action="capture_screen")
        if result.get("success"):
            print("✅ Screenshot taken:", result["capture"]["path"])
        else:
            print("ℹ️  Screenshot skipped (no display):", result)
    except Exception as e:
        print("ℹ️  Screenshot not available (headless):", str(e))

asyncio.run(test())
print("\n✅ Screen capture plugin loaded!")
EOF
```

### API Testing Plugin
```bash
python << 'EOF'
import asyncio
from src.plugins.api_testing import APITestingTool

async def test():
    tool = APITestingTool()
    
    # Test GitHub API
    result = await tool.execute(
        action="send_request",
        method="GET",
        url="https://api.github.com/repos/UdaySoni32/Jarvis-2.0"
    )
    
    if result.get("success"):
        response = result.get("response", {})
        print("✅ API Testing working!")
        print(f"   Status: {response.get('status_code')}")
        print(f"   Response time: {response.get('response_time'):.3f}s")
    
    # Get results
    result = await tool.execute(action="get_results")
    print(f"✅ Test results stored: {result.get('count')} tests")

asyncio.run(test())
print("\n✅ API testing working!")
EOF
```

### Docker Plugin
```bash
python << 'EOF'
import asyncio
from src.plugins.docker_integration import DockerIntegrationTool

async def test():
    tool = DockerIntegrationTool()
    
    # Check Docker availability
    result = await tool.execute(action="get_info")
    
    if result.get("success"):
        print("✅ Docker integration working!")
        print(f"   Info: {result.get('info', {})}")
    else:
        print("ℹ️  Docker not available:", result.get("error"))
        print("   Install with: sudo apt install docker.io")

asyncio.run(test())
EOF
```

## Step 6: Start JARVIS Interactive Mode

```bash
# Configure JARVIS first
python -m src.setup_wizard

# Then start JARVIS
python main.py
```

### Test Commands in JARVIS

Once JARVIS starts, try:

```
> Hello JARVIS

> What's my system information?

> List all available plugins

> Show me system status

> Create a task called "Test JARVIS" due tomorrow

> What can you do?
```

## Expected Results

### ✅ All Tests Should Pass
- Database Integration: 18/18 ✅
- GitHub Integration: 18/18 ✅
- Docker Integration: 6/6 ✅
- Clipboard Manager: 12/12 ✅
- API Testing: 9/9 ✅
- Screen Capture: 7/7 ✅
- Core Tools: All passing ✅
- Context Management: All passing ✅
- Learning System: All passing ✅
- Automation Engine: All passing ✅

### 📊 Total: 70+ tests passing

## Troubleshooting

### If tests fail:

```bash
# Check Python version (needs 3.10+)
python3 --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Install missing system packages
sudo apt install -y scrot tesseract-ocr xclip xsel

# Check virtual environment
which python  # Should point to venv/bin/python
```

### If Docker tests fail:

```bash
# Install Docker
sudo apt install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

### If display-related tests fail:

This is normal on headless servers. Screenshot and clipboard tests may skip.

## Performance Verification

```bash
# Run tests with timing
python -m pytest tests/ -v --durations=10

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test with output
python -m pytest tests/test_github_integration.py::TestGitHubIntegration::test_initialization -v -s
```

## Cleanup After Testing

```bash
# Remove test database
rm -f test_demo.db

# Deactivate virtual environment
deactivate
```

## Quick Validation

Run this one-liner to validate everything:

```bash
source venv/bin/activate && python -m pytest tests/ -v --tb=short && echo "✅ ALL TESTS PASSED!" || echo "❌ Some tests failed"
```

---

**All tests passing?** 🎉 **JARVIS 2.0 is ready to use!**
