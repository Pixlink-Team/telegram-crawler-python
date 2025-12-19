"""
Webhook service for sending events to Laravel backend
"""
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import settings
from app.api.schemas import WebhookPayload, WebhookMessage, WebhookMessageFrom, WebhookMessageChat

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhooks to Laravel backend"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = settings.laravel_base_url
        self.secret_token = settings.webhook_secret_token
    
    async def send_webhook(self, agent_id: int, payload: WebhookPayload) -> bool:
        """Send webhook to Laravel backend"""
        url = f"{self.base_url}/api/webhooks/telegram/{agent_id}"
        headers = {
            "Authorization": f"Bearer {self.secret_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                url,
                json=payload.model_dump(mode='json', by_alias=True),
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook sent successfully to agent {agent_id}")
                return True
            else:
                logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook to agent {agent_id}: {e}")
            return False
    
    async def send_message_webhook(
        self,
        agent_id: int,
        session_id: str,
        event_type: str,
        message: Any,
        sender: Any
    ) -> bool:
        """Send message webhook"""
        try:
            # Build webhook message
            webhook_msg = WebhookMessage(
                id=message.id,
                **{
                    "from": WebhookMessageFrom(
                        id=sender.id,
                        first_name=sender.first_name or "",
                        last_name=sender.last_name,
                        username=sender.username,
                        phone=sender.phone
                    )
                },
                chat=WebhookMessageChat(
                    id=message.chat_id,
                    type="private" if message.is_private else "group"
                ),
                text=message.text or "",
                date=message.date.isoformat(),
                reply_to_message_id=message.reply_to_msg_id
            )
            
            payload = WebhookPayload(
                event=event_type,
                session_id=session_id,
                message=webhook_msg
            )
            
            return await self.send_webhook(agent_id, payload)
            
        except Exception as e:
            logger.error(f"Error creating message webhook: {e}")
            return False
    
    async def send_event_webhook(
        self,
        agent_id: int,
        session_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send event webhook (connection_lost, session_expired, etc.)"""
        payload = WebhookPayload(
            event=event_type,
            session_id=session_id,
            metadata=metadata
        )
        
        return await self.send_webhook(agent_id, payload)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
webhook_service = WebhookService()
