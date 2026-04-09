"""
Plugin Management API Routes

Endpoints for managing, configuring, and executing JARVIS plugins.
"""

from fastapi import Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import asyncio
import time
from datetime import datetime

from . import plugins_router
from ..middleware.auth import get_current_user, get_current_user_optional
from ..models.user import User

logger = logging.getLogger(__name__)


# Pydantic Models
class PluginInfo(BaseModel):
    """Plugin information model"""
    name: str = Field(..., description="Plugin name")
    display_name: str = Field(..., description="Human-readable plugin name")
    description: str = Field(..., description="Plugin description")
    version: str = Field(..., description="Plugin version")
    category: str = Field(..., description="Plugin category")
    author: str = Field(..., description="Plugin author")
    enabled: bool = Field(..., description="Whether plugin is enabled")
    installed: bool = Field(..., description="Whether plugin is installed")
    configuration_schema: Dict[str, Any] = Field(default_factory=dict, description="Plugin configuration schema")
    requirements: List[str] = Field(default_factory=list, description="Plugin requirements")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")


class PluginConfiguration(BaseModel):
    """Plugin configuration model"""
    plugin_name: str = Field(..., description="Plugin name to configure")
    config: Dict[str, Any] = Field(..., description="Plugin configuration data")
    enabled: bool = Field(default=True, description="Whether to enable the plugin")


class PluginExecutionRequest(BaseModel):
    """Plugin execution request model"""
    plugin_name: str = Field(..., description="Plugin name to execute")
    action: str = Field(..., description="Plugin action to execute") 
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    async_execution: bool = Field(default=False, description="Execute asynchronously")


class PluginExecutionResult(BaseModel):
    """Plugin execution result model"""
    plugin_name: str
    action: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime


# Get plugin registry from app state
async def get_plugin_registry(request: Request):
    """Get plugin registry from application state"""
    registry = getattr(request.app.state, "plugin_registry", None)
    if registry is not None:
        return registry

    try:
        from ...plugins.registry import PluginRegistry

        registry = PluginRegistry()
        request.app.state.plugin_registry = registry
        return registry
    except Exception as e:
        logger.error(f"Failed to get plugin registry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plugin registry not available"
        )


@plugins_router.get("/", 
                   response_model=List[PluginInfo],
                   summary="List All Plugins",
                   description="Get list of all available plugins with their information")
