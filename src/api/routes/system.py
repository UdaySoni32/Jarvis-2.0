"""
System Routes

System status, health checks, and model management.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
import psutil
import platform

from . import system_router
from ..routes.auth import get_current_user
from ..utils import get_db
from ...core.llm.manager import llm_manager
from ...core.config import settings


@system_router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns basic system health status.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api_version": "v1",
    }


@system_router.get("/status")
async def system_status(current_user = Depends(get_current_user)):
    """
    Get system status
    
    Returns detailed system information and resource usage.
    """
    return {
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        },
        "resources": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "disk_used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
            "disk_percent": psutil.disk_usage('/').percent,
        },
        "config": {
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "enable_memory": settings.enable_memory,
            "enable_plugins": settings.enable_plugins,
            "debug": settings.debug,
        },
    }


@system_router.get("/models")
async def list_models(current_user = Depends(get_current_user)):
    """
    List available LLM models
    
    Returns all configured LLM providers and their models.
    """
    available_models = llm_manager.get_available_models()
    current_model = llm_manager.current_model
    
    return {
        "current_model": current_model,
        "available_models": available_models,
        "providers": {
            "ollama": {
                "name": "Ollama",
                "available": llm_manager.check_provider_available("ollama"),
                "models": ["llama3", "llama2", "mistral", "codellama"],
            },
            "openai": {
                "name": "OpenAI",
                "available": llm_manager.check_provider_available("openai"),
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "available": llm_manager.check_provider_available("anthropic"),
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            },
            "google": {
                "name": "Google Gemini",
                "available": llm_manager.check_provider_available("google"),
                "models": ["gemini-pro", "gemini-ultra"],
            },
        },
    }


@system_router.post("/models/{model_name}")
async def switch_model(
    model_name: str,
    current_user = Depends(get_current_user)
):
    """
    Switch active LLM model
    
    Change the active model for the current session.
    """
    try:
        llm_manager.set_model(model_name)
        return {
            "success": True,
            "model": model_name,
            "message": f"Switched to model: {model_name}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@system_router.get("/plugins")
async def list_plugins(current_user = Depends(get_current_user)):
    """
    List available plugins
    
    Returns all loaded plugins and their status.
    """
    from ...plugins import PLUGIN_REGISTRY
    
    plugins = []
    for name, plugin_class in PLUGIN_REGISTRY.items():
        plugin = plugin_class()
        plugins.append({
            "name": name,
            "description": plugin.description if hasattr(plugin, 'description') else "",
            "version": plugin.version if hasattr(plugin, 'version') else "1.0.0",
            "enabled": True,
        })
    
    return {
        "plugins": plugins,
        "total": len(plugins),
    }
