"""Pydantic Schemas for API"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Authentication
class UserBase(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str
    password: str

# Chat
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    model_used: str
    created_at: datetime

# Plugins
class PluginInfo(BaseModel):
    name: str
    version: str
    description: str
    enabled: bool

# System
class SystemStatus(BaseModel):
    status: str
    version: str
    uptime_seconds: int

__all__ = [
    "UserCreate", "UserResponse", "Token", "LoginRequest",
    "ChatRequest", "ChatResponse", 
    "PluginInfo", "SystemStatus"
]
