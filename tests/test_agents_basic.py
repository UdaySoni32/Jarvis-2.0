"""
Basic agent system tests - No LLM required.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.agents import (
    agent_coordinator,
    planning_agent,
    research_agent,
    code_agent,
    AgentStatus,
    AgentMessage
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
    assert any(a['name'] == 'PlanningAgent' for a in agents), "Should have PlanningAgent"
    assert any(a['name'] == 'ResearchAgent' for a in agents), "Should have ResearchAgent"
    assert any(a['name'] == 'CodeAgent' for a in agents), "Should have CodeAgent"
    print("✅ Agent registration test passed\n")


def test_agent_retrieval():
    """Test getting agents by name."""
    print("Testing agent retrieval...")
    
    planning = agent_coordinator.get_agent("PlanningAgent")
    assert planning is not None, "Should retrieve PlanningAgent"
    assert planning.name == "PlanningAgent"
    print(f"✅ Retrieved PlanningAgent")
    
    research = agent_coordinator.get_agent("ResearchAgent")
    assert research is not None, "Should retrieve ResearchAgent"
    print(f"✅ Retrieved ResearchAgent")
    
    code = agent_coordinator.get_agent("CodeAgent")
    assert code is not None, "Should retrieve CodeAgent"
    print(f"✅ Retrieved CodeAgent")
    
    none_agent = agent_coordinator.get_agent("NonExistent")
    assert none_agent is None, "Should return None for non-existent agent"
    print(f"✅ Returns None for non-existent agent")
    
    print("✅ Agent retrieval test passed\n")


def test_planning_agent_capability():
    """Test planning agent can identify planning tasks."""
    print("Testing planning agent capabilities...")
    
    planning_tasks = [
        "Create a plan to build a web application",
        "How to implement a feature",
        "Design a system architecture",
        "Steps to deploy the app",
        "Plan out the project structure"
    ]
    
    non_planning_tasks = [
        "What is Python?",
        "Search for information about AI",
        "Write a function"
    ]
    
    for task in planning_tasks:
        result = planning_agent.can_handle(task)
        assert result, f"Should handle: {task}"
        print(f"✅ Can handle: {task[:50]}...")
    
    print(f"✅ Correctly identifies {len(planning_tasks)} planning tasks")
    print("✅ Planning agent capability test passed\n")


def test_research_agent_capability():
    """Test research agent can identify research tasks."""
    print("Testing research agent capabilities...")
    
    research_tasks = [
        "Research machine learning",
        "Find information about Python",
        "What is quantum computing?",
        "Tell me about neural networks",
        "Search for recent AI developments",
        "Look up best practices for testing"
    ]
    
    for task in research_tasks:
        result = research_agent.can_handle(task)
        assert result, f"Should handle: {task}"
        print(f"✅ Can handle: {task[:50]}...")
    
    print(f"✅ Correctly identifies {len(research_tasks)} research tasks")
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
        "Fix the error in my code",
        "Refactor this class",
        "Optimize this algorithm"
    ]
    
    for task in code_tasks:
        result = code_agent.can_handle(task)
        assert result, f"Should handle: {task}"
        print(f"✅ Can handle: {task[:50]}...")
    
    print(f"✅ Correctly identifies {len(code_tasks)} code tasks")
    print("✅ Code agent capability test passed\n")


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
        assert "tasks_completed" in status, "Should have tasks_completed"
        assert status['status'] == 'idle', "Should be idle"
    
    print("✅ Agent status test passed\n")


def test_agent_capabilities():
    """Test agent capabilities listing."""
    print("Testing agent capabilities...")
    
    planning_caps = planning_agent.get_capabilities()
    assert len(planning_caps) > 0, "Should have capabilities"
    assert "Task decomposition" in planning_caps
    print(f"✅ PlanningAgent: {len(planning_caps)} capabilities")
    
    research_caps = research_agent.get_capabilities()
    assert len(research_caps) > 0, "Should have capabilities"
    assert "Web search and information gathering" in research_caps
    print(f"✅ ResearchAgent: {len(research_caps)} capabilities")
    
    code_caps = code_agent.get_capabilities()
    assert len(code_caps) > 0, "Should have capabilities"
    assert "Code generation" in code_caps
    print(f"✅ CodeAgent: {len(code_caps)} capabilities")
    
    print("✅ Agent capabilities test passed\n")


def test_agent_messaging():
    """Test agent messaging system."""
    print("Testing agent messaging...")
    
    # Create a message
    msg = AgentMessage(
        sender="TestSender",
        recipient="TestRecipient",
        content="Test message",
        message_type="info"
    )
    
    assert msg.sender == "TestSender"
    assert msg.recipient == "TestRecipient"
    assert msg.content == "Test message"
    assert msg.message_type == "info"
    print("✅ AgentMessage created successfully")
    
    # Convert to dict
    msg_dict = msg.to_dict()
    assert "sender" in msg_dict
    assert "content" in msg_dict
    assert "timestamp" in msg_dict
    print("✅ AgentMessage converts to dict")
    
    # Test message receiving
    planning_agent.receive_message(msg)
    assert len(planning_agent.message_queue) > 0
    print("✅ Agent can receive messages")
    
    print("✅ Agent messaging test passed\n")


def test_agent_task_history():
    """Test agent task history."""
    print("Testing agent task history...")
    
    # Clear history
    planning_agent.task_history = []
    
    # Add a task
    task = "Test task"
    result = {"success": True, "data": "test"}
    planning_agent.add_to_history(task, result)
    
    assert len(planning_agent.task_history) == 1
    assert planning_agent.task_history[0]["task"] == task
    assert planning_agent.task_history[0]["agent"] == "PlanningAgent"
    print("✅ Task added to history")
    
    # Check status reflects history
    status = planning_agent.get_status()
    assert status["tasks_completed"] == 1
    print("✅ Status reflects task history")
    
    print("✅ Agent task history test passed\n")


def test_code_agent_language_support():
    """Test code agent supported languages."""
    print("Testing code agent language support...")
    
    languages = code_agent.supported_languages
    assert len(languages) > 0, "Should support multiple languages"
    assert "python" in languages
    assert "javascript" in languages
    print(f"✅ CodeAgent supports {len(languages)} languages")
    print(f"  Languages: {', '.join(languages[:5])}...")
    
    print("✅ Code agent language support test passed\n")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("AGENT SYSTEM BASIC TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_agent_registration()
        test_agent_retrieval()
        test_planning_agent_capability()
        test_research_agent_capability()
        test_code_agent_capability()
        test_agent_status()
        test_agent_capabilities()
        test_agent_messaging()
        test_agent_task_history()
        test_code_agent_language_support()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Note: These tests cover the agent framework structure.")
        print("Full agent execution tests require a working LLM connection.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
