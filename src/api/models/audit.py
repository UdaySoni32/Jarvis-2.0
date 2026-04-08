"""Audit Log Model"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from .user import Base
import uuid


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    method = Column(String(10), nullable=False)
    endpoint = Column(String(500), nullable=False)
    
    status_code = Column(Integer, nullable=False)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    duration_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
