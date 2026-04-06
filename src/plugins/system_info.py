"""System information tool."""

from typing import Dict

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.tools.base import BaseTool, ToolParameter


class SystemInfoTool(BaseTool):
    """Gets system information like CPU, memory, and disk usage."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "info_type": ToolParameter(
                name="info_type",
                type="string",
                description="Type of system info to retrieve",
                required=False,
                default="all",
                enum=["all", "cpu", "memory", "disk"],
            )
        }

    async def execute(self, info_type: str = "all") -> Dict[str, any]:
        """
        Get system information.

        Args:
            info_type: Type of info (all, cpu, memory, disk)

        Returns:
            System information
        """
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil not installed. Install with: pip install psutil")

        result = {}

        if info_type in ["all", "cpu"]:
            result["cpu"] = {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
            }

        if info_type in ["all", "memory"]:
            mem = psutil.virtual_memory()
            result["memory"] = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent,
            }

        if info_type in ["all", "disk"]:
            disk = psutil.disk_usage("/")
            result["disk"] = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            }

        return result
