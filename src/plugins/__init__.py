"""Plugin initialization and registration."""

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
