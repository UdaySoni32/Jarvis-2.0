"""Memory manager for conversation context and history."""

from typing import List, Optional, Dict, Any
from pathlib import Path

from ..logger import logger
from ..config import settings
from .models import Message, ConversationSession
from .storage import ConversationStorage


class MemoryManager:
    """Manages conversation memory and context."""

    def __init__(self, storage: Optional[ConversationStorage] = None):
        """
        Initialize memory manager.

        Args:
            storage: Storage backend (creates default if None)
        """
        if storage is None:
            db_path = settings.user_data_dir / "conversations.db"
            storage = ConversationStorage(db_path)

        self.storage = storage
        self.current_session: Optional[ConversationSession] = None
        self.max_context_messages = settings.max_context_messages
        logger.info("Memory manager initialized")

    def start_session(
        self, title: Optional[str] = None, session_id: Optional[str] = None
    ) -> ConversationSession:
        """
        Start a new conversation session.

        Args:
            title: Optional session title
            session_id: Optional session ID (for resuming)

        Returns:
            New or resumed session
        """
        if session_id:
            # Try to resume existing session
            session = self.storage.get_session(session_id)
            if session:
                self.current_session = session
                logger.info(f"Resumed session: {session_id}")
                return session

        # Create new session
        session = ConversationSession(title=title)
        self.storage.create_session(session)
        self.current_session = session
        logger.info(f"Started new session: {session.session_id}")
        return session

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add message to current session.

        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata

        Returns:
            Created message
        """
        if not self.current_session:
            self.start_session()

        message = Message(role=role, content=content, metadata=metadata)
        self.current_session.add_message(message)
        self.storage.add_message(self.current_session.session_id, message)

        logger.debug(f"Added message: {role} ({len(content)} chars)")
        return message

    def get_context_messages(
        self, max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get recent messages for LLM context.

        Args:
            max_messages: Maximum messages (uses default if None)

        Returns:
            List of message dicts for LLM (role, content)
        """
        if not self.current_session:
            return []

        max_msg = max_messages or self.max_context_messages
        messages = self.current_session.messages[-max_msg:]

        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get current session summary.

        Returns:
            Session summary dict
        """
        if not self.current_session:
            return {"active": False}

        return {
            "active": True,
            "session_id": self.current_session.session_id,
            "title": self.current_session.title,
            "message_count": len(self.current_session.messages),
            "created_at": self.current_session.created_at.isoformat(),
            "updated_at": self.current_session.updated_at.isoformat(),
        }

    def list_sessions(self, limit: int = 50) -> List[ConversationSession]:
        """
        List recent sessions.

        Args:
            limit: Maximum sessions

        Returns:
            List of sessions
        """
        return self.storage.list_sessions(limit=limit)

    def load_session(self, session_id: str) -> bool:
        """
        Load and set as current session.

        Args:
            session_id: Session ID to load

        Returns:
            True if successful
        """
        session = self.storage.get_session(session_id)
        if session:
            self.current_session = session
            logger.info(f"Loaded session: {session_id}")
            return True
        return False

    def end_session(self):
        """End current session."""
        if self.current_session:
            logger.info(f"Ended session: {self.current_session.session_id}")
            self.current_session = None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session = None
        return self.storage.delete_session(session_id)

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search messages across all sessions.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Search results
        """
        return self.storage.search_messages(query, limit=limit)

    def update_session_title(self, title: str) -> bool:
        """
        Update current session title.

        Args:
            title: New title

        Returns:
            True if successful
        """
        if not self.current_session:
            return False

        self.current_session.title = title
        return self.storage.update_session(self.current_session)


# Global memory manager instance
memory_manager = MemoryManager()
