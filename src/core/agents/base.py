"""
Base agent framework for JARVIS 2.0.

Provides abstract base class for specialized agents that can perform
complex, multi-step tasks autonomously.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from enum import Enum

from ..logger import logger
from ..llm.manager import llm_manager
from ..memory.semantic import semantic_memory
from ..tools.registry import tool_registry


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETE = "complete"
    FAILED = "failed"


class AgentMessage:
    """Message for agent communication."""
    
    def __init__(
        self,
        sender: str,
        recipient: str,
        content: str,
        message_type: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.message_type = message_type  # info, request, response, error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "type": self.message_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Agents are specialized AI components that can:
    - Perform complex, multi-step tasks
    - Use tools autonomously
    - Communicate with other agents
    - Learn from experience
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize agent.
        
        Args:
            name: Agent name
            description: Agent description/purpose
        """
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.llm = llm_manager
        self.memory = semantic_memory
        self.tools = tool_registry
        self.message_queue: List[AgentMessage] = []
        self.task_history: List[Dict[str, Any]] = []
        
        logger.info(f"Agent initialized: {name}")
    
    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            task: Task description
            context: Optional context information
            
        Returns:
            Dictionary with results
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: str) -> bool:
        """
        Check if agent can handle a task.
        
        Args:
            task: Task description
            
        Returns:
            True if agent can handle this task
        """
        pass
    
    async def think(self, prompt: str) -> str:
        """
        Use LLM to think/reason about something.
        
        Args:
            prompt: Thinking prompt
            
        Returns:
            LLM response
        """
        self.status = AgentStatus.THINKING
        try:
            response = await self.llm.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"Agent {self.name} thinking error: {e}")
            return ""
        finally:
            self.status = AgentStatus.IDLE
    
    async def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Use a tool.
        
        Args:
            tool_name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        self.status = AgentStatus.EXECUTING
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                return {"success": False, "error": f"Tool not found: {tool_name}"}
            
            result = await tool.execute(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Agent {self.name} tool error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.status = AgentStatus.IDLE
    
    def send_message(self, recipient: str, content: str, message_type: str = "info"):
        """
        Send message to another agent.
        
        Args:
            recipient: Recipient agent name
            content: Message content
            message_type: Message type
        """
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            content=content,
            message_type=message_type
        )
        # In a full implementation, this would route to the recipient
        logger.debug(f"Agent {self.name} → {recipient}: {content[:50]}...")
    
    def receive_message(self, message: AgentMessage):
        """
        Receive a message.
        
        Args:
            message: Incoming message
        """
        self.message_queue.append(message)
        logger.debug(f"Agent {self.name} received message from {message.sender}")
    
    def add_to_history(self, task: str, result: Dict[str, Any]):
        """
        Add task to history.
        
        Args:
            task: Task description
            result: Task result
        """
        self.task_history.append({
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "agent": self.name
        })
    
    def get_capabilities(self) -> List[str]:
        """
        Get agent capabilities.
        
        Returns:
            List of capabilities
        """
        return [
            "Execute complex tasks",
            "Use tools autonomously",
            "Learn from experience",
            "Communicate with other agents"
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status.
        
        Returns:
            Status dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "tasks_completed": len(self.task_history),
            "messages_pending": len(self.message_queue)
        }


class AgentCoordinator:
    """
    Coordinates multiple agents.
    
    Routes tasks to appropriate agents and manages agent communication.
    """
    
    def __init__(self):
        """Initialize coordinator."""
        self.agents: Dict[str, BaseAgent] = {}
        logger.info("Agent coordinator initialized")
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.name] = agent
        logger.info(f"Agent registered: {agent.name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(name)
    
    async def delegate_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Delegate task to appropriate agent.
        
        Args:
            task: Task description
            context: Optional context
            
        Returns:
            Task result
        """
        # Find capable agent
        for agent in self.agents.values():
            if agent.can_handle(task):
                logger.info(f"Delegating task to {agent.name}: {task[:50]}...")
                result = await agent.execute(task, context)
                return result
        
        return {
            "success": False,
            "error": "No agent found to handle this task"
        }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents.
        
        Returns:
            List of agent info
        """
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "status": agent.status.value,
                "capabilities": agent.get_capabilities()
            }
            for agent in self.agents.values()
        ]


# Global coordinator instance
agent_coordinator = AgentCoordinator()
