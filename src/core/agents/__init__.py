"""
Agent system for JARVIS 2.0.

Provides specialized AI agents for complex tasks.
"""

from .base import (
    BaseAgent,
    AgentStatus,
    AgentMessage,
    AgentCoordinator,
    agent_coordinator
)
from .planning import PlanningAgent, planning_agent
from .research import ResearchAgent, research_agent
from .code import CodeAgent, code_agent

# Register all agents with the coordinator
agent_coordinator.register_agent(planning_agent)
agent_coordinator.register_agent(research_agent)
agent_coordinator.register_agent(code_agent)

__all__ = [
    "BaseAgent",
    "AgentStatus",
    "AgentMessage",
    "AgentCoordinator",
    "agent_coordinator",
    "PlanningAgent",
    "planning_agent",
    "ResearchAgent",
    "research_agent",
    "CodeAgent",
    "code_agent",
]
