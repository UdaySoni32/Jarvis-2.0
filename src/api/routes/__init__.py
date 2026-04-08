"""API Routes"""

from fastapi import APIRouter

# Create routers
auth_router = APIRouter()
chat_router = APIRouter()
plugins_router = APIRouter()
system_router = APIRouter()
websocket_router = APIRouter()

# Import route handlers
from . import auth, chat, plugins, system, websocket

__all__ = [
    "auth_router",
    "chat_router",
    "plugins_router",
    "system_router",
    "websocket_router",
]
