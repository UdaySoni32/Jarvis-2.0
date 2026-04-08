"""Plugin initialization and registration."""

from typing import Any, Dict, Type

from src.core.tools.registry import tool_registry
from src.core.logger import logger

# Import tools
from .calculator import CalculatorTool
from .system_info import SystemInfoTool
from .file_ops import FileReadTool, FileListTool
from .datetime_info import DateTimeTool
from .web_search import WebSearchTool
from .weather import WeatherTool
from .timer import TimerTool
from .notes import NotesTool
from .process_manager import ProcessManagerTool
from .email_integration import EmailIntegrationTool
from .calendar_integration import CalendarIntegrationTool
from .database_integration import DatabaseIntegrationTool
from .github_integration import GitHubIntegrationTool
from .docker_integration import DockerIntegrationTool
from .clipboard_manager import ClipboardManagerTool
from .api_testing import APITestingTool
from .screen_capture_ocr import ScreenCaptureOCRTool


def _plugin_key(plugin_cls: Type) -> str:
    return plugin_cls.__name__.lower().replace("tool", "")


def _plugin_info(plugin_cls: Type) -> Dict[str, Any]:
    """Build metadata for a plugin class."""
    try:
        plugin = plugin_cls()
        parameters = plugin.get_parameters()
    except Exception as exc:
        logger.warning(f"Unable to inspect plugin {plugin_cls.__name__}: {exc}")
        return {
            "name": _plugin_key(plugin_cls),
            "display_name": plugin_cls.__name__.replace("Tool", "").replace("_", " "),
            "description": plugin_cls.__doc__ or "No description available",
            "version": "1.0.0",
            "category": "general",
            "author": "JARVIS Team",
            "enabled": True,
            "installed": True,
            "configuration_schema": {},
            "requirements": [],
            "permissions": [],
        }

    return {
        "name": plugin.name,
        "display_name": plugin_cls.__name__.replace("Tool", "").replace("_", " "),
        "description": plugin.description or "No description available",
        "version": getattr(plugin_cls, "version", "1.0.0"),
        "category": getattr(plugin_cls, "category", "general"),
        "author": getattr(plugin_cls, "author", "JARVIS Team"),
        "enabled": True,
        "installed": True,
        "configuration_schema": {
            name: {
                "type": param.type,
                "description": param.description,
                "required": param.required,
                "default": param.default,
                "enum": param.enum,
            }
            for name, param in parameters.items()
        },
        "requirements": list(getattr(plugin_cls, "requirements", [])),
        "permissions": list(getattr(plugin_cls, "permissions", [])),
    }


def _attach_info_method(plugin_cls: Type) -> None:
    if not hasattr(plugin_cls, "get_info"):
        setattr(plugin_cls, "get_info", classmethod(lambda cls: _plugin_info(cls)))


def register_all_plugins():
    """Register all available plugins."""
    plugins = [
        # Basic tools
        CalculatorTool(),
        SystemInfoTool(),
        FileReadTool(),
        FileListTool(),
        # New core plugins
        DateTimeTool(),
        WebSearchTool(),
        WeatherTool(),
        TimerTool(),
        NotesTool(),
        ProcessManagerTool(),
        # Advanced plugins (Phase 2.6)
        EmailIntegrationTool(),
        CalendarIntegrationTool(),
        DatabaseIntegrationTool(),
        GitHubIntegrationTool(),
        DockerIntegrationTool(),
        ClipboardManagerTool(),
        APITestingTool(),
        ScreenCaptureOCRTool(),
    ]

    for plugin in plugins:
        try:
            tool_registry.register(plugin)
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {e}")

    logger.info(f"Registered {len(tool_registry)} plugins")


# Auto-register on import
register_all_plugins()

PLUGIN_REGISTRY = {
    _plugin_key(plugin_cls): plugin_cls
    for plugin_cls in [
        CalculatorTool,
        SystemInfoTool,
        FileReadTool,
        FileListTool,
        DateTimeTool,
        WebSearchTool,
        WeatherTool,
        TimerTool,
        NotesTool,
        ProcessManagerTool,
        EmailIntegrationTool,
        CalendarIntegrationTool,
        DatabaseIntegrationTool,
        GitHubIntegrationTool,
        DockerIntegrationTool,
        ClipboardManagerTool,
        APITestingTool,
        ScreenCaptureOCRTool,
    ]
}

for _plugin_cls in PLUGIN_REGISTRY.values():
    _attach_info_method(_plugin_cls)

__all__ = [
    "PLUGIN_REGISTRY",
    "register_all_plugins",
]
