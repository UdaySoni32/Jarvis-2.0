"""SQLite storage for conversation history."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..logger import logger
from .models import Message, ConversationSession


class ConversationStorage:
    """Manages conversation storage in SQLite."""

    def __init__(self, db_path: Path):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"Conversation storage initialized: {db_path}")

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """
            )

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at)"
            )

            conn.commit()

    def create_session(self, session: ConversationSession) -> bool:
        """
        Create a new session.

        Args:
            session: Session to create

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, title, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        session.session_id,
                        session.title,
                        session.created_at.isoformat(),
                        session.updated_at.isoformat(),
                        json.dumps(session.metadata),
                    ),
                )
                conn.commit()
            logger.info(f"Created session: {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                session = ConversationSession(
                    session_id=row["session_id"],
                    title=row["title"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )

                # Load messages
                messages = self.get_messages(session_id)
                session.messages = messages

                return session
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    def list_sessions(
        self, limit: int = 50, offset: int = 0
    ) -> List[ConversationSession]:
        """
        List sessions ordered by most recent.

        Args:
            limit: Maximum number of sessions
            offset: Offset for pagination

        Returns:
            List of sessions
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """,
                    (limit, offset),
                )

                sessions = []
                for row in cursor.fetchall():
                    session = ConversationSession(
                        session_id=row["session_id"],
                        title=row["title"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                    sessions.append(session)

                return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def update_session(self, session: ConversationSession) -> bool:
        """
        Update session.

        Args:
            session: Session to update

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE sessions
                    SET title = ?, updated_at = ?, metadata = ?
                    WHERE session_id = ?
                """,
                    (
                        session.title,
                        session.updated_at.isoformat(),
                        json.dumps(session.metadata),
                        session.session_id,
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session and all its messages.

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def add_message(self, session_id: str, message: Message) -> bool:
        """
        Add message to session.

        Args:
            session_id: Session ID
            message: Message to add

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO messages (message_id, session_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        message.message_id,
                        session_id,
                        message.role,
                        message.content,
                        message.timestamp.isoformat(),
                        json.dumps(message.metadata),
                    ),
                )

                # Update session timestamp
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (datetime.now().isoformat(), session_id),
                )

                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False

    def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages for session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages (most recent)

        Returns:
            List of messages
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                if limit:
                    cursor = conn.execute(
                        """
                        SELECT * FROM messages
                        WHERE session_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """,
                        (session_id, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM messages
                        WHERE session_id = ?
                        ORDER BY timestamp ASC
                    """,
                        (session_id,),
                    )

                messages = []
                for row in cursor.fetchall():
                    message = Message(
                        role=row["role"],
                        content=row["content"],
                        message_id=row["message_id"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                    messages.append(message)

                # Reverse if we limited (we want oldest first)
                if limit:
                    messages.reverse()

                return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    def search_messages(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search messages by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of message dicts with session info
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT m.*, s.title as session_title
                    FROM messages m
                    JOIN sessions s ON m.session_id = s.session_id
                    WHERE m.content LIKE ?
                    ORDER BY m.timestamp DESC
                    LIMIT ?
                """,
                    (f"%{query}%", limit),
                )

                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "message_id": row["message_id"],
                            "session_id": row["session_id"],
                            "session_title": row["session_title"],
                            "role": row["role"],
                            "content": row["content"],
                            "timestamp": row["timestamp"],
                        }
                    )

                return results
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []
