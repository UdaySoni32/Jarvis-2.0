"""
WebSocket Real-time Communication Routes

Provides real-time bidirectional communication for JARVIS 2.0.
Supports chat streaming, presence system, and live notifications.
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.websockets import WebSocketState
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, ValidationError
import logging
import json
import asyncio
import time
from datetime import datetime
from enum import Enum

from . import websocket_router
from ..middleware.auth import get_current_user_from_token, get_current_user, get_current_user_optional
from ..models.user import User
from ...core.llm.manager import llm_manager
from ...core.llm.base import Message

logger = logging.getLogger(__name__)


# WebSocket Event Types
class EventType(str, Enum):
    MESSAGE = "message"
    TYPING = "typing"
    PRESENCE = "presence"
    SYSTEM = "system"
    PLUGIN = "plugin"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


# WebSocket Message Models
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: EventType
    data: Dict[str, Any]
    timestamp: float = None
    user_id: Optional[int] = None
    
    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = time.time()
        super().__init__(**data)


class ChatMessage(BaseModel):
    """Chat message model"""
    content: str
    conversation_id: Optional[str] = None
    streaming: bool = False
    model: Optional[str] = None


class TypingIndicator(BaseModel):
    """Typing indicator model"""
    is_typing: bool
    conversation_id: Optional[str] = None


class PresenceUpdate(BaseModel):
    """User presence update model"""
    status: str  # online, away, busy, offline
    last_seen: Optional[datetime] = None


# WebSocket Connection Manager
class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_presence: Dict[int, str] = {}
        self.typing_users: Dict[str, Set[int]] = {}  # conversation_id -> user_ids
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket, user: User):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Add to active connections
        if user.id not in self.active_connections:
            self.active_connections[user.id] = []
        self.active_connections[user.id].append(websocket)
        
        # Set user online
        self.user_presence[user.id] = "online"
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user.id,
            "connected_at": time.time(),
            "last_heartbeat": time.time(),
        }
        
        logger.info(f"User {user.id} connected via WebSocket")
        
        # Broadcast presence update
        await self.broadcast_presence_update(user.id, "online")
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type=EventType.SYSTEM,
            data={
                "message": "Connected to JARVIS 2.0",
                "user_id": user.id,
                "features": ["chat", "typing", "presence", "notifications"]
            }
        )
        await self.send_to_user(user.id, welcome_msg.dict())
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket not in self.connection_metadata:
            return
            
        metadata = self.connection_metadata[websocket]
        user_id = metadata["user_id"]
        
        # Remove from active connections
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                conn for conn in self.active_connections[user_id] 
                if conn != websocket
            ]
            
            # If no more connections, set user offline
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.user_presence[user_id] = "offline"
                await self.broadcast_presence_update(user_id, "offline")
        
        # Clean up metadata
        del self.connection_metadata[websocket]
        
        # Remove from typing indicators
        for conversation_id, typing_users in self.typing_users.items():
            typing_users.discard(user_id)
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id not in self.active_connections:
            return False
        
        connections_to_remove = []
        for websocket in self.active_connections[user_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    connections_to_remove.append(websocket)
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                connections_to_remove.append(websocket)
        
        # Clean up broken connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket)
        
        return len(self.active_connections.get(user_id, [])) > 0
    
    async def broadcast_to_all(self, message: Dict[str, Any], exclude_user: Optional[int] = None):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(user_id, message)
    
    async def broadcast_presence_update(self, user_id: int, status: str):
        """Broadcast user presence update"""
        presence_msg = WebSocketMessage(
            type=EventType.PRESENCE,
            data={
                "user_id": user_id,
                "status": status,
                "timestamp": time.time()
            }
        )
        await self.broadcast_to_all(presence_msg.dict(), exclude_user=user_id)
    
    async def update_typing_status(self, user_id: int, conversation_id: str, is_typing: bool):
        """Update typing indicator status"""
        if conversation_id not in self.typing_users:
            self.typing_users[conversation_id] = set()
        
        if is_typing:
            self.typing_users[conversation_id].add(user_id)
        else:
            self.typing_users[conversation_id].discard(user_id)
        
        # Broadcast typing update (exclude the typing user)
        typing_msg = WebSocketMessage(
            type=EventType.TYPING,
            data={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "is_typing": is_typing,
                "typing_users": list(self.typing_users[conversation_id])
            }
        )
        
        # Send to all users except the one typing
        for other_user_id in self.active_connections.keys():
            if other_user_id != user_id:
                await self.send_to_user(other_user_id, typing_msg.dict())
    
    def get_online_users(self) -> List[Dict[str, Any]]:
        """Get list of currently online users"""
        online_users = []
        for user_id, status in self.user_presence.items():
            if status == "online":
                connections = len(self.active_connections.get(user_id, []))
                online_users.append({
                    "user_id": user_id,
                    "status": status,
                    "connections": connections
                })
        return online_users
    
    async def handle_heartbeat(self, websocket: WebSocket):
        """Handle heartbeat from client"""
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_heartbeat"] = time.time()
            
            # Send heartbeat response
            heartbeat_msg = WebSocketMessage(
                type=EventType.HEARTBEAT,
                data={"status": "alive", "server_time": time.time()}
            )
            await websocket.send_json(heartbeat_msg.dict())


# Global WebSocket manager instance
manager = WebSocketManager()


# WebSocket Authentication
async def get_websocket_user(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication")
) -> User:
    """Authenticate WebSocket connection"""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token required")
    
    try:
        # Use the auth middleware function
        user = await get_current_user_from_token(token)
        return user
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@websocket_router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_websocket_user)
):
    """Main WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, user)
    
    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_json()
                message = WebSocketMessage(**data)
                message.user_id = user.id
                
                # Route message based on type
                await handle_websocket_message(websocket, user, message)
                
            except ValidationError as e:
                # Send error response for invalid message format
                error_msg = WebSocketMessage(
                    type=EventType.ERROR,
                    data={
                        "error": "Invalid message format",
                        "details": str(e)
                    }
                )
                await websocket.send_json(error_msg.dict())
                
            except json.JSONDecodeError:
                # Handle non-JSON messages
                error_msg = WebSocketMessage(
                    type=EventType.ERROR,
                    data={"error": "Message must be valid JSON"}
                )
                await websocket.send_json(error_msg.dict())
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
        await manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, user: User, message: WebSocketMessage):
    """Handle incoming WebSocket message based on type"""
    
    if message.type == EventType.MESSAGE:
        await handle_chat_message(websocket, user, message)
    
    elif message.type == EventType.TYPING:
        await handle_typing_indicator(websocket, user, message)
    
    elif message.type == EventType.PRESENCE:
        await handle_presence_update(websocket, user, message)
    
    elif message.type == EventType.HEARTBEAT:
        await manager.handle_heartbeat(websocket)
    
    elif message.type == EventType.SYSTEM:
        await handle_system_message(websocket, user, message)
    
    else:
        # Unknown message type
        error_msg = WebSocketMessage(
            type=EventType.ERROR,
            data={"error": f"Unknown message type: {message.type}"}
        )
        await websocket.send_json(error_msg.dict())


