# 🤝 Contributing to JARVIS 2.0

Thank you for your interest in contributing to JARVIS 2.0! This guide will help you get started.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Adding a New Tool](#adding-a-new-tool)
4. [Code Style](#code-style)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)

---

## Getting Started

### Prerequisites

- Python 3.14+ (or 3.11+)
- Git
- Virtual environment
- Basic understanding of async Python

### Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0

# Add upstream remote
git remote add upstream https://github.com/UdaySoni32/Jarvis-2.0.git
```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
```

### 2. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

### 3. Setup Configuration

```bash
# Copy example config
cp .env.example .env

# Edit with your API keys
nano .env
```

### 4. Run Tests

```bash
# Make sure everything works
python tests/test_integration.py
```

---

## Adding a New Tool

Tools (plugins) are the easiest way to extend JARVIS! Here's how:

### Step 1: Create Tool File

Create a new file in `src/plugins/`:

```python
# src/plugins/my_awesome_tool.py

from core.tools.base import BaseTool, ToolParameter
from typing import Dict, Any

class MyAwesomeTool(BaseTool):
    """
    A tool that does something awesome.
    
    This description will be shown to the LLM so it knows when to use your tool.
    Be specific about what it does!
    """
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Define the parameters your tool accepts."""
        return {
            "input_text": ToolParameter(
                name="input_text",
                type="string",
                description="The text to process",
                required=True
            ),
            "mode": ToolParameter(
                name="mode",
                type="string",
                description="Processing mode: 'uppercase' or 'lowercase'",
                required=False
            )
        }
    
    async def execute(self, input_text: str, mode: str = "uppercase") -> Dict[str, Any]:
        """
        Execute the tool logic.
        
        Args:
            input_text: The text to process
            mode: Processing mode
            
        Returns:
            Dictionary with results
        """
        try:
            if mode == "uppercase":
                result = input_text.upper()
            elif mode == "lowercase":
                result = input_text.lower()
            else:
                return {
                    "success": False,
                    "error": f"Unknown mode: {mode}"
                }
            
            return {
                "success": True,
                "result": result,
                "original": input_text,
                "mode": mode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### Step 2: Register the Tool

Add it to `src/plugins/__init__.py`:

```python
# src/plugins/__init__.py

from .my_awesome_tool import MyAwesomeTool  # Add this import

def register_all_plugins(registry):
    """Register all available plugins."""
    from .calculator import CalculatorTool
    from .system_info import SystemInfoTool
    # ... other imports ...
    
    # Register existing tools
    registry.register(CalculatorTool())
    registry.register(SystemInfoTool())
    # ... other registrations ...
    
    # Register your new tool
    registry.register(MyAwesomeTool())  # Add this line
```

### Step 3: Test Your Tool

Create a test file `tests/test_my_tool.py`:

```python
import asyncio
from src.plugins.my_awesome_tool import MyAwesomeTool

async def test_my_tool():
    """Test the new tool."""
    tool = MyAwesomeTool()
    
    # Test uppercase
    result = await tool.execute("hello world", mode="uppercase")
    assert result["success"] is True
    assert result["result"] == "HELLO WORLD"
    print("✓ Uppercase test passed")
    
    # Test lowercase
    result = await tool.execute("HELLO WORLD", mode="lowercase")
    assert result["success"] is True
    assert result["result"] == "hello world"
    print("✓ Lowercase test passed")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_my_tool())
```

Run the test:

```bash
python tests/test_my_tool.py
```

### Step 4: Try It in JARVIS

```bash
python -m src.cli

# Then in JARVIS:
❯ Convert "hello world" to uppercase
🔧 Using tool: myawesometool(input_text="hello world", mode="uppercase")
JARVIS: The result is "HELLO WORLD"!
```

---

## Code Style

### Python Guidelines

- **Python 3.14+** features
- **Type hints** for all functions
- **Async/await** for I/O operations
- **Docstrings** for classes and methods
- **Error handling** with try/except

### Example

```python
async def my_function(param: str, count: int = 1) -> Dict[str, Any]:
    """
    Brief description of what this does.
    
    Args:
        param: Description of param
        count: Description of count
        
    Returns:
        Dictionary with results
        
    Raises:
        ValueError: When param is invalid
    """
    try:
        # Your logic here
        result = param * count
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `MyAwesomeTool`)
- **Functions**: `snake_case` (e.g., `get_parameters`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private**: `_leading_underscore` (e.g., `_internal_method`)

---

## Testing

### Run All Tests

```bash
# Test function calling system
python tests/test_function_calling.py

# Test memory system
python tests/test_memory.py

# Test all plugins
python tests/test_plugins.py

# Integration test (full workflow)
python tests/test_integration.py
```

### Write Tests for New Features

Every new tool should have tests:

```python
async def test_your_tool():
    """Test your new tool."""
    tool = YourTool()
    
    # Test basic functionality
    result = await tool.execute(param="test")
    assert result["success"] is True
    
    # Test error cases
    result = await tool.execute(param="")
    assert result["success"] is False
    
    print("✅ All tests passed!")
```

---

## Submitting Changes

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-awesome-tool
```

### 2. Make Changes

- Write your code
- Add tests
- Update documentation if needed

### 3. Test Everything

```bash
# Run all tests
python tests/test_integration.py

# Make sure nothing is broken
python -m src.cli
# Try your new feature manually
```

### 4. Commit Changes

```bash
# Add files
git add src/plugins/my_awesome_tool.py
git add tests/test_my_tool.py
git add src/plugins/__init__.py

# Commit with descriptive message
git commit -m "Add MyAwesomeTool for text processing

- Implements uppercase/lowercase conversion
- Includes comprehensive tests
- Updates plugin registry

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### 5. Push to Your Fork

```bash
git push origin feature/my-awesome-tool
```

### 6. Create Pull Request

1. Go to GitHub
2. Click "New Pull Request"
3. Describe your changes
4. Reference any related issues
5. Submit!

---

## Ideas for Contributions

### Easy (Good First Issues)

- Add new simple tools (URL shortener, QR code generator, etc.)
- Improve error messages
- Add more tests
- Fix typos in documentation
- Add examples to SETUP.md

### Medium

- Add new LLM provider (Claude, Gemini, etc.)
- Implement conversation export
- Add tool categories/tags
- Improve memory search
- Add rate limiting

### Hard

- Implement Phase 2 features (vector database)
- Add multi-agent system
- Build web interface (Phase 3)
- Add voice I/O (Phase 5)
- Implement plugins marketplace

---

## Thank You!

Every contribution, no matter how small, is appreciated! 🙏

Together we're building something awesome! 🚀

---

*Questions? Open an issue on GitHub!*
