"""Compatibility plugin registry for API routes."""

from typing import Dict, Type

from src.core.tools.base import BaseTool

from . import PLUGIN_REGISTRY


class PluginRegistry:
    """Wrapper around the global plugin registry."""

    def __init__(self):
        self._registry = PLUGIN_REGISTRY

    def get_available_plugins(self) -> Dict[str, Type[BaseTool]]:
        """Return all registered plugin classes."""
        return self._registry.copy()

    def get_plugin(self, name: str):
        """Return a plugin class by name."""
        return self._registry.get(name)

    def __len__(self) -> int:
        return len(self._registry)
