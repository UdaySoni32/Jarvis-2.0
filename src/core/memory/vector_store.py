"""
Vector database integration for semantic memory.

Uses ChromaDB for vector storage and sentence-transformers for embeddings.
Enables semantic search and long-term knowledge storage.
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector embeddings and semantic search.
    
    Uses ChromaDB for persistence and sentence-transformers for embeddings.
    Enables semantic memory: find similar conversations, concepts, and context.
    """
    
    def __init__(self, persist_directory: str = "user_data/vector_db"):
        """
        Initialize vector store.
        
        Args:
            persist_directory: Directory to store vector database
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with new persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )
        
        # Create or get collections
        self.conversations_collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Conversation message embeddings"}
        )
        
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge",
            metadata={"description": "Long-term knowledge and facts"}
        )
        
        # Initialize embedding model (using a lightweight model)
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded")
        
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        return self.embedding_model.encode(text).tolist()
    
    def add_message(
        self,
        message_id: str,
        content: str,
        session_id: str,
        role: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to the vector store.
        
        Args:
            message_id: Unique message identifier
            content: Message content
            session_id: Session identifier
            role: Message role (user/assistant)
            timestamp: Message timestamp
            metadata: Additional metadata
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(content)
            
            # Prepare metadata
            meta = {
                "session_id": session_id,
                "role": role,
                "timestamp": timestamp.isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            self.conversations_collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            
            logger.debug(f"Added message {message_id} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding message to vector store: {e}")
    
    def search_similar_messages(
        self,
        query: str,
        n_results: int = 5,
        session_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar messages.
        
        Args:
            query: Search query
            n_results: Number of results to return
            session_id: Optional filter by session
            role: Optional filter by role
            
        Returns:
            List of similar messages with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build filter
            where_filter = {}
            if session_id:
                where_filter["session_id"] = session_id
            if role:
                where_filter["role"] = role
            
            # Search
            results = self.conversations_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            # Format results
            similar_messages = []
            if results['ids'] and results['ids'][0]:
                for i, msg_id in enumerate(results['ids'][0]):
                    similar_messages.append({
                        "id": msg_id,
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            return similar_messages
            
        except Exception as e:
            logger.error(f"Error searching similar messages: {e}")
            return []
    
    def add_knowledge(
        self,
        knowledge_id: str,
        content: str,
        category: str,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a piece of knowledge to long-term memory.
        
        Args:
            knowledge_id: Unique knowledge identifier
            content: Knowledge content
            category: Knowledge category (fact, preference, skill, etc.)
            importance: Importance score (0.0 to 1.0)
            metadata: Additional metadata
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(content)
            
            # Prepare metadata
            meta = {
                "category": category,
                "importance": importance,
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            self.knowledge_collection.add(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            
            logger.info(f"Added knowledge: {knowledge_id} (category: {category})")
            
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
    
    def search_knowledge(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge.
        
        Args:
            query: Search query
            n_results: Number of results to return
            category: Optional filter by category
            min_importance: Minimum importance threshold
            
        Returns:
            List of relevant knowledge with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build filter
            where_filter = {}
            if category:
                where_filter["category"] = category
            
            # Search
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,  # Get more, filter later
                where=where_filter if where_filter else None
            )
            
            # Format and filter results
            knowledge_items = []
            if results['ids'] and results['ids'][0]:
                for i, k_id in enumerate(results['ids'][0]):
                    meta = results['metadatas'][0][i]
                    # Filter by importance
                    if meta.get('importance', 0) >= min_importance:
                        knowledge_items.append({
                            "id": k_id,
                            "content": results['documents'][0][i],
                            "metadata": meta,
                            "distance": results['distances'][0][i] if 'distances' in results else None
                        })
                    
                    # Stop if we have enough results
                    if len(knowledge_items) >= n_results:
                        break
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            conversations_count = self.conversations_collection.count()
            knowledge_count = self.knowledge_collection.count()
            
            return {
                "conversations_count": conversations_count,
                "knowledge_count": knowledge_count,
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dimensions": 384,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def delete_session_messages(self, session_id: str):
        """
        Delete all messages from a session.
        
        Args:
            session_id: Session identifier
        """
        try:
            self.conversations_collection.delete(
                where={"session_id": session_id}
            )
            logger.info(f"Deleted messages from session: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session messages: {e}")
    
    def clear_all(self):
        """Clear all data from vector store."""
        try:
            self.client.delete_collection("conversations")
            self.client.delete_collection("knowledge")
            
            # Recreate collections
            self.conversations_collection = self.client.create_collection("conversations")
            self.knowledge_collection = self.client.create_collection("knowledge")
            
            logger.info("Cleared all vector store data")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get the global vector store instance.
    
    Returns:
        VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
