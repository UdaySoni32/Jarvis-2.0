"""
Docker Integration Plugin for JARVIS 2.0

Docker container management and orchestration capabilities.
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from src.core.tools.base import BaseTool, ToolParameter


@dataclass
class DockerExecutor:
    """Executes Docker CLI commands"""
    
    @staticmethod
    async def run(cmd: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute docker command"""
        try:
            process = await asyncio.create_subprocess_shell(
                f"docker {cmd}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip()
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DockerIntegrationTool(BaseTool):
    """Docker integration tool for container management"""
    
    def __init__(self):
        super().__init__()
        self.executor = DockerExecutor()
    
    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters"""
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Docker action",
                required=True,
                enum=[
                    "list_containers", "get_container", "create_container",
                    "start_container", "stop_container", "remove_container",
                    "list_images", "get_image", "pull_image", "remove_image",
                    "list_networks", "list_volumes", "get_docker_info",
                    "execute_in_container", "get_logs", "get_stats"
                ]
            ),
            "container_id": ToolParameter(
                name="container_id",
                type="string",
                description="Container ID or name",
                required=False
            ),
            "image": ToolParameter(
                name="image",
                type="string",
                description="Image name",
                required=False
            )
        }
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Docker operation"""
        
        if action == "list_containers":
            return await self._list_containers(**kwargs)
        elif action == "get_container":
            return await self._get_container(**kwargs)
        elif action == "create_container":
            return await self._create_container(**kwargs)
        elif action == "start_container":
            return await self._start_container(**kwargs)
        elif action == "stop_container":
            return await self._stop_container(**kwargs)
        elif action == "remove_container":
            return await self._remove_container(**kwargs)
        elif action == "list_images":
            return await self._list_images(**kwargs)
        elif action == "get_image":
            return await self._get_image(**kwargs)
        elif action == "pull_image":
            return await self._pull_image(**kwargs)
        elif action == "remove_image":
            return await self._remove_image(**kwargs)
        elif action == "list_networks":
            return await self._list_networks(**kwargs)
        elif action == "list_volumes":
            return await self._list_volumes(**kwargs)
        elif action == "get_docker_info":
            return await self._get_docker_info(**kwargs)
        elif action == "execute_in_container":
            return await self._execute_in_container(**kwargs)
        elif action == "get_logs":
            return await self._get_logs(**kwargs)
        elif action == "get_stats":
            return await self._get_stats(**kwargs)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _list_containers(self, all: bool = False, **kwargs) -> Dict[str, Any]:
        """List containers"""
        cmd = "ps" + (" -a" if all else "")
        result = await self.executor.run(cmd)
        return {
            "success": result["success"],
            "containers": result["stdout"],
            "error": result.get("error")
        }
    
    async def _get_container(self, container_id: str, **kwargs) -> Dict[str, Any]:
        """Get container info"""
        result = await self.executor.run(f"inspect {container_id}")
        if not result["success"]:
            return {"success": False, "error": f"Container {container_id} not found"}
        try:
            data = json.loads(result["stdout"])
            return {"success": True, "container": data[0] if data else {}}
        except:
            return {"success": False, "error": "Parse error"}
    
    async def _create_container(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[List[str]] = None,
        env: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create container"""
        cmd = f"run -d"
        if name:
            cmd += f" --name {name}"
        if env:
            for e in env:
                cmd += f" -e {e}"
        if ports:
            for p in ports:
                cmd += f" -p {p}"
        cmd += f" {image}"
        
        result = await self.executor.run(cmd)
        return {
            "success": result["success"],
            "container_id": result["stdout"] if result["success"] else None,
            "error": result.get("error")
        }
    
    async def _start_container(self, container_id: str, **kwargs) -> Dict[str, Any]:
        """Start container"""
        result = await self.executor.run(f"start {container_id}")
        return {"success": result["success"], "error": result.get("error")}
    
    async def _stop_container(self, container_id: str, **kwargs) -> Dict[str, Any]:
        """Stop container"""
        result = await self.executor.run(f"stop {container_id}")
        return {"success": result["success"], "error": result.get("error")}
    
    async def _remove_container(self, container_id: str, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Remove container"""
        cmd = f"rm" + (" -f" if force else "") + f" {container_id}"
        result = await self.executor.run(cmd)
        return {"success": result["success"], "error": result.get("error")}
    
    async def _list_images(self, **kwargs) -> Dict[str, Any]:
        """List images"""
        result = await self.executor.run("images")
        return {
            "success": result["success"],
            "images": result["stdout"],
            "error": result.get("error")
        }
    
    async def _get_image(self, image_id: str, **kwargs) -> Dict[str, Any]:
        """Get image info"""
        result = await self.executor.run(f"inspect {image_id}")
        if not result["success"]:
            return {"success": False, "error": f"Image {image_id} not found"}
        try:
            return {"success": True, "image": json.loads(result["stdout"])[0]}
        except:
            return {"success": False, "error": "Parse error"}
    
    async def _pull_image(self, image: str, **kwargs) -> Dict[str, Any]:
        """Pull image"""
        result = await self.executor.run(f"pull {image}")
        return {"success": result["success"], "error": result.get("error")}
    
    async def _remove_image(self, image_id: str, force: bool = False, **kwargs) -> Dict[str, Any]:
        """Remove image"""
        cmd = f"rmi" + (" -f" if force else "") + f" {image_id}"
        result = await self.executor.run(cmd)
        return {"success": result["success"], "error": result.get("error")}
    
    async def _list_networks(self, **kwargs) -> Dict[str, Any]:
        """List networks"""
        result = await self.executor.run("network ls")
        return {
            "success": result["success"],
            "networks": result["stdout"],
            "error": result.get("error")
        }
    
    async def _list_volumes(self, **kwargs) -> Dict[str, Any]:
        """List volumes"""
        result = await self.executor.run("volume ls")
        return {
            "success": result["success"],
            "volumes": result["stdout"],
            "error": result.get("error")
        }
    
    async def _get_docker_info(self, **kwargs) -> Dict[str, Any]:
        """Get Docker info"""
        result = await self.executor.run("info")
        return {
            "success": result["success"],
            "info": result["stdout"],
            "error": result.get("error")
        }
    
    async def _execute_in_container(self, container_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command in container"""
        result = await self.executor.run(f"exec {container_id} {command}")
        return {
            "success": result["success"],
            "output": result["stdout"],
            "error": result.get("error")
        }
    
    async def _get_logs(self, container_id: str, tail: int = 50, **kwargs) -> Dict[str, Any]:
        """Get container logs"""
        result = await self.executor.run(f"logs --tail {tail} {container_id}")
        return {
            "success": result["success"],
            "logs": result["stdout"],
            "error": result.get("error")
        }
    
    async def _get_stats(self, container_id: str, **kwargs) -> Dict[str, Any]:
        """Get container stats"""
        result = await self.executor.run(f"stats --no-stream {container_id}")
        return {
            "success": result["success"],
            "stats": result["stdout"],
            "error": result.get("error")
        }
