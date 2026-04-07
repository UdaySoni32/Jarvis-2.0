"""Enhanced memory manager with semantic search capabilities."""

from typing import List, Dict, Any, Optional
from ..logger import logger
from .manager import MemoryManager as BaseMemoryManager
from .models import Message
from .vector_store import get_vector_store


class SemanticMemoryManager(BaseMemoryManager):
    """Extended MemoryManager with semantic search capabilities."""
    
    def __init__(self, storage=None):
        """Initialize with vector store for semantic search."""
        super().__init__(storage)
        
        # Initialize vector store
        try:
            self.vector_store = get_vector_store()
            self.semantic_enabled = True
            logger.info("Semantic search enabled")
        except Exception as e:
            logger.warning(f"Semantic search disabled: {e}")
            self.vector_store = None
            self.semantic_enabled = False
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add message and store embedding."""
        message = super().add_message(role, content, metadata)
        
        # Add to vector store
        if self.semantic_enabled and self.current_session:
            try:
                self.vector_store.add_message(
                    message_id=message.message_id,
                    content=content,
                    session_id=self.current_session.session_id,
                    role=role,
                    timestamp=message.timestamp,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Failed to add to vector store: {e}")
        
        return message
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for semantically similar messages."""
        if not self.semantic_enabled:
            return []
        
        try:
            return self.vector_store.search_similar_messages(
                query=query,
                n_results=n_results,
                session_id=self.current_session.session_id if self.current_session else None
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def add_knowledge(self, knowledge_id: str, content: str, category: str = "general", importance: float = 0.5):
        """Add knowledge to long-term memory."""
        if not self.semantic_enabled:
            return False
        
        try:
            self.vector_store.add_knowledge(knowledge_id, content, category, importance)
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return False
    
    def search_knowledge(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base."""
        if not self.semantic_enabled:
            return []
        
        try:
            return self.vector_store.search_knowledge(query, n_results)
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    def get_semantic_context(self, query: str, max_messages: int = 5) -> List[Message]:
        """Get semantically relevant context."""
        if not self.semantic_enabled:
            return self.get_context_messages()
        
        try:
            similar = self.search_similar(query, max_messages)
            messages = []
            
            for item in similar:
                msg = Message(
                    role=item['metadata']['role'],
                    content=item['content'],
                    message_id=item['id']
                )
                messages.append(msg)
            
            return messages
        except:
            return self.get_context_messages()


# Create semantic memory manager instance
semantic_memory = SemanticMemoryManager()
