# 🔌 JARVIS 2.0 - Plugin Development Guide

**Version**: 1.0 | **Audience**: Developers adding new tools/plugins

---

## Overview

JARVIS plugins are Python classes that:
1. Inherit from `BaseTool`
2. Declare their parameters via `get_parameters()`
3. Implement their logic in `async execute()`
4. Self-register by being added to `src/plugins/__init__.py`

The tool registry automatically generates OpenAI function-calling schemas from your plugin definition.

---

## Quick Start: Creating a Plugin

### 1. Create the file

```bash
touch src/plugins/my_tool.py
```

### 2. Implement the tool

```python
# src/plugins/my_tool.py
"""My custom JARVIS tool."""

from typing import Dict, Any

from core.tools.base import BaseTool, ToolParameter


class MyTool(BaseTool):
    """
    One-line description used by the LLM to decide when to call this tool.

    More detail can go here for maintainers, but the LLM uses the first line.
    """

    name = "mytool"           # Unique lowercase identifier
    description = "One-line description used by the LLM to decide when to call this tool."

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Declare accepted parameters."""
        return {
            "query": ToolParameter(
                name="query",
                type="string",
                description="The input query",
                required=True,
            ),
            "limit": ToolParameter(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=10,
            ),
        }

    async def execute(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Execute the tool.

        Returns a dict. Use {"error": "..."} for errors.
        """
        # Your logic here
        result = f"You searched for: {query}"
        return {"result": result, "count": 1}
```

### 3. Register the plugin

Add it to `src/plugins/__init__.py`:

```python
from .my_tool import MyTool   # add import

def register_all_plugins():
    plugins = [
        ...
        MyTool(),              # add instance
    ]
```

### 4. Test it

```bash
# Quick smoke test
python -c "
import asyncio, sys
sys.path.insert(0, 'src')
from plugins import register_all_plugins
from core.tools.registry import tool_registry
from core.tools.executor import tool_executor

async def main():
    result = await tool_executor.execute('mytool', {'query': 'hello'})
    print(result)

asyncio.run(main())
"
```

---

## BaseTool API Reference

```python
class BaseTool(ABC):
    name: str                                   # Unique tool name
    description: str                            # LLM-visible description

    @abstractmethod
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Return parameter definitions."""

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool. Return dict with results or {"error": ...}."""

    def to_openai_function(self) -> Dict:
        """Auto-generate OpenAI function calling schema."""
```

---

## ToolParameter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | ✅ | Parameter name (matches execute() kwarg) |
| `type` | str | ✅ | JSON type: `"string"`, `"integer"`, `"number"`, `"boolean"`, `"array"` |
| `description` | str | ✅ | LLM-visible description |
| `required` | bool | ✅ | Is this parameter mandatory? |
| `default` | Any | ❌ | Default value if not provided |
| `enum` | list | ❌ | Restrict to specific values |

---

## Best Practices

### Return structure
Always return a dict. For success:
```python
return {"result": data, "count": len(data)}
```
For errors:
```python
return {"error": "Description of what went wrong"}
```

### Guard optional dependencies
```python
try:
    import some_library
    LIBRARY_AVAILABLE = True
except ImportError:
    LIBRARY_AVAILABLE = False

async def execute(self, ...):
    if not LIBRARY_AVAILABLE:
        return {"error": "some_library not installed. Run: pip install some_library"}
```

### Async IO
All `execute()` methods are `async`. Use `await` for network/IO:
```python
import httpx

async def execute(self, url: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        return {"content": response.text}
```

### Logging
```python
from core.logger import logger

async def execute(self, ...):
    logger.debug(f"MyTool called with: {query}")
    ...
    logger.info("MyTool success")
```

---

## Writing Tests

Add your plugin tests to `tests/test_plugins.py` or create a new file:

```python
import asyncio
import pytest

def test_my_tool(tool_executor):
    result = asyncio.get_event_loop().run_until_complete(
        tool_executor.execute("mytool", {"query": "hello"})
    )
    assert result["success"]
    assert "result" in result["result"]
```

Run tests:
```bash
source venv/bin/activate
python -m pytest tests/test_core.py tests/test_plugins.py -v
```

---

## Existing Plugins (for reference)

| Plugin | File | Key pattern |
|--------|------|-------------|
| Calculator | `calculator.py` | Pure Python eval with safety |
| System Info | `system_info.py` | psutil for OS metrics |
| File Ops | `file_ops.py` | Path safety checks before reading |
| DateTime | `datetime_info.py` | Multiple output formats |
| Web Search | `web_search.py` | httpx async HTTP, DuckDuckGo |
| Weather | `weather.py` | External API with key check |
| Timer | `timer.py` | Background threading |
| Notes | `notes.py` | JSON file persistence |
| Process Manager | `process_manager.py` | psutil + safety blocklist |
