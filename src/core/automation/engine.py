"""
Automation engine for JARVIS 2.0.

Executes automation rules and manages their lifecycle.
"""

import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from ..logger import logger
from .schemas import (
    AutomationRule,
    Action,
    ActionType,
    AutomationRun,
    AutomationStatus
)
from .scheduler import automation_scheduler


class AutomationEngine:
    """
    Core automation engine.
    
    Executes automation rules and manages their state.
    """
    
    def __init__(self):
        """Initialize automation engine."""
        self.rules: Dict[str, AutomationRule] = {}
        self.runs: List[AutomationRun] = []
        self.running = False
        logger.info("Automation engine initialized")
    
    async def start(self):
        """Start the automation engine."""
        if not self.running:
            automation_scheduler.start()
            self.running = True
            logger.info("Automation engine started")
    
    async def stop(self):
        """Stop the automation engine."""
        if self.running:
            automation_scheduler.shutdown()
            self.running = False
            logger.info("Automation engine stopped")
    
    async def add_rule(self, rule: AutomationRule) -> bool:
        """
        Add an automation rule.
        
        Args:
            rule: Automation rule to add
            
        Returns:
            True if added successfully
        """
        try:
            # Store rule
            self.rules[rule.id] = rule
            
            # Add to scheduler if it's a schedule trigger
            if rule.trigger.trigger_type.value == "schedule":
                callback = lambda: asyncio.create_task(self.execute_rule(rule.id))
                success = automation_scheduler.add_rule(rule, callback)
                if not success:
                    del self.rules[rule.id]
                    return False
            
            logger.info(f"Added automation rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding rule {rule.id}: {e}")
            return False
    
    async def remove_rule(self, rule_id: str) -> bool:
        """Remove an automation rule."""
        try:
            if rule_id in self.rules:
                rule = self.rules[rule_id]
                
                # Remove from scheduler
                if rule.trigger.trigger_type.value == "schedule":
                    automation_scheduler.remove_rule(rule_id)
                
                del self.rules[rule_id]
                logger.info(f"Removed automation rule: {rule_id}")
                return True
            
            logger.warning(f"Rule not found: {rule_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error removing rule {rule_id}: {e}")
            return False
    
    async def pause_rule(self, rule_id: str) -> bool:
        """Pause a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].status = AutomationStatus.PAUSED
            automation_scheduler.pause_rule(rule_id)
            return True
        return False
    
    async def resume_rule(self, rule_id: str) -> bool:
        """Resume a paused rule."""
        if rule_id in self.rules:
            self.rules[rule_id].status = AutomationStatus.ACTIVE
            automation_scheduler.resume_rule(rule_id)
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self, status: Optional[AutomationStatus] = None) -> List[AutomationRule]:
        """List all rules, optionally filtered by status."""
        if status:
            return [r for r in self.rules.values() if r.status == status]
        return list(self.rules.values())
    
    def get_recent_runs(self, limit: int = 10) -> List[AutomationRun]:
        """Get recent automation runs."""
        return sorted(
            self.runs,
            key=lambda r: r.started_at,
            reverse=True
        )[:limit]
    
    async def execute_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Execute an automation rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Execution result
        """
        if rule_id not in self.rules:
            logger.error(f"Rule not found: {rule_id}")
            return {"success": False, "error": "Rule not found"}
        
        rule = self.rules[rule_id]
        
        # Check if rule is enabled
        if not rule.enabled or rule.status != AutomationStatus.ACTIVE:
            logger.debug(f"Rule {rule.name} is disabled or paused")
            return {"success": False, "error": "Rule is disabled or paused"}
        
        # Check max runs
        if rule.max_runs and rule.run_count >= rule.max_runs:
            logger.info(f"Rule {rule.name} has reached max runs ({rule.max_runs})")
            await self.pause_rule(rule_id)
            return {"success": False, "error": "Max runs reached"}
        
        # Create run record
        run = AutomationRun(
            rule_id=rule.id,
            rule_name=rule.name,
            started_at=datetime.now(),
            status="running"
        )
        
        logger.info(f"Executing automation rule: {rule.name}")
        
        try:
            # Execute actions
            results = []
            for i, action in enumerate(rule.actions):
                try:
                    result = await self._execute_action(action)
                    results.append(result)
                    
                    if result.get("success"):
                        run.actions_executed += 1
                    else:
                        run.actions_failed += 1
                        logger.error(f"Action {i+1} failed: {result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Action {i+1} error: {e}")
                    run.actions_failed += 1
                    results.append({"success": False, "error": str(e)})
            
            # Update run record
            run.completed_at = datetime.now()
            run.status = "success" if run.actions_failed == 0 else "partial"
            run.output = {"results": results}
            
            # Update rule
            rule.run_count += 1
            rule.last_run = datetime.now()
            
            # Store run
            self.runs.append(run)
            if len(self.runs) > 1000:  # Keep last 1000 runs
                self.runs = self.runs[-1000:]
            
            logger.info(
                f"Rule {rule.name} completed: "
                f"{run.actions_executed} succeeded, {run.actions_failed} failed"
            )
            
            return {
                "success": True,
                "run": run.dict(),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.name}: {e}")
            run.completed_at = datetime.now()
            run.status = "failed"
            run.error = str(e)
            self.runs.append(run)
            
            return {"success": False, "error": str(e)}
    
    async def _execute_action(self, action: Action) -> Dict[str, Any]:
        """
        Execute a single action.
        
        Args:
            action: Action to execute
            
        Returns:
            Action result
        """
        try:
            if action.action_type == ActionType.COMMAND:
                return await self._execute_command(action)
            
            elif action.action_type == ActionType.TOOL:
                return await self._execute_tool(action)
            
            elif action.action_type == ActionType.AGENT:
                return await self._execute_agent(action)
            
            elif action.action_type == ActionType.LLM:
                return await self._execute_llm(action)
            
            elif action.action_type == ActionType.NOTIFICATION:
                return await self._execute_notification(action)
            
            elif action.action_type == ActionType.WEBHOOK:
                return await self._execute_webhook(action)
            
            elif action.action_type == ActionType.SCRIPT:
                return await self._execute_script(action)
            
            else:
                return {"success": False, "error": f"Unknown action type: {action.action_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_command(self, action: Action) -> Dict[str, Any]:
        """Execute shell command."""
        try:
            process = await asyncio.create_subprocess_shell(
                action.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=action.timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "returncode": process.returncode
                }
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": "Command timeout"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_tool(self, action: Action) -> Dict[str, Any]:
        """Execute a JARVIS tool."""
        try:
            from ..tools import tool_registry, tool_executor
            
            tool = tool_registry.get(action.tool_name)
            if not tool:
                return {"success": False, "error": f"Tool not found: {action.tool_name}"}
            
            result = await tool_executor.execute(action.tool_name, action.tool_params or {})
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_agent(self, action: Action) -> Dict[str, Any]:
        """Delegate to an agent."""
        try:
            from ..agents import agent_coordinator
            
            result = await agent_coordinator.delegate_task(
                action.agent_task,
                action.agent_context
            )
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_llm(self, action: Action) -> Dict[str, Any]:
        """Execute LLM query."""
        try:
            from ..llm import llm_manager
            
            response = await llm_manager.generate(action.llm_prompt)
            return {"success": True, "response": response}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_notification(self, action: Action) -> Dict[str, Any]:
        """Send notification."""
        try:
            # For now, just log it
            # In a full implementation, would use system notifications
            logger.info(
                f"NOTIFICATION: {action.notification_title} - {action.notification_message}"
            )
            return {
                "success": True,
                "message": "Notification sent (logged)"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_webhook(self, action: Action) -> Dict[str, Any]:
        """Execute webhook."""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                if action.webhook_method == "POST":
                    response = await client.post(
                        action.webhook_url,
                        json=action.webhook_data,
                        timeout=action.timeout
                    )
                elif action.webhook_method == "GET":
                    response = await client.get(
                        action.webhook_url,
                        timeout=action.timeout
                    )
                else:
                    return {"success": False, "error": f"Unknown method: {action.webhook_method}"}
                
                return {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response": response.text
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_script(self, action: Action) -> Dict[str, Any]:
        """Execute Python script."""
        try:
            # Create execution context
            context = {
                "logger": logger,
                "result": None
            }
            
            # Execute script
            if action.script_code:
                exec(action.script_code, context)
            elif action.script_file:
                with open(action.script_file, 'r') as f:
                    exec(f.read(), context)
            else:
                return {"success": False, "error": "No script provided"}
            
            return {
                "success": True,
                "result": context.get("result")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global engine instance
automation_engine = AutomationEngine()
