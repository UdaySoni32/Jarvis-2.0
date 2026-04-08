"""Process management tool."""

from typing import Dict, List
import signal

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.core.tools.base import BaseTool, ToolParameter


class ProcessManagerTool(BaseTool):
    """Lists and manages system processes."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Process action",
                required=True,
                enum=["list", "info", "kill"],
            ),
            "filter": ToolParameter(
                name="filter",
                type="string",
                description="Filter processes by name (for list)",
                required=False,
            ),
            "pid": ToolParameter(
                name="pid",
                type="number",
                description="Process ID (for info/kill)",
                required=False,
            ),
            "sort_by": ToolParameter(
                name="sort_by",
                type="string",
                description="Sort processes by field",
                required=False,
                default="cpu",
                enum=["cpu", "memory", "name", "pid"],
            ),
            "limit": ToolParameter(
                name="limit",
                type="number",
                description="Maximum processes to return",
                required=False,
                default=10,
            ),
        }

    async def execute(
        self,
        action: str,
        filter: str = None,
        pid: int = None,
        sort_by: str = "cpu",
        limit: int = 10,
    ) -> Dict:
        """
        Manage processes.

        Args:
            action: list, info, or kill
            filter: Filter by process name
            pid: Process ID
            sort_by: Sort field (cpu, memory, name, pid)
            limit: Max processes to return

        Returns:
            Process information
        """
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil not installed. Install with: pip install psutil")

        if action == "list":
            processes = []

            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
                try:
                    pinfo = proc.info
                    
                    # Apply filter if specified
                    if filter and filter.lower() not in pinfo["name"].lower():
                        continue

                    processes.append(
                        {
                            "pid": pinfo["pid"],
                            "name": pinfo["name"],
                            "cpu_percent": pinfo["cpu_percent"],
                            "memory_percent": round(pinfo["memory_percent"], 2),
                            "status": pinfo["status"],
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x["memory_percent"], reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x["name"].lower())
            elif sort_by == "pid":
                processes.sort(key=lambda x: x["pid"])

            # Limit results
            processes = processes[:limit]

            return {
                "action": "list",
                "processes": processes,
                "count": len(processes),
                "total_processes": len(list(psutil.process_iter())),
            }

        elif action == "info":
            if not pid:
                raise ValueError("PID required for info action")

            try:
                proc = psutil.Process(pid)
                info = {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_info": {
                        "rss_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                        "vms_mb": round(proc.memory_info().vms / 1024 / 1024, 2),
                        "percent": round(proc.memory_percent(), 2),
                    },
                    "num_threads": proc.num_threads(),
                    "create_time": proc.create_time(),
                }

                # Try to get additional info (may fail with permission errors)
                try:
                    info["cmdline"] = " ".join(proc.cmdline())
                    info["cwd"] = proc.cwd()
                    info["username"] = proc.username()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                return {"action": "info", "process": info}

            except psutil.NoSuchProcess:
                raise ValueError(f"Process not found: PID {pid}")
            except psutil.AccessDenied:
                raise ValueError(f"Access denied for process PID {pid}")

        elif action == "kill":
            if not pid:
                raise ValueError("PID required for kill action")

            try:
                proc = psutil.Process(pid)
                proc_name = proc.name()
                
                # Safety check - don't kill critical system processes
                critical_processes = ["systemd", "init", "kernel", "launchd"]
                if any(crit in proc_name.lower() for crit in critical_processes):
                    raise ValueError(
                        f"Cannot kill critical system process: {proc_name}"
                    )

                proc.terminate()  # SIGTERM first
                proc.wait(timeout=3)  # Wait for graceful shutdown

                return {
                    "action": "killed",
                    "pid": pid,
                    "name": proc_name,
                    "message": f"Terminated process {proc_name} (PID: {pid})",
                }

            except psutil.NoSuchProcess:
                raise ValueError(f"Process not found: PID {pid}")
            except psutil.AccessDenied:
                raise ValueError(
                    f"Access denied. Cannot kill process PID {pid} (may require elevated permissions)"
                )
            except psutil.TimeoutExpired:
                # Force kill if terminate didn't work
                try:
                    proc.kill()  # SIGKILL
                    return {
                        "action": "killed",
                        "pid": pid,
                        "name": proc_name,
                        "message": f"Force killed process {proc_name} (PID: {pid})",
                    }
                except:
                    raise ValueError(f"Failed to kill process PID {pid}")

        else:
            raise ValueError(f"Unknown action: {action}")
