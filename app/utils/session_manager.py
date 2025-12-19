"""
Session manager utility for MongoDB operations
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class SessionManager:
    """Manager for session operations in MongoDB"""
    
    def __init__(self):
        self.db = None
        self.collection = None
    
    def set_mongodb_service(self, mongodb_service):
        """Set MongoDB service instance"""
        self.db = mongodb_service.db
        self.collection = mongodb_service.sessions_collection
    
    async def create_session(self, agent_id: int, session_id: str, session_file: str) -> Dict[str, Any]:
        """Create a new session record"""
        try:
            session = {
                "_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "session_id": session_id,
                "session_file": session_file,
                "session_string": None,  # Will be updated after login
                "phone": None,
                "user_id": None,
                "is_active": False,
                "connected_at": None,
                "last_activity": datetime.utcnow(),
                "metadata": {},
                "created_at": datetime.utcnow(),
            }
            
            await self.collection.insert_one(session)
            logger.info(f"Created session record for session_id: {session_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by session_id"""
        try:
            session = await self.collection.find_one({"session_id": session_id})
            return session
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def get_session_by_agent(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get active session by agent_id"""
        try:
            session = await self.collection.find_one({
                "agent_id": agent_id,
                "is_active": True
            })
            return session
        except Exception as e:
            logger.error(f"Error getting session by agent: {e}")
            return None
    
    async def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        try:
            cursor = self.collection.find({"is_active": True})
            sessions = await cursor.to_list(length=None)
            return sessions
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    async def update_session_connected(
        self,
        session_id: str,
        phone: str,
        user_id: int,
        is_active: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Update session after successful connection"""
        try:
            result = await self.collection.find_one_and_update(
                {"session_id": session_id},
                {
                    "$set": {
                        "phone": phone,
                        "user_id": user_id,
                        "is_active": is_active,
                        "connected_at": datetime.utcnow(),
                        "last_activity": datetime.utcnow(),
                    }
                },
                return_document=True
            )
            
            if result:
                logger.info(f"Updated session {session_id} as connected")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            raise
    
    async def update_session_phone(self, session_id: str, phone: str) -> Optional[Dict[str, Any]]:
        """Update session phone number"""
        try:
            result = await self.collection.find_one_and_update(
                {"session_id": session_id},
                {"$set": {"phone": phone}},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated phone for session {session_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error updating session phone: {e}")
            raise
    
    async def update_session_string(self, session_id: str, session_string: str) -> Optional[Dict[str, Any]]:
        """Update session string in database"""
        try:
            result = await self.collection.find_one_and_update(
                {"session_id": session_id},
                {"$set": {"session_string": session_string}},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated session string for session {session_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error updating session string: {e}")
            raise
    
    async def update_session_activity(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Update last activity timestamp"""
        try:
            result = await self.collection.find_one_and_update(
                {"session_id": session_id},
                {"$set": {"last_activity": datetime.utcnow()}},
                return_document=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session record"""
        try:
            result = await self.collection.delete_one({"session_id": session_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted session record: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            raise
    
    async def deactivate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Deactivate a session"""
        try:
            result = await self.collection.find_one_and_update(
                {"session_id": session_id},
                {"$set": {"is_active": False}},
                return_document=True
            )
            
            if result:
                logger.info(f"Deactivated session: {session_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error deactivating session: {e}")
            raise


# Global instance
session_manager = SessionManager()
