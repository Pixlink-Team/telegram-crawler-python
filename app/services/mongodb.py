"""
MongoDB service for storing messages and events
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for MongoDB operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.messages_collection: Optional[AsyncIOMotorCollection] = None
        self.sessions_collection: Optional[AsyncIOMotorCollection] = None
        self.events_collection: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_database]
            
            # Collections
            self.messages_collection = self.db["messages"]
            self.sessions_collection = self.db["telegram_sessions"]
            self.events_collection = self.db["events"]
            
            # Create indexes
            await self._create_indexes()
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise
    
    async def _create_indexes(self):
        """Create database indexes"""
        try:
            # Messages collection indexes
            await self.messages_collection.create_index([("session_id", ASCENDING)])
            await self.messages_collection.create_index([("agent_id", ASCENDING)])
            await self.messages_collection.create_index([("chat_id", ASCENDING)])
            await self.messages_collection.create_index([("message_id", ASCENDING)])
            await self.messages_collection.create_index([("date", DESCENDING)])
            
            # Sessions collection indexes
            await self.sessions_collection.create_index([("session_id", ASCENDING)], unique=True)
            await self.sessions_collection.create_index([("agent_id", ASCENDING)])
            
            # Events collection indexes
            await self.events_collection.create_index([("session_id", ASCENDING)])
            await self.events_collection.create_index([("event_type", ASCENDING)])
            await self.events_collection.create_index([("created_at", DESCENDING)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    # Message operations
    async def save_message(
        self,
        session_id: str,
        agent_id: int,
        message_data: Dict[str, Any]
    ) -> str:
        """Save a message to MongoDB"""
        try:
            document = {
                "session_id": session_id,
                "agent_id": agent_id,
                "message_id": message_data.get("id"),
                "chat_id": message_data.get("chat", {}).get("id"),
                "from_user": {
                    "id": message_data.get("from", {}).get("id"),
                    "first_name": message_data.get("from", {}).get("first_name"),
                    "last_name": message_data.get("from", {}).get("last_name"),
                    "username": message_data.get("from", {}).get("username"),
                    "phone": message_data.get("from", {}).get("phone"),
                },
                "chat": {
                    "id": message_data.get("chat", {}).get("id"),
                    "type": message_data.get("chat", {}).get("type"),
                },
                "text": message_data.get("text"),
                "date": message_data.get("date"),
                "reply_to_message_id": message_data.get("reply_to_message_id"),
                "created_at": datetime.utcnow(),
                "is_outgoing": message_data.get("is_outgoing", False),
            }
            
            result = await self.messages_collection.insert_one(document)
            logger.info(f"Message saved to MongoDB: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving message to MongoDB: {e}")
            raise
    
    async def get_messages(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from MongoDB"""
        try:
            query = {}
            if session_id:
                query["session_id"] = session_id
            if agent_id:
                query["agent_id"] = agent_id
            if chat_id:
                query["chat_id"] = chat_id
            
            cursor = self.messages_collection.find(query).sort("date", DESCENDING).skip(skip).limit(limit)
            messages = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for msg in messages:
                msg["_id"] = str(msg["_id"])
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages from MongoDB: {e}")
            return []
    
    async def get_chat_history(
        self,
        session_id: str,
        chat_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history for a specific chat"""
        return await self.get_messages(
            session_id=session_id,
            chat_id=chat_id,
            limit=limit
        )
    
    # Event operations
    async def save_event(
        self,
        session_id: str,
        agent_id: int,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save an event to MongoDB"""
        try:
            document = {
                "session_id": session_id,
                "agent_id": agent_id,
                "event_type": event_type,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
            }
            
            result = await self.events_collection.insert_one(document)
            logger.info(f"Event saved to MongoDB: {event_type}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving event to MongoDB: {e}")
            raise
    
    async def get_events(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events from MongoDB"""
        try:
            query = {}
            if session_id:
                query["session_id"] = session_id
            if agent_id:
                query["agent_id"] = agent_id
            if event_type:
                query["event_type"] = event_type
            
            cursor = self.events_collection.find(query).sort("created_at", DESCENDING).limit(limit)
            events = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for event in events:
                event["_id"] = str(event["_id"])
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events from MongoDB: {e}")
            return []
    
    # Statistics
    async def get_message_count(
        self,
        session_id: Optional[str] = None,
        agent_id: Optional[int] = None
    ) -> int:
        """Get message count"""
        try:
            query = {}
            if session_id:
                query["session_id"] = session_id
            if agent_id:
                query["agent_id"] = agent_id
            
            count = await self.messages_collection.count_documents(query)
            return count
            
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    async def get_agent_stats(self, agent_id: int) -> Dict[str, Any]:
        """Get statistics for an agent"""
        try:
            total_messages = await self.get_message_count(agent_id=agent_id)
            
            # Get recent messages
            recent_messages = await self.messages_collection.find(
                {"agent_id": agent_id}
            ).sort("date", DESCENDING).limit(10).to_list(length=10)
            
            # Get unique chats
            pipeline = [
                {"$match": {"agent_id": agent_id}},
                {"$group": {"_id": "$chat_id"}},
                {"$count": "total"}
            ]
            unique_chats = await self.messages_collection.aggregate(pipeline).to_list(length=1)
            unique_chats_count = unique_chats[0]["total"] if unique_chats else 0
            
            return {
                "agent_id": agent_id,
                "total_messages": total_messages,
                "unique_chats": unique_chats_count,
                "recent_messages_count": len(recent_messages),
            }
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {
                "agent_id": agent_id,
                "total_messages": 0,
                "unique_chats": 0,
                "recent_messages_count": 0,
            }


# Global instance
mongodb_service = MongoDBService()