async def handle_chat_message(websocket: WebSocket, user: User, message: WebSocketMessage):
    """Handle chat message - integrate with LLM for responses"""
    try:
        chat_data = ChatMessage(**message.data)

        if chat_data.model:
            llm_manager.set_model(chat_data.model)
        
        if chat_data.streaming:
            # Handle streaming response
            response_msg = WebSocketMessage(
                type=EventType.MESSAGE,
                data={
                    "conversation_id": chat_data.conversation_id,
                    "content": "",
                    "streaming": True,
                    "status": "started",
                    "user_type": "assistant"
                }
            )
            await websocket.send_json(response_msg.dict())
            
            # Stream LLM response
            full_response = ""
            async for chunk in llm_manager.stream_completion(
                [Message("user", chat_data.content)]
            ):
                full_response += chunk
                
                chunk_msg = WebSocketMessage(
                    type=EventType.MESSAGE,
                    data={
                        "conversation_id": chat_data.conversation_id,
                        "content": chunk,
                        "streaming": True,
                        "status": "streaming",
                        "user_type": "assistant",
                        "full_content": full_response
                    }
                )
                await websocket.send_json(chunk_msg.dict())
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.05)
            
            # Send completion message
            completion_msg = WebSocketMessage(
                type=EventType.MESSAGE,
                data={
                    "conversation_id": chat_data.conversation_id,
                    "content": full_response,
                    "streaming": False,
                    "status": "completed",
                    "user_type": "assistant"
                }
            )
            await websocket.send_json(completion_msg.dict())
        
        else:
            # Handle non-streaming response
            response = await llm_manager.generate(chat_data.content)
            
            response_msg = WebSocketMessage(
                type=EventType.MESSAGE,
                data={
                    "conversation_id": chat_data.conversation_id,
                    "content": response,
                    "streaming": False,
                    "user_type": "assistant"
                }
            )
            await websocket.send_json(response_msg.dict())
    
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        error_msg = WebSocketMessage(
            type=EventType.ERROR,
            data={"error": f"Failed to process chat message: {str(e)}"}
        )
        await websocket.send_json(error_msg.dict())


