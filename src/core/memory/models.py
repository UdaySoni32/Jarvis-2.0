"""Memory system for conversation history and context management."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4

from ..logger import logger


class Message:
    """Represents a conversation message."""

    def __init__(
        self,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize message.

        Args:
            role: Message role (system/user/assistant/function)
            content: Message content
            message_id: Unique message ID
            timestamp: Message timestamp
            metadata: Additional metadata
        """
        self.role = role
        self.content = content
        self.message_id = message_id or str(uuid4())
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            message_id=data.get("message_id"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else None,
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return f"<Message role={self.role} id={self.message_id[:8]}>"


class ConversationSession:
    """Represents a conversation session."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize session.

        Args:
            session_id: Unique session ID
            title: Session title
            created_at: Creation timestamp
            updated_at: Last update timestamp
            metadata: Additional metadata
        """
        self.session_id = session_id or str(uuid4())
        self.title = title or f"Conversation {self.session_id[:8]}"
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
        self.messages: List[Message] = []

    def add_message(self, message: Message):
        """Add message to session."""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "message_count": len(self.messages),
        }

    def __repr__(self) -> str:
        return f"<Session id={self.session_id[:8]} messages={len(self.messages)}>"
