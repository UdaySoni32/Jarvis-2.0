"""
Planning Agent - Decomposes complex tasks into actionable steps.
"""

from typing import Dict, List, Any, Optional
import re

from .base import BaseAgent, AgentStatus
from ..logger import logger


class PlanningAgent(BaseAgent):
    """
    Agent specialized in task planning and decomposition.
    
    Capabilities:
    - Break down complex tasks into steps
    - Create actionable plans
    - Track goal progress
    - Adjust plans based on feedback
    """
    
    def __init__(self):
        super().__init__(
            name="PlanningAgent",
            description="Plans and decomposes complex tasks into actionable steps"
        )
        self.current_plan: Optional[Dict[str, Any]] = None
    
    def can_handle(self, task: str) -> bool:
        """Check if task requires planning."""
        planning_keywords = [
            "plan", "steps", "how to", "create", "build",
            "implement", "design", "organize", "strategy"
        ]
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in planning_keywords)
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a plan for the given task.
        
        Args:
            task: Task to plan
            context: Optional context
            
        Returns:
            Dictionary with plan
        """
        try:
            logger.info(f"PlanningAgent: Creating plan for '{task[:50]}...'")
            
            # Use LLM to generate plan
            planning_prompt = f"""You are a planning expert. Break down this task into clear, actionable steps:

Task: {task}

Provide a detailed plan with numbered steps. Each step should be specific and actionable.
Format:
1. [Step description]
2. [Step description]
...

Plan:"""
            
            plan_text = await self.think(planning_prompt)
            
            # Parse the plan into structured format
            plan = self._parse_plan(plan_text)
            plan["task"] = task
            plan["status"] = "created"
            
            self.current_plan = plan
            self.add_to_history(task, plan)
            
            return {
                "success": True,
                "plan": plan,
                "steps_count": len(plan["steps"]),
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"PlanningAgent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """
        Parse plan text into structured format.
        
        Args:
            plan_text: Raw plan text
            
        Returns:
            Structured plan
        """
        steps = []
        
        # Extract numbered steps
        lines = plan_text.split('\n')
        for line in lines:
            line = line.strip()
            # Match patterns like "1.", "1)", "Step 1:", etc.
            match = re.match(r'^(\d+)[\.):\s]+(.+)$', line)
            if match:
                step_num = int(match.group(1))
                step_desc = match.group(2).strip()
                steps.append({
                    "number": step_num,
                    "description": step_desc,
                    "status": "pending",
                    "result": None
                })
        
        return {
            "steps": steps,
            "total_steps": len(steps),
            "completed_steps": 0,
            "current_step": 1 if steps else 0
        }
    
    def mark_step_complete(self, step_number: int, result: str = ""):
        """
        Mark a step as complete.
        
        Args:
            step_number: Step number
            result: Step result
        """
        if not self.current_plan:
            return
        
        for step in self.current_plan["steps"]:
            if step["number"] == step_number:
                step["status"] = "complete"
                step["result"] = result
                self.current_plan["completed_steps"] += 1
                
                # Update current step
                next_pending = self._get_next_pending_step()
                if next_pending:
                    self.current_plan["current_step"] = next_pending["number"]
                else:
                    self.current_plan["status"] = "complete"
                
                break
    
    def _get_next_pending_step(self) -> Optional[Dict[str, Any]]:
        """Get next pending step."""
        if not self.current_plan:
            return None
        
        for step in self.current_plan["steps"]:
            if step["status"] == "pending":
                return step
        return None
    
    def get_plan_summary(self) -> Dict[str, Any]:
        """Get current plan summary."""
        if not self.current_plan:
            return {"active": False}
        
        return {
            "active": True,
            "task": self.current_plan.get("task", ""),
            "total_steps": self.current_plan["total_steps"],
            "completed_steps": self.current_plan["completed_steps"],
            "current_step": self.current_plan["current_step"],
            "status": self.current_plan.get("status", "in_progress"),
            "progress": (self.current_plan["completed_steps"] / 
                        self.current_plan["total_steps"] * 100 
                        if self.current_plan["total_steps"] > 0 else 0)
        }
    
    def get_capabilities(self) -> List[str]:
        """Get planning agent capabilities."""
        return super().get_capabilities() + [
            "Task decomposition",
            "Step-by-step planning",
            "Goal tracking",
            "Progress monitoring"
        ]


# Create global instance
planning_agent = PlanningAgent()
