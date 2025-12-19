"""
Session manager utility for database operations
"""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.config import settings
from app.models.session import Base, TelegramSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manager for database session operations"""
    
    def __init__(self):
        self.engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            return db
        except Exception:
            db.close()
            raise
    
    def create_session(self, agent_id: int, session_id: str, session_file: str) -> TelegramSession:
        """Create a new session record"""
        db = self.get_db()
        try:
            session = TelegramSession(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                session_id=session_id,
                session_file=session_file,
                is_active=False,
                metadata={}
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"Created session record for session_id: {session_id}")
            return session
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating session: {e}")
            raise
        finally:
            db.close()
    
    def get_session_by_id(self, session_id: str) -> Optional[TelegramSession]:
        """Get session by session_id"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.session_id == session_id
            ).first()
            return session
        finally:
            db.close()
    
    def get_session_by_agent(self, agent_id: int) -> Optional[TelegramSession]:
        """Get active session by agent_id"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.agent_id == agent_id,
                TelegramSession.is_active == True
            ).first()
            return session
        finally:
            db.close()
    
    def get_all_active_sessions(self) -> List[TelegramSession]:
        """Get all active sessions"""
        db = self.get_db()
        try:
            sessions = db.query(TelegramSession).filter(
                TelegramSession.is_active == True
            ).all()
            return sessions
        finally:
            db.close()
    
    def update_session_connected(
        self,
        session_id: str,
        phone: str,
        user_id: int,
        is_active: bool = True
    ) -> Optional[TelegramSession]:
        """Update session after successful connection"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.session_id == session_id
            ).first()
            
            if session:
                session.phone = phone
                session.user_id = user_id
                session.is_active = is_active
                session.connected_at = datetime.utcnow()
                session.last_activity = datetime.utcnow()
                db.commit()
                db.refresh(session)
                logger.info(f"Updated session {session_id} as connected")
                return session
            return None
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating session: {e}")
            raise
        finally:
            db.close()
    
    def update_session_phone(self, session_id: str, phone: str) -> Optional[TelegramSession]:
        """Update session phone number"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.session_id == session_id
            ).first()
            
            if session:
                session.phone = phone
                db.commit()
                db.refresh(session)
                logger.info(f"Updated phone for session {session_id}")
                return session
            return None
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating session phone: {e}")
            raise
        finally:
            db.close()
    
    def update_session_activity(self, session_id: str) -> Optional[TelegramSession]:
        """Update last activity timestamp"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.session_id == session_id
            ).first()
            
            if session:
                session.last_activity = datetime.utcnow()
                db.commit()
                db.refresh(session)
                return session
            return None
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating session activity: {e}")
            raise
        finally:
            db.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session record"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.session_id == session_id
            ).first()
            
            if session:
                db.delete(session)
                db.commit()
                logger.info(f"Deleted session record: {session_id}")
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting session: {e}")
            raise
        finally:
            db.close()
    
    def deactivate_session(self, session_id: str) -> Optional[TelegramSession]:
        """Deactivate a session"""
        db = self.get_db()
        try:
            session = db.query(TelegramSession).filter(
                TelegramSession.session_id == session_id
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
                db.refresh(session)
                logger.info(f"Deactivated session: {session_id}")
                return session
            return None
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deactivating session: {e}")
            raise
        finally:
            db.close()


# Global instance
session_manager = SessionManager()
