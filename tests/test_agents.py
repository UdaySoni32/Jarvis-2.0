"""
Test suite for agent system.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.agents import (
    agent_coordinator,
    planning_agent,
    research_agent,
    code_agent,
    AgentStatus
)


def test_agent_registration():
    """Test that all agents are registered."""
    print("Testing agent registration...")
    
    agents = agent_coordinator.list_agents()
    print(f"✅ Found {len(agents)} registered agents")
    
    for agent_info in agents:
        print(f"  - {agent_info['name']}: {agent_info['description']}")
        print(f"    Status: {agent_info['status']}")
        print(f"    Capabilities: {len(agent_info['capabilities'])}")
    
    assert len(agents) == 3, "Should have 3 agents registered"
    print("✅ Agent registration test passed\n")


def test_planning_agent_capability():
    """Test planning agent can identify planning tasks."""
    print("Testing planning agent capabilities...")
    
    planning_tasks = [
        "Create a plan to build a web application",
        "How to implement a feature",
        "Design a system architecture",
        "Steps to deploy the app"
    ]
    
    non_planning_tasks = [
        "What is Python?",
        "Search for information about AI"
    ]
    
    for task in planning_tasks:
        assert planning_agent.can_handle(task), f"Should handle: {task}"
        print(f"✅ Can handle: {task}")
    
    for task in non_planning_tasks:
        if planning_agent.can_handle(task):
            print(f"⚠️  Unexpectedly handles: {task}")
    
    print("✅ Planning agent capability test passed\n")


def test_research_agent_capability():
    """Test research agent can identify research tasks."""
    print("Testing research agent capabilities...")
    
    research_tasks = [
        "Research machine learning",
        "Find information about Python",
        "What is quantum computing?",
        "Tell me about neural networks",
        "Search for recent AI developments"
    ]
    
    for task in research_tasks:
        assert research_agent.can_handle(task), f"Should handle: {task}"
        print(f"✅ Can handle: {task}")
    
    print("✅ Research agent capability test passed\n")


def test_code_agent_capability():
    """Test code agent can identify code tasks."""
    print("Testing code agent capabilities...")
    
    code_tasks = [
        "Write a Python function to sort a list",
        "Debug this code",
        "Implement a binary search algorithm",
        "Review this JavaScript code",
        "Explain this function",
        "Fix the error in my code"
    ]
    
    for task in code_tasks:
        assert code_agent.can_handle(task), f"Should handle: {task}"
        print(f"✅ Can handle: {task}")
    
    print("✅ Code agent capability test passed\n")


async def test_planning_agent_execution():
    """Test planning agent execution."""
    print("Testing planning agent execution...")
    
    task = "Create a plan to build a simple todo application"
    result = await planning_agent.execute(task)
    
    assert result["success"], "Execution should succeed"
    assert "plan" in result, "Should return a plan"
    assert result["steps_count"] > 0, "Plan should have steps"
    
    plan = result["plan"]
    print(f"✅ Generated plan with {plan['total_steps']} steps")
    print(f"  Task: {plan['task']}")
    
    # Print first 3 steps
    for step in plan["steps"][:3]:
        print(f"  {step['number']}. {step['description'][:60]}...")
    
    # Test plan summary
    summary = planning_agent.get_plan_summary()
    assert summary["active"], "Plan should be active"
    assert summary["total_steps"] == plan["total_steps"], "Step count should match"
    
    print("✅ Planning agent execution test passed\n")


async def test_research_agent_execution():
    """Test research agent execution."""
    print("Testing research agent execution...")
    
    task = "What is artificial intelligence?"
    result = await research_agent.execute(task)
    
    assert result["success"], "Execution should succeed"
    assert "findings" in result, "Should return findings"
    assert "topic" in result, "Should identify topic"
    
    findings = result["findings"]
    print(f"✅ Research completed on: {result['topic']}")
    print(f"  Sources used: {findings.get('sources', [])}")
    print(f"  Confidence: {findings.get('confidence', 'unknown')}")
    
    if "key_points" in findings:
        print(f"  Key points found: {len(findings['key_points'])}")
    
    print("✅ Research agent execution test passed\n")


async def test_code_agent_execution():
    """Test code agent execution."""
    print("Testing code agent execution...")
    
    task = "Write a Python function to calculate factorial"
    result = await code_agent.execute(task, {"language": "python"})
    
    assert result["success"], "Execution should succeed"
    assert "result" in result, "Should return result"
    assert result["task_type"] == "generate", "Should be generation task"
    
    code_result = result["result"]
    print(f"✅ Generated {code_result['language']} code")
    print(f"  Type: {code_result['type']}")
    print(f"  Code length: {len(code_result['code'])} characters")
    
    # Show first few lines of generated code
    code_lines = code_result["code"].split('\n')[:5]
    print("  Preview:")
    for line in code_lines:
        print(f"    {line}")
    
    print("✅ Code agent execution test passed\n")


async def test_task_delegation():
    """Test agent coordinator task delegation."""
    print("Testing task delegation...")
    
    tasks = [
        ("Create a plan for building a website", "PlanningAgent"),
        ("Research Python frameworks", "ResearchAgent"),
        ("Write a function to parse JSON", "CodeAgent")
    ]
    
    for task, expected_agent in tasks:
        result = await agent_coordinator.delegate_task(task)
        print(f"✅ Task: '{task[:40]}...'")
        print(f"  Handled by: {result.get('agent', 'unknown')}")
        assert result.get("agent") == expected_agent, f"Should be handled by {expected_agent}"
    
    print("✅ Task delegation test passed\n")


def test_agent_status():
    """Test agent status reporting."""
    print("Testing agent status...")
    
    agents = [planning_agent, research_agent, code_agent]
    
    for agent in agents:
        status = agent.get_status()
        print(f"✅ {status['name']}")
        print(f"  Status: {status['status']}")
        print(f"  Tasks completed: {status['tasks_completed']}")
        print(f"  Messages pending: {status['messages_pending']}")
        
        assert "name" in status, "Should have name"
        assert "status" in status, "Should have status"
    
    print("✅ Agent status test passed\n")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("AGENT SYSTEM TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        # Synchronous tests
        test_agent_registration()
        test_planning_agent_capability()
        test_research_agent_capability()
        test_code_agent_capability()
        
        # Asynchronous tests
        await test_planning_agent_execution()
        await test_research_agent_execution()
        await test_code_agent_execution()
        await test_task_delegation()
        
        # Status tests
        test_agent_status()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
