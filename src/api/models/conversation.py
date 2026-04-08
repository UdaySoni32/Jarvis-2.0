"""Conversation Models"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from .user import Base
import uuid


class ConversationHistory(Base):
    """Conversation history model"""
    __tablename__ = "conversation_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String, nullable=False, index=True)
    
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