async def list_plugins(
    category: Optional[str] = None,
    enabled_only: bool = False,
    installed_only: bool = False,
    plugin_registry = Depends(get_plugin_registry),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List all available plugins with filtering options"""
    try:
        plugins = plugin_registry.get_available_plugins()
        
        # Convert to PluginInfo models
        plugin_list = []
        for plugin_name, plugin_class in plugins.items():
            try:
                plugin_info = plugin_class.get_info()
                
                # Check if plugin is enabled for this user
                enabled = True  # Default enabled for now
                
                plugin_data = PluginInfo(
                    name=plugin_name,
                    display_name=plugin_info.get("display_name", plugin_name.title()),
                    description=plugin_info.get("description", "No description available"),
                    version=plugin_info.get("version", "1.0.0"),
                    category=plugin_info.get("category", "general"),
                    author=plugin_info.get("author", "JARVIS Team"),
                    enabled=enabled,
                    installed=True,  # All loaded plugins are considered installed
                    configuration_schema=plugin_info.get(
                        "configuration_schema",
                        plugin_info.get("config_schema", {})
                    ),
                    requirements=plugin_info.get("requirements", []),
                    permissions=plugin_info.get("permissions", [])
                )
                
                # Apply filters
                if category and plugin_data.category != category:
                    continue
                if enabled_only and not plugin_data.enabled:
                    continue
                if installed_only and not plugin_data.installed:
                    continue
                    
                plugin_list.append(plugin_data)
                
            except Exception as e:
                logger.warning(f"Error getting info for plugin {plugin_name}: {e}")
                continue
        
        return plugin_list
        
    except Exception as e:
        logger.error(f"Error listing plugins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugins: {str(e)}"
        )


@plugins_router.get("/categories",
                   summary="List Plugin Categories",
                   description="Get list of all plugin categories")
async def list_plugin_categories(
    plugin_registry = Depends(get_plugin_registry)
):
    """Get list of all plugin categories"""
    try:
        plugins = plugin_registry.get_available_plugins()
        categories = set()
        
        for plugin_name, plugin_class in plugins.items():
            try:
                plugin_info = plugin_class.get_info()
                category = plugin_info.get("category", "general")
                categories.add(category)
            except Exception as e:
                logger.warning(f"Error getting category for plugin {plugin_name}: {e}")
                continue
        
        return {
            "categories": sorted(list(categories)),
            "total_count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error listing plugin categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugin categories: {str(e)}"
        )


@plugins_router.get("/stats",
                   summary="Plugin Statistics", 
                   description="Get plugin usage statistics")
async def get_plugin_stats(
    plugin_registry = Depends(get_plugin_registry),
    current_user: User = Depends(get_current_user)
):
    """Get plugin usage statistics"""
    try:
        plugins = plugin_registry.get_available_plugins()
        
        stats = {
            "total_plugins": len(plugins),
            "enabled_plugins": len(plugins),  # All enabled by default for now
            "disabled_plugins": 0,
            "categories": {},
            "user_plugins": {}
        }
        
        for plugin_name, plugin_class in plugins.items():
            try:
                plugin_info = plugin_class.get_info()
                category = plugin_info.get("category", "general")
                
                # Count by category
                if category not in stats["categories"]:
                    stats["categories"][category] = 0
                stats["categories"][category] += 1
                
                # All plugins enabled by default for now
                stats["user_plugins"][plugin_name] = {
                    "enabled": True,
                    "category": category
                }
                
            except Exception as e:
                logger.warning(f"Error getting stats for plugin {plugin_name}: {e}")
                continue
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting plugin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin statistics: {str(e)}"
        )


@plugins_router.get("/{plugin_name}",
                   response_model=PluginInfo, 
                   summary="Get Plugin Details",
                   description="Get detailed information about a specific plugin")
async def get_plugin(
    plugin_name: str,
    plugin_registry = Depends(get_plugin_registry),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get detailed information about a specific plugin"""
    try:
        plugins = plugin_registry.get_available_plugins()
        
        if plugin_name not in plugins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_name}' not found"
            )
        
        plugin_class = plugins[plugin_name]
        plugin_info = plugin_class.get_info()
        
        # Check if plugin is enabled for this user
        enabled = True  # Default enabled for now
        
        return PluginInfo(
            name=plugin_name,
            display_name=plugin_info.get("display_name", plugin_name.title()),
            description=plugin_info.get("description", "No description available"),
            version=plugin_info.get("version", "1.0.0"),
            category=plugin_info.get("category", "general"),
            author=plugin_info.get("author", "JARVIS Team"),
            enabled=enabled,
            installed=True,
            configuration_schema=plugin_info.get(
                "configuration_schema",
                plugin_info.get("config_schema", {})
            ),
            requirements=plugin_info.get("requirements", []),
            permissions=plugin_info.get("permissions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugin {plugin_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin information: {str(e)}"
        )


@plugins_router.get("/{plugin_name}/actions",
                   summary="List Plugin Actions",
                   description="Get available actions for a specific plugin")
async def get_plugin_actions(
    plugin_name: str,
    plugin_registry = Depends(get_plugin_registry),
    current_user: User = Depends(get_current_user)
):
    """Get available actions for a specific plugin"""
    try:
        plugins = plugin_registry.get_available_plugins()
        
        if plugin_name not in plugins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_name}' not found"
            )
        
        plugin_class = plugins[plugin_name]
        
        # Get plugin instance to check available actions
        plugin_instance = plugin_class()
        actions = {}

        parameters = plugin_instance.get_parameters()
        action_parameter = parameters.get("action")

        if action_parameter and action_parameter.enum:
            for action_name in action_parameter.enum:
                actions[action_name] = {
                    "description": action_parameter.description or "No description available",
                    "parameters": {},
                }
        else:
            actions["execute"] = {
                "description": "Execute plugin with provided parameters",
                "parameters": {},
            }
        
        return {
            "plugin_name": plugin_name,
            "actions": actions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugin actions for {plugin_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin actions: {str(e)}"
        )


@plugins_router.post("/{plugin_name}/execute",
                    response_model=PluginExecutionResult,
                    summary="Execute Plugin Action",
                    description="Execute a specific action on a plugin")
async def execute_plugin_action(
    plugin_name: str,
    execution_request: PluginExecutionRequest,
    background_tasks: BackgroundTasks,
    plugin_registry = Depends(get_plugin_registry),
    current_user: User = Depends(get_current_user)
):
    """Execute a specific action on a plugin"""
    try:
        plugins = plugin_registry.get_available_plugins()
        
        if plugin_name != execution_request.plugin_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plugin name in URL must match plugin name in request"
            )
        
        if plugin_name not in plugins:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_name}' not found"
            )
        
        # Execute the plugin action
        start_time = time.time()
        
        try:
            from ...core.tools.executor import tool_executor
            execution_params = {"action": execution_request.action, **execution_request.parameters}
            
            if execution_request.async_execution:
                # Execute asynchronously in background
                task_id = f"{plugin_name}_{execution_request.action}_{int(start_time)}"
                
                background_tasks.add_task(
                    _execute_plugin_background,
                    plugin_name,
                    execution_params,
                    task_id
                )
                
                return PluginExecutionResult(
                    plugin_name=plugin_name,
                    action=execution_request.action,
                    success=True,
                    result={"task_id": task_id, "status": "running"},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            else:
                # Execute synchronously
                result = await tool_executor.execute(plugin_name, execution_params)
                
                return PluginExecutionResult(
                    plugin_name=plugin_name,
                    action=execution_request.action,
                    success=result.get("success", False),
                    result=result.get("result"),
                    error=result.get("error"),
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
                
        except Exception as exec_error:
            return PluginExecutionResult(
                plugin_name=plugin_name,
                action=execution_request.action,
                success=False,
                error=str(exec_error),
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing plugin {plugin_name}.{execution_request.action}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute plugin action: {str(e)}"
        )


async def _execute_plugin_background(
    tool_name: str,
    arguments: Dict[str, Any],
    task_id: str
):
    """Execute plugin in background task"""
    try:
        from ...core.tools.executor import tool_executor
        await tool_executor.execute(tool_name, arguments)
        
        logger.info(f"Background plugin execution completed: {task_id}")
        # In a real implementation, you'd store this result somewhere
        # for the user to retrieve later
        
    except Exception as e:
        logger.error(f"Background plugin execution failed: {task_id}, error: {e}")
