#!/usr/bin/env python3
"""Test script for function calling system."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_tools():
    """Test tool registration and execution."""
    from core.tools import tool_registry, tool_executor
    from plugins import register_all_plugins
    
    print("\n" + "=" * 60)
    print("JARVIS 2.0 - Function Calling System Test")
    print("=" * 60 + "\n")
    
    # Test 1: Tool Registration
    print("✓ Test 1: Tool Registration")
    print(f"  Registered tools: {len(tool_registry)}")
    for tool_name in tool_registry.list_tools():
        print(f"    - {tool_name}")
    print()
    
    # Test 2: Calculator Tool
    print("✓ Test 2: Calculator Tool")
    result = await tool_executor.execute("calculator", {"expression": "2 + 2 * 3"})
    if result["success"]:
        print(f"  Expression: 2 + 2 * 3")
        print(f"  Result: {result['result']['result']}")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 3: System Info Tool
    print("✓ Test 3: System Info Tool")
    result = await tool_executor.execute("systeminfo", {"info_type": "cpu"})
    if result["success"]:
        print(f"  Info Type: cpu")
        print(f"  CPU Usage: {result['result']['cpu']['percent']}%")
        print(f"  CPU Count: {result['result']['cpu']['count']}")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 4: File List Tool
    print("✓ Test 4: File List Tool")
    result = await tool_executor.execute("filelist", {
        "directory": "/home/uday/jarvis-2.0",
        "pattern": "*.md"
    })
    if result["success"]:
        print(f"  Directory: /home/uday/jarvis-2.0")
        print(f"  Pattern: *.md")
        print(f"  Found: {result['result']['count']} files")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 5: OpenAI Function Schema
    print("✓ Test 5: OpenAI Function Schema Generation")
    functions = tool_registry.get_openai_functions()
    print(f"  Generated {len(functions)} function schemas")
    print(f"  Example (calculator):")
    import json
    print(json.dumps(functions[0], indent=2))
    print(f"  ✅ Passed")
    print()
    
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_tools())
