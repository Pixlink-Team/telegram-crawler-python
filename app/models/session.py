"""
Database models for Telegram sessions
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class TelegramSession(Base):
    """Model for storing Telegram session information"""
    
    __tablename__ = "telegram_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=True)
    user_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    session_file = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<TelegramSession(session_id='{self.session_id}', agent_id={self.agent_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "phone": self.phone,
            "user_id": self.user_id,
            "is_active": self.is_active,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "session_file": self.session_file,
            "metadata": self.metadata
        }
