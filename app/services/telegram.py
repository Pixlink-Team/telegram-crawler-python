"""Telegram client management service."""

import logging
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
import base64

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, PasswordHashInvalidError, PhoneCodeInvalidError, SessionPasswordNeededError
from telethon.network.connection import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.tl.types import User

from app.config import settings
from app.services.mongodb import mongodb_service
from app.utils.session_manager import session_manager

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for managing multiple Telegram client sessions."""

    def __init__(self):
        self.clients: Dict[str, TelegramClient] = {}
        self._proxy = self._build_proxy()

    def _build_proxy(self):
        """Return proxy config tuple for MTProto if enabled."""
        if settings.use_mtproto_proxy and settings.mtproto_host and settings.mtproto_port and settings.mtproto_secret:
            # Convert base64 secret to hex if needed
            secret = settings.mtproto_secret
            try:
                # If it's base64, decode and convert to hex
                if len(secret) == 22 or len(secret) == 24:  # base64 encoded 16 bytes
                    secret_bytes = base64.b64decode(secret + "==")
                    secret = secret_bytes.hex()
                elif len(secret) != 32:  # not hex 16 bytes
                    # Try to decode as base64 anyway
                    secret_bytes = base64.b64decode(secret)
                    secret = secret_bytes.hex()
            except Exception as e:
                logger.warning(f"Could not convert MTProto secret, using as-is: {e}")
            
            return (settings.mtproto_host, int(settings.mtproto_port), secret)
        return None



    async def create_client(self, session_id: str, session_string: Optional[str] = None) -> TelegramClient:
        """Create a new Telegram client for a session."""
        # Use StringSession with optional existing session string
        string_session = StringSession(session_string) if session_string else StringSession()
        
        client_kwargs = {}
        if self._proxy:
            client_kwargs.update(
                connection=ConnectionTcpMTProxyRandomizedIntermediate,
                proxy=self._proxy,
            )

        client = TelegramClient(
            string_session,
            settings.telegram_api_id,
            settings.telegram_api_hash,
            **client_kwargs,
        )
        self.clients[session_id] = client
        logger.info(f"Created Telegram client for session: {session_id}")
        return client

    async def connect_client(self, session_id: str) -> TelegramClient:
        """Ensure a Telegram client exists and is connected."""
        if session_id not in self.clients:
            await self.create_client(session_id)

        client = self.clients[session_id]
        if not client.is_connected():
            await client.connect()
            logger.info(f"Connected Telegram client for session: {session_id}")
        return client

    async def request_qr_login(self, session_id: str) -> str:
        """Request a QR code login URL."""
        client = await self.connect_client(session_id)
        qr_login = await client.qr_login()
        client._qr_login = qr_login  # type: ignore[attr-defined]
        
        # Save initial session string to database
        session_string = client.session.save()
        await session_manager.update_session_string(session_id, session_string)
        
        logger.info(f"QR login requested for session: {session_id}")
        return qr_login.url

    async def send_code_request(self, session_id: str, phone: str) -> str:
        """Send code request for phone-based login."""
        client = await self.connect_client(session_id)
        result = await client.send_code_request(phone)
        client._phone_code_hash = result.phone_code_hash  # type: ignore[attr-defined]
        logger.info(f"Code request sent for session: {session_id}, phone: {phone}")
        return result.phone_code_hash

    async def verify_code(self, session_id: str, phone: str, code: str) -> Tuple[bool, Optional[User], bool]:
        """Verify phone code. Returns (success, user, requires_password)."""
        client = self.clients.get(session_id)
        if not client:
            raise ValueError("Session not found")

        try:
            phone_code_hash = getattr(client, "_phone_code_hash", None)
            if not phone_code_hash:
                raise ValueError("Phone code hash not found. Call send_code_request first.")

            user = await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Save session string after successful login
            session_string = client.session.save()
            await session_manager.update_session_string(session_id, session_string)
            
            logger.info(f"Signed in successfully for session: {session_id}")
            return True, user, False

        except SessionPasswordNeededError:
            logger.info(f"2FA password required for session: {session_id}")
            return True, None, True

        except PhoneCodeInvalidError:
            logger.error(f"Invalid phone code for session: {session_id}")
            return False, None, False

    async def verify_password(self, session_id: str, password: str) -> User:
        """Verify 2FA password."""
        client = self.clients.get(session_id)
        if not client:
            raise ValueError("Session not found")

        try:
            user = await client.sign_in(password=password)
            
            # Save session string after password verification
            session_string = client.session.save()
            await session_manager.update_session_string(session_id, session_string)
            
            logger.info(f"Signed in with password for session: {session_id}")
            return user
        except PasswordHashInvalidError:
            logger.error(f"Invalid password for session: {session_id}")
            raise ValueError("رمز عبور نامعتبر است")

    async def setup_message_handler(self, session_id: str, agent_id: Optional[int]):
        """Attach a message handler that saves inbound messages to MongoDB."""
        client = self.clients.get(session_id)
        if not client:
            raise ValueError("Session not found")

        @client.on(events.NewMessage)
        async def handle_new_message(event):  # pragma: no cover - runtime callback
            try:
                message = event.message
                sender = await event.get_sender()

                message_data = {
                    "id": message.id,
                    "from": {
                        "id": getattr(sender, "id", None),
                        "first_name": getattr(sender, "first_name", ""),
                        "last_name": getattr(sender, "last_name", None),
                        "username": getattr(sender, "username", None),
                        "phone": getattr(sender, "phone", None),
                    },
                    "chat": {
                        "id": message.chat_id,
                        "type": "private" if message.is_private else "group",
                    },
                    "text": message.text or "",
                    "date": message.date.isoformat(),
                    "reply_to_message_id": message.reply_to_msg_id,
                    "is_outgoing": False,
                }

                await mongodb_service.save_message(
                    session_id=session_id,
                    agent_id=agent_id or 0,
                    message_data=message_data,
                )

                await mongodb_service.save_event(
                    session_id=session_id,
                    agent_id=agent_id or 0,
                    event_type="message.received",
                    metadata={"message_id": message.id, "chat_id": message.chat_id},
                )

            except Exception as exc:
                logger.error(f"Error handling new message for session {session_id}: {exc}")

        logger.info(f"Message handler set for session: {session_id}")

    async def send_message(
        self, session_id: str, chat_id: int, message: str, reply_to: Optional[int] = None
    ) -> Tuple[int, datetime]:
        """Send a message and record it in MongoDB."""
        client = await self.connect_client(session_id)
        if not await client.is_user_authorized():
            raise ValueError("Session not authorized")

        session_record = await session_manager.get_session_by_id(session_id)
        if not session_record:
            raise ValueError("Session not found")

        agent_id = session_record.get("agent_id")

        try:
            sent_message = await client.send_message(chat_id, message, reply_to=reply_to)
            logger.info(f"Message sent for session: {session_id}, chat: {chat_id}")

            me = await client.get_me()
            message_data = {
                "id": sent_message.id,
                "from": {
                    "id": getattr(me, "id", None),
                    "first_name": getattr(me, "first_name", ""),
                    "last_name": getattr(me, "last_name", None),
                    "username": getattr(me, "username", None),
                    "phone": getattr(me, "phone", None),
                },
                "chat": {
                    "id": chat_id,
                    "type": "private",
                },
                "text": message,
                "date": sent_message.date.isoformat(),
                "reply_to_message_id": reply_to,
                "is_outgoing": True,
            }

            await mongodb_service.save_message(
                session_id=session_id,
                agent_id=agent_id or 0,
                message_data=message_data,
            )

            await mongodb_service.save_event(
                session_id=session_id,
                agent_id=agent_id or 0,
                event_type="message.sent",
                metadata={"message_id": sent_message.id, "chat_id": chat_id},
            )

            return sent_message.id, sent_message.date

        except FloodWaitError as exc:
            logger.error(f"FloodWaitError: need to wait {exc.seconds} seconds")
            raise ValueError(f"باید {exc.seconds} ثانیه صبر کنید")

    async def get_user_info(self, session_id: str) -> Optional[User]:
        """Return the current user info if connected."""
        client = self.clients.get(session_id)
        if not client or not client.is_connected():
            return None
        try:
            return await client.get_me()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Error getting user info for {session_id}: {exc}")
            return None

    async def disconnect_client(self, session_id: str):
        """Disconnect and remove a client."""
        client = self.clients.get(session_id)
        if client:
            if client.is_connected():
                await client.log_out()
                await client.disconnect()

            del self.clients[session_id]

        logger.info(f"Disconnected and cleaned up session: {session_id}")

    async def is_connected(self, session_id: str) -> bool:
        """Check if a session is connected and authorized."""
        client = self.clients.get(session_id)
        if not client:
            return False
        return client.is_connected() and await client.is_user_authorized()

    async def reconnect_client(self, session_id: str) -> bool:
        """Reconnect an existing session from database."""
        try:
            # Get session string from database
            session_record = await session_manager.get_session_by_id(session_id)
            if not session_record:
                logger.error(f"Session record not found: {session_id}")
                return False
            
            session_string = session_record.get("session_string")
            if not session_string:
                logger.error(f"Session string not found: {session_id}")
                return False

            client = await self.create_client(session_id, session_string)
            await client.connect()

            if await client.is_user_authorized():
                logger.info(f"Reconnected session: {session_id}")
                return True

            logger.error(f"Session not authorized: {session_id}")
            return False

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Error reconnecting session {session_id}: {exc}")
            return False


# Global instance
telegram_service = TelegramService()
