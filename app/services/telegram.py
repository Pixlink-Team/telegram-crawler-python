"""
Telegram client management service
"""
import asyncio
import logging
from typing import Dict, Optional, Tuple
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PasswordHashInvalidError,
    FloodWaitError
)
from telethon.tl.types import User
from datetime import datetime
import os

from app.config import settings
from app.services.webhook import WebhookService

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for managing multiple Telegram client sessions"""
    
    def __init__(self):
        self.clients: Dict[str, TelegramClient] = {}
        self.webhook_service = WebhookService()
        self._ensure_session_directory()
    
    def _ensure_session_directory(self):
        """Ensure session directory exists"""
        if not os.path.exists(settings.session_directory):
            os.makedirs(settings.session_directory)
    
    def _get_session_file_path(self, session_id: str) -> str:
        """Get full path for session file"""
        return os.path.join(settings.session_directory, f"{session_id}")
    
    async def create_client(self, session_id: str) -> TelegramClient:
        """Create a new Telegram client"""
        session_file = self._get_session_file_path(session_id)
        
        client = TelegramClient(
            session_file,
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        
        self.clients[session_id] = client
        logger.info(f"Created new Telegram client for session: {session_id}")
        
        return client
    
    async def connect_client(self, session_id: str) -> TelegramClient:
        """Connect to Telegram"""
        if session_id not in self.clients:
            await self.create_client(session_id)
        
        client = self.clients[session_id]
        
        if not client.is_connected():
            await client.connect()
            logger.info(f"Connected client for session: {session_id}")
        
        return client
    
    async def request_qr_login(self, session_id: str) -> bytes:
        """Request QR code login"""
        client = await self.connect_client(session_id)
        
        # Request QR code
        qr_login = await client.qr_login()
        
        # Store QR login object for later use
        if not hasattr(client, '_qr_login'):
            client._qr_login = qr_login
        
        logger.info(f"QR code requested for session: {session_id}")
        
        # Return the URL for QR code generation
        return qr_login.url
    
    async def send_code_request(self, session_id: str, phone: str) -> str:
        """Send code request for phone login"""
        client = await self.connect_client(session_id)
        
        result = await client.send_code_request(phone)
        
        # Store phone hash for verification
        if not hasattr(client, '_phone_code_hash'):
            client._phone_code_hash = result.phone_code_hash
        
        logger.info(f"Code request sent for session: {session_id}, phone: {phone}")
        
        return result.phone_code_hash
    
    async def verify_code(self, session_id: str, phone: str, code: str) -> Tuple[bool, Optional[User], bool]:
        """
        Verify phone code
        Returns: (success, user, requires_password)
        """
        client = self.clients.get(session_id)
        if not client:
            raise ValueError("Session not found")
        
        try:
            phone_code_hash = getattr(client, '_phone_code_hash', None)
            if not phone_code_hash:
                raise ValueError("Phone code hash not found. Call send_code_request first.")
            
            user = await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            logger.info(f"Successfully signed in for session: {session_id}")
            
            return True, user, False
            
        except SessionPasswordNeededError:
            logger.info(f"2FA password required for session: {session_id}")
            return True, None, True
            
        except PhoneCodeInvalidError:
            logger.error(f"Invalid phone code for session: {session_id}")
            return False, None, False
    
    async def verify_password(self, session_id: str, password: str) -> User:
        """Verify 2FA password"""
        client = self.clients.get(session_id)
        if not client:
            raise ValueError("Session not found")
        
        try:
            user = await client.sign_in(password=password)
            logger.info(f"Successfully signed in with password for session: {session_id}")
            return user
            
        except PasswordHashInvalidError:
            logger.error(f"Invalid password for session: {session_id}")
            raise ValueError("رمز عبور نامعتبر است")
    
    async def setup_message_handler(self, session_id: str, agent_id: int):
        """Setup message handler for a client"""
        client = self.clients.get(session_id)
        if not client:
            raise ValueError("Session not found")
        
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            """Handle new messages"""
            try:
                message = event.message
                sender = await event.get_sender()
                
                # Send webhook to Laravel
                await self.webhook_service.send_message_webhook(
                    agent_id=agent_id,
                    session_id=session_id,
                    event_type="new_message",
                    message=message,
                    sender=sender
                )
                
            except Exception as e:
                logger.error(f"Error handling new message: {e}")
        
        logger.info(f"Message handler setup for session: {session_id}")
    
    async def send_message(self, session_id: str, chat_id: int, message: str, reply_to: Optional[int] = None) -> Tuple[int, datetime]:
        """Send a message"""
        client = self.clients.get(session_id)
        if not client or not client.is_connected():
            raise ValueError("Session not found or not connected")
        
        try:
            sent_message = await client.send_message(
                chat_id,
                message,
                reply_to=reply_to
            )
            
            logger.info(f"Message sent for session: {session_id}, chat: {chat_id}")
            
            return sent_message.id, sent_message.date
            
        except FloodWaitError as e:
            logger.error(f"FloodWaitError: need to wait {e.seconds} seconds")
            raise ValueError(f"باید {e.seconds} ثانیه صبر کنید")
    
    async def get_user_info(self, session_id: str) -> Optional[User]:
        """Get current user information"""
        client = self.clients.get(session_id)
        if not client or not client.is_connected():
            return None
        
        try:
            me = await client.get_me()
            return me
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def disconnect_client(self, session_id: str):
        """Disconnect and remove a client"""
        client = self.clients.get(session_id)
        if client:
            if client.is_connected():
                await client.log_out()
                await client.disconnect()
            
            # Remove from active clients
            del self.clients[session_id]
            
            # Remove session file
            session_file = self._get_session_file_path(session_id)
            if os.path.exists(f"{session_file}.session"):
                os.remove(f"{session_file}.session")
            
            logger.info(f"Disconnected and removed session: {session_id}")
    
    async def is_connected(self, session_id: str) -> bool:
        """Check if a session is connected"""
        client = self.clients.get(session_id)
        if not client:
            return False
        
        return client.is_connected() and await client.is_user_authorized()
    
    async def reconnect_client(self, session_id: str) -> bool:
        """Reconnect an existing session"""
        try:
            session_file = self._get_session_file_path(session_id)
            
            if not os.path.exists(f"{session_file}.session"):
                logger.error(f"Session file not found: {session_id}")
                return False
            
            client = await self.create_client(session_id)
            await client.connect()
            
            if await client.is_user_authorized():
                logger.info(f"Successfully reconnected session: {session_id}")
                return True
            else:
                logger.error(f"Session not authorized: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error reconnecting session {session_id}: {e}")
            return False


# Global instance
telegram_service = TelegramService()