async def handle_typing_indicator(websocket: WebSocket, user: User, message: WebSocketMessage):
    """Handle typing indicator"""
    try:
        typing_data = TypingIndicator(**message.data)
        conversation_id = typing_data.conversation_id or "default"
        
        await manager.update_typing_status(
            user.id, 
            conversation_id, 
            typing_data.is_typing
        )
        
    except Exception as e:
        logger.error(f"Error handling typing indicator: {e}")


async def handle_presence_update(websocket: WebSocket, user: User, message: WebSocketMessage):
    """Handle user presence update"""
    try:
        presence_data = PresenceUpdate(**message.data)
        manager.user_presence[user.id] = presence_data.status
        
        await manager.broadcast_presence_update(user.id, presence_data.status)
        
    except Exception as e:
        logger.error(f"Error handling presence update: {e}")


async def handle_system_message(websocket: WebSocket, user: User, message: WebSocketMessage):
    """Handle system message requests"""
    try:
        system_data = message.data
        command = system_data.get("command")
        
        if command == "get_online_users":
            online_users = manager.get_online_users()
            response_msg = WebSocketMessage(
                type=EventType.SYSTEM,
                data={
                    "command": "online_users_response",
                    "users": online_users
                }
            )
            await websocket.send_json(response_msg.dict())
        
        elif command == "ping":
            response_msg = WebSocketMessage(
                type=EventType.SYSTEM,
                data={
                    "command": "pong",
                    "server_time": time.time()
                }
            )
            await websocket.send_json(response_msg.dict())
        
        else:
            error_msg = WebSocketMessage(
                type=EventType.ERROR,
                data={"error": f"Unknown system command: {command}"}
            )
            await websocket.send_json(error_msg.dict())
            
    except Exception as e:
        logger.error(f"Error handling system message: {e}")


# REST endpoints for WebSocket management
@websocket_router.get("/status")
async def websocket_status():
    """Get WebSocket server status"""
    return {
        "status": "active",
        "connections": sum(len(conns) for conns in manager.active_connections.values()),
        "online_users": len(manager.user_presence),
        "typing_conversations": len(manager.typing_users),
        "features": ["chat", "typing", "presence", "notifications", "streaming"]
    }


@websocket_router.get("/online-users")
async def get_online_users(current_user: User = Depends(get_current_user)):
    """Get list of currently online users"""
    return {
        "online_users": manager.get_online_users(),
        "total_count": len(manager.get_online_users())
    }


@websocket_router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Broadcast message to all connected users (admin only)"""
    # Note: In production, add admin role check here
    
    broadcast_msg = WebSocketMessage(
        type=EventType.NOTIFICATION,
        data=message
    )
    
    await manager.broadcast_to_all(broadcast_msg.dict())
    
    return {
        "broadcasted": True,
        "message": "Message sent to all connected users",
        "recipient_count": len(manager.active_connections)
    }
