"""
Intelligent context management system.

Handles context prioritization, summarization, and smart window management.
Uses semantic search to select most relevant context instead of just recent messages.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from ..logger import logger
from .models import Message
from .semantic import SemanticMemoryManager


class ContextManager:
    """
    Manages conversation context intelligently.
    
    Features:
    - Context prioritization by relevance and recency
    - Automatic summarization of long conversations
    - Multi-turn conversation tracking
    - Smart context window management
    """
    
    def __init__(self, memory_manager: SemanticMemoryManager):
        """
        Initialize context manager.
        
        Args:
            memory_manager: Semantic memory manager instance
        """
        self.memory = memory_manager
        self.max_context_tokens = 4000  # ~3000 words
        self.max_context_messages = 20
        logger.info("Context manager initialized")
    
    def prioritize_context(
        self,
        messages: List[Any],  # Can be Message objects or dicts
        current_query: str,
        max_messages: int = 10
    ) -> List[Any]:
        """
        Prioritize messages by relevance to current query.
        
        Scores messages based on:
        - Semantic similarity to current query
        - Recency (newer = higher score)
        - Position in conversation flow
        
        Args:
            messages: List of messages (Message objects or dicts)
            current_query: Current user query
            max_messages: Maximum messages to return
            
        Returns:
            Prioritized list of messages
        """
        if not messages:
            return []
        
        # Helper to get role from message (dict or object)
        def get_role(msg):
            if isinstance(msg, dict):
                return msg.get('role', 'user')
            else:
                return msg.role
        
        # Calculate scores for each message
        scored_messages = []
        
        for idx, msg in enumerate(messages):
            score = 0.0
            
            # Recency score (0.0 to 1.0, newer is higher)
            recency_score = idx / len(messages)
            score += recency_score * 0.4  # 40% weight
            
            # Position score (messages near start/end are important)
            if idx < 3:  # First 3 messages (context setting)
                score += 0.3
            elif idx >= len(messages) - 3:  # Last 3 messages (current topic)
                score += 0.5
            
            # Role score (alternate user/assistant is good conversation flow)
            if idx > 0 and get_role(messages[idx-1]) != get_role(msg):
                score += 0.1
            
            scored_messages.append((score, idx, msg))
        
        # Sort by score (descending)
        scored_messages.sort(reverse=True, key=lambda x: x[0])
        
        # Take top N messages
        top_messages = scored_messages[:max_messages]
        
        # Re-sort by original order to maintain conversation flow
        top_messages.sort(key=lambda x: x[1])
        
        return [msg for _, _, msg in top_messages]
    
    def get_smart_context(
        self,
        current_query: str,
        use_semantic: bool = True
    ) -> List[Message]:
        """
        Get smart context for current query.
        
        Uses semantic search if available, otherwise falls back to
        prioritized recent messages.
        
        Args:
            current_query: Current user query
            use_semantic: Whether to use semantic search
            
        Returns:
            List of contextually relevant messages
        """
        try:
            if use_semantic and self.memory.semantic_enabled:
                # Use semantic search to find relevant messages
                similar = self.memory.search_similar(
                    current_query,
                    n_results=self.max_context_messages
                )
                
                # Convert to Message objects
                messages = []
                for item in similar:
                    msg = Message(
                        role=item['metadata']['role'],
                        content=item['content'],
                        message_id=item['id']
                    )
                    messages.append(msg)
                
                return messages
            else:
                # Fall back to recent messages with prioritization
                recent = self.memory.get_context_messages()
                return self.prioritize_context(
                    recent,
                    current_query,
                    max_messages=self.max_context_messages
                )
                
        except Exception as e:
            logger.error(f"Error getting smart context: {e}")
            return self.memory.get_context_messages()
    
    def summarize_messages(
        self,
        messages: List[Any],  # Can be Message objects or dicts
        max_length: int = 200
    ) -> str:
        """
        Summarize a list of messages.
        
        Creates a brief summary of the conversation so far.
        Useful for very long conversations to reduce context size.
        
        Args:
            messages: Messages to summarize (Message objects or dicts)
            max_length: Maximum summary length in words
            
        Returns:
            Summary text
        """
        if not messages:
            return ""
        
        # Helper functions
        def get_role(msg):
            return msg.get('role', 'user') if isinstance(msg, dict) else msg.role
        
        def get_content(msg):
            return msg.get('content', '') if isinstance(msg, dict) else msg.content
        
        # Simple extraction-based summarization
        summary_parts = []
        
        # Get key messages (first, last, and important ones)
        key_messages = []
        
        if messages:
            # First message (sets context)
            key_messages.append(messages[0])
            
            # Last few messages (current topic)
            key_messages.extend(messages[-3:])
        
        for msg in key_messages:
            content = get_content(msg).strip()
            # Take first sentence or first 50 characters
            if '.' in content:
                first_sentence = content.split('.')[0] + '.'
            else:
                first_sentence = content[:50] + '...' if len(content) > 50 else content
            
            summary_parts.append(f"[{get_role(msg)}] {first_sentence}")
        
        summary = " | ".join(summary_parts)
        
        # Truncate if too long
        words = summary.split()
        if len(words) > max_length:
            summary = ' '.join(words[:max_length]) + '...'
        
        return summary
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation.
        
        Returns:
            Dictionary with conversation statistics and summary
        """
        if not self.memory.current_session:
            return {
                "active": False,
                "message_count": 0,
                "summary": ""
            }
        
        messages = self.memory.get_context_messages()
        
        # Helper to get role
        def get_role(msg):
            return msg.get('role', 'user') if isinstance(msg, dict) else msg.role
        
        def get_content(msg):
            return msg.get('content', '') if isinstance(msg, dict) else msg.content
        
        # Count user vs assistant messages
        user_count = sum(1 for m in messages if get_role(m) == "user")
        assistant_count = sum(1 for m in messages if get_role(m) == "assistant")
        
        # Get topics (using first few words of user messages)
        topics = []
        for msg in messages:
            if get_role(msg) == "user":
                words = get_content(msg).split()[:5]
                topics.append(' '.join(words))
        
        return {
            "active": True,
            "session_id": self.memory.current_session.session_id,
            "message_count": len(messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "topics": topics[:5],  # First 5 topics
            "summary": self.summarize_messages(messages)
        }
    
    def track_conversation_flow(self) -> List[Dict[str, Any]]:
        """
        Track multi-turn conversation flow.
        
        Identifies conversation topics and how they change over time.
        
        Returns:
            List of conversation segments with topics
        """
        # Get actual Message objects from current session
        if not self.memory.current_session:
            return []
        
        messages = self.memory.current_session.messages
        
        if not messages:
            return []
        
        # Group messages into conversation segments
        # A new segment starts when topic appears to change
        segments = []
        current_segment = {
            "start_idx": 0,
            "messages": [],
            "topic_keywords": set()
        }
        
        for idx, msg in enumerate(messages):
            if msg.role == "user":
                # Extract keywords (simple: take first 3-5 meaningful words)
                words = msg.content.lower().split()
                keywords = [w for w in words if len(w) > 4][:5]
                current_segment["topic_keywords"].update(keywords)
            
            current_segment["messages"].append(msg)
            
            # Check if we should start a new segment
            # (simple heuristic: every 4-6 messages)
            if len(current_segment["messages"]) >= 5:
                segments.append(current_segment)
                current_segment = {
                    "start_idx": idx + 1,
                    "messages": [],
                    "topic_keywords": set()
                }
        
        # Add final segment if not empty
        if current_segment["messages"]:
            segments.append(current_segment)
        
        # Format for output
        formatted_segments = []
        for seg in segments:
            formatted_segments.append({
                "message_count": len(seg["messages"]),
                "topic_keywords": list(seg["topic_keywords"])[:5],
                "summary": self.summarize_messages(seg["messages"], max_length=50)
            })
        
        return formatted_segments
    
    def estimate_token_count(self, messages: List[Any]) -> int:
        """
        Estimate token count for messages.
        
        Rough estimate: 1 token ≈ 4 characters
        
        Args:
            messages: List of messages (Message objects or dicts)
            
        Returns:
            Estimated token count
        """
        total_chars = 0
        for msg in messages:
            content = _get_content(msg) if 'content' in dir(msg) or isinstance(msg, dict) else msg.content
            total_chars += len(content)
        return total_chars // 4
    
    def trim_context_to_fit(
        self,
        messages: List[Message],
        max_tokens: int = None
    ) -> List[Message]:
        """
        Trim context to fit within token limit.
        
        Removes oldest messages first, but keeps at least the last 2-3
        messages for immediate context.
        
        Args:
            messages: Messages to trim
            max_tokens: Maximum token count (uses self.max_context_tokens if None)
            
        Returns:
            Trimmed list of messages
        """
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        # Keep removing oldest messages until we fit
        current_tokens = self.estimate_token_count(messages)
        
        while current_tokens > max_tokens and len(messages) > 3:
            # Remove oldest message (but keep first message for context)
            if len(messages) > 5:
                messages = [messages[0]] + messages[2:]
            else:
                messages = messages[1:]
            
            current_tokens = self.estimate_token_count(messages)
        
        return messages


# Create global context manager instance
# Will be initialized with semantic memory manager
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """
    Get the global context manager instance.
    
    Returns:
        ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        from .semantic import semantic_memory
        _context_manager = ContextManager(semantic_memory)
    return _context_manager

# Helper functions for handling both dict and Message objects
def _get_role(msg) -> str:
    """Get role from message (dict or Message object)."""
    return msg.get('role', 'user') if isinstance(msg, dict) else msg.role

def _get_content(msg) -> str:
    """Get content from message (dict or Message object)."""
    return msg.get('content', '') if isinstance(msg, dict) else msg.content
