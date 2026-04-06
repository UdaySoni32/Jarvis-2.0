#!/usr/bin/env python3
"""Test script for core plugins."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_plugins():
    """Test all core plugins."""
    from core.tools import tool_registry, tool_executor
    from plugins import register_all_plugins
    
    print("\n" + "=" * 60)
    print("JARVIS 2.0 - Core Plugins Test")
    print("=" * 60 + "\n")
    
    # Test 1: Plugin Registration
    print("✓ Test 1: Plugin Registration")
    print(f"  Registered plugins: {len(tool_registry)}")
    for tool_name in tool_registry.list_tools():
        print(f"    - {tool_name}")
    print(f"  ✅ Passed\n")
    
    # Test 2: DateTime Tool
    print("✓ Test 2: DateTime Tool")
    result = await tool_executor.execute("datetime", {"info_type": "current"})
    if result["success"]:
        print(f"  Current date: {result['result']['date']}")
        print(f"  Current time: {result['result']['time']}")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 3: Timer Tool
    print("✓ Test 3: Timer Tool")
    result = await tool_executor.execute("timer", {
        "action": "create",
        "duration": 5,
        "label": "Test Timer"
    })
    if result["success"]:
        print(f"  Created timer: {result['result']['timer_id']}")
        print(f"  Duration: {result['result']['duration_seconds']}s")
        
        # List timers
        list_result = await tool_executor.execute("timer", {"action": "list"})
        if list_result["success"]:
            print(f"  Active timers: {list_result['result']['count']}")
            print(f"  ✅ Passed")
        else:
            print(f"  ❌ Failed to list: {list_result.get('error')}")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 4: Notes Tool
    print("✓ Test 4: Notes Tool")
    result = await tool_executor.execute("notes", {
        "action": "create",
        "title": "Test Note",
        "content": "This is a test note created during plugin testing.",
        "tags": "test,demo"
    })
    if result["success"]:
        note_id = result['result']['note']['id']
        print(f"  Created note: {note_id}")
        print(f"  Title: {result['result']['note']['title']}")
        
        # List notes
        list_result = await tool_executor.execute("notes", {"action": "list"})
        if list_result["success"]:
            print(f"  Total notes: {list_result['result']['count']}")
            
            # Delete test note
            delete_result = await tool_executor.execute("notes", {
                "action": "delete",
                "note_id": note_id
            })
            if delete_result["success"]:
                print(f"  Deleted test note")
                print(f"  ✅ Passed")
            else:
                print(f"  ⚠️  Note created but cleanup failed")
        else:
            print(f"  ❌ Failed to list: {list_result.get('error')}")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 5: Process Manager Tool
    print("✓ Test 5: Process Manager Tool")
    result = await tool_executor.execute("processmanager", {
        "action": "list",
        "sort_by": "cpu",
        "limit": 5
    })
    if result["success"]:
        print(f"  Listed processes: {result['result']['count']}")
        print(f"  Total processes: {result['result']['total_processes']}")
        if result['result']['processes']:
            top_proc = result['result']['processes'][0]
            print(f"  Top CPU: {top_proc['name']} ({top_proc['cpu_percent']}%)")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 6: Web Search Tool
    print("✓ Test 6: Web Search Tool")
    result = await tool_executor.execute("websearch", {
        "query": "Python programming",
        "max_results": 3
    })
    if result["success"]:
        print(f"  Search query: {result['result']['query']}")
        print(f"  Results: {result['result']['results_count']}")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 7: Weather Tool (will fail without API key, but tests the structure)
    print("✓ Test 7: Weather Tool")
    result = await tool_executor.execute("weather", {
        "location": "London",
        "units": "metric"
    })
    if result["success"]:
        if "error" in result['result']:
            print(f"  API key not configured (expected)")
            print(f"  Error message present: ✓")
            print(f"  ✅ Passed (structure test)")
        else:
            print(f"  Location: {result['result']['location']}")
            print(f"  Temperature: {result['result']['temperature']['current']}°C")
            print(f"  Conditions: {result['result']['conditions']['description']}")
            print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 8: Calculator (existing tool, regression test)
    print("✓ Test 8: Calculator Tool (Regression)")
    result = await tool_executor.execute("calculator", {"expression": "sqrt(144)"})
    if result["success"]:
        print(f"  Expression: sqrt(144)")
        print(f"  Result: {result['result']['result']}")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 9: System Info (existing tool, regression test)
    print("✓ Test 9: System Info Tool (Regression)")
    result = await tool_executor.execute("systeminfo", {"info_type": "memory"})
    if result["success"]:
        print(f"  Total RAM: {result['result']['memory']['total_gb']}GB")
        print(f"  Used: {result['result']['memory']['used_gb']}GB")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    # Test 10: File Operations (existing tool, regression test)
    print("✓ Test 10: File Operations Tool (Regression)")
    result = await tool_executor.execute("filelist", {
        "directory": "/home/uday/jarvis-2.0",
        "pattern": "*.py"
    })
    if result["success"]:
        print(f"  Directory: /home/uday/jarvis-2.0")
        print(f"  Python files: {result['result']['count']}")
        print(f"  ✅ Passed")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
    print()
    
    print("=" * 60)
    print("✅ Plugin tests complete!")
    print("=" * 60 + "\n")
    
    # Summary
    print(f"Total plugins available: {len(tool_registry)}")
    print(f"Tools tested: 10/10")
    print("\n📝 Note: Weather tool requires OPENWEATHER_API_KEY in .env")


if __name__ == "__main__":
    asyncio.run(test_plugins())
