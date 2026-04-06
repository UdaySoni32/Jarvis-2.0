"""Tool executor for running tools and handling results."""

import json
from typing import Any, Dict, Optional

from ..logger import logger
from .base import BaseTool
from .registry import tool_registry


class ToolExecutor:
    """Executes tools and formats results."""

    def __init__(self):
        """Initialize tool executor."""
        self.registry = tool_registry
        logger.info("Tool executor initialized")

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Execution result with status and data
        """
        try:
            # Get tool from registry
            tool = self.registry.get(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": self.registry.list_tools(),
                }

            logger.info(f"Executing tool: {tool_name} with args: {arguments}")

            # Execute tool
            result = await tool.execute(**arguments)

            return {
                "success": True,
                "tool": tool_name,
                "result": result,
            }

        except TypeError as e:
            logger.error(f"Invalid arguments for tool {tool_name}: {e}")
            return {
                "success": False,
                "error": f"Invalid arguments: {e}",
                "tool": tool_name,
            }

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
            }

    async def execute_from_llm(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool from LLM tool call.

        Args:
            tool_call: Tool call from LLM (with name and arguments)

        Returns:
            Execution result
        """
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        # Handle arguments if they're a string (parse JSON)
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON in arguments",
                    "tool": tool_name,
                }

        return await self.execute(tool_name, arguments)

    def format_result_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Format tool execution result for LLM.

        Args:
            result: Tool execution result

        Returns:
            Formatted string result
        """
        if result["success"]:
            tool_result = result.get("result")
            if isinstance(tool_result, dict):
                return json.dumps(tool_result, indent=2)
            elif isinstance(tool_result, (list, tuple)):
                return json.dumps(tool_result)
            else:
                return str(tool_result)
        else:
            return f"Error: {result.get('error', 'Unknown error')}"


# Global tool executor instance
tool_executor = ToolExecutor()
