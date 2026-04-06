"""Base tool class for JARVIS function calling system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[list] = None


class BaseTool(ABC):
    """Abstract base class for tools/functions."""

    def __init__(self):
        """Initialize tool."""
        self.name = self.__class__.__name__.lower().replace("tool", "")
        self.description = self.__doc__ or "No description provided"

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """
        Get tool parameter definitions.

        Returns:
            Dictionary of parameter name to ToolParameter
        """
        pass

    def to_openai_function(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function schema.

        Returns:
            OpenAI function definition
        """
        parameters = self.get_parameters()

        properties = {}
        required = []

        for param_name, param in parameters.items():
            prop = {
                "type": param.type,
                "description": param.description,
            }

            if param.enum:
                prop["enum"] = param.enum

            properties[param_name] = prop

            if param.required:
                required.append(param_name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
