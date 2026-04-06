"""Tool registry for managing available tools."""

from typing import Dict, List, Optional

from ..logger import logger
from .base import BaseTool


class ToolRegistry:
    """Registry for managing tools/functions."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        logger.info("Tool registry initialized")

    def register(self, tool: BaseTool):
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        tool_name = tool.name
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")

        self._tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name}")

    def unregister(self, tool_name: str):
        """
        Unregister a tool.

        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools.

        Returns:
            Dictionary of tool name to tool instance
        """
        return self._tools.copy()

    def get_openai_functions(self) -> List[Dict]:
        """
        Get OpenAI function schemas for all tools.

        Returns:
            List of OpenAI function definitions
        """
        return [tool.to_openai_function() for tool in self._tools.values()]

    def clear(self):
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("Tool registry cleared")

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered."""
        return tool_name in self._tools


# Global tool registry instance
tool_registry = ToolRegistry()
