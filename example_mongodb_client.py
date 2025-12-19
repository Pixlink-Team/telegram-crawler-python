"""
Example client for testing MongoDB integration
"""
import httpx
import asyncio
import json
from typing import Optional


class TelegramServiceClient:
    """Client for Telegram Service API with MongoDB"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    async def request_qr(self, agent_id: int) -> dict:
        """Request QR code for login"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/telegram/request-qr",
                json={"agent_id": agent_id},
                headers=self.headers
            )
            return response.json()
    
    async def send_message(
        self,
        session_id: str,
        chat_id: int,
        message: str,
        reply_to: Optional[int] = None
    ) -> dict:
        """Send a message"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/telegram/send-message",
                json={
                    "session_id": session_id,
                    "chat_id": chat_id,
                    "message": message,
                    "reply_to": reply_to
                },
                headers=self.headers
            )
            return response.json()
    
    async def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> dict:
        """Get messages from MongoDB"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/telegram/messages/{session_id}?limit={limit}&skip={skip}",
                headers=self.headers
            )
            return response.json()
    
    async def get_chat_history(
        self,
        session_id: str,
        chat_id: int,
        limit: int = 50
    ) -> dict:
        """Get chat history for a specific chat"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/telegram/chat-history/{session_id}/{chat_id}?limit={limit}",
                headers=self.headers
            )
            return response.json()
    
    async def get_agent_stats(self, agent_id: int) -> dict:
        """Get statistics for an agent"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/telegram/agent-stats/{agent_id}",
                headers=self.headers
            )
            return response.json()
    
    async def get_events(self, session_id: str, limit: int = 100) -> dict:
        """Get events for a session"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/telegram/events/{session_id}?limit={limit}",
                headers=self.headers
            )
            return response.json()


async def main():
    """Example usage with MongoDB"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    API_KEY = "your-api-secret-key"
    AGENT_ID = 123
    SESSION_ID = "your-session-id"  # Replace with actual session ID
    CHAT_ID = 123456789  # Replace with actual chat ID
    
    # Create client
    client = TelegramServiceClient(BASE_URL, API_KEY)
    
    print("🚀 Telegram Service MongoDB Example")
    print("=" * 50)
    print()
    
    # Example 1: Get all messages for a session
    print("📨 Example 1: Getting messages from MongoDB...")
    messages_response = await client.get_messages(SESSION_ID, limit=10)
    
    if messages_response.get("success"):
        print(f"✓ Found {messages_response['count']} messages")
        for msg in messages_response['messages'][:3]:  # Show first 3
            print(f"  - [{msg['date']}] {msg['from_user']['first_name']}: {msg['text'][:50]}...")
        print()
    
    # Example 2: Get chat history
    print("💬 Example 2: Getting chat history...")
    chat_response = await client.get_chat_history(SESSION_ID, CHAT_ID, limit=20)
    
    if chat_response.get("success"):
        print(f"✓ Found {chat_response['count']} messages in chat {CHAT_ID}")
        print()
    
    # Example 3: Get agent statistics
    print("📊 Example 3: Getting agent statistics...")
    stats_response = await client.get_agent_stats(AGENT_ID)
    
    if stats_response.get("success"):
        stats = stats_response['stats']
        print(f"✓ Agent {AGENT_ID} Statistics:")
        print(f"  - Total messages: {stats['total_messages']}")
        print(f"  - Unique chats: {stats['unique_chats']}")
        print(f"  - Recent messages: {stats['recent_messages_count']}")
        print()
    
    # Example 4: Get events
    print("📋 Example 4: Getting events...")
    events_response = await client.get_events(SESSION_ID, limit=5)
    
    if events_response.get("success"):
        print(f"✓ Found {events_response['count']} events")
        for event in events_response['events'][:3]:  # Show first 3
            print(f"  - [{event['created_at']}] {event['event_type']}")
        print()
    
    # Example 5: Send a message (will be saved to MongoDB automatically)
    print("✉️ Example 5: Sending a message (saves to MongoDB)...")
    send_response = await client.send_message(
        session_id=SESSION_ID,
        chat_id=CHAT_ID,
        message="این یک پیام تست است که در MongoDB ذخیره می‌شود"
    )
    
    if send_response.get("success"):
        print(f"✓ Message sent and saved!")
        print(f"  - Message ID: {send_response['message_id']}")
        print()
    
    print("=" * 50)
    print("✅ All examples completed!")
    print()
    print("💡 Tips:")
    print("  - همه پیام‌ها خودکار در MongoDB ذخیره می‌شوند")
    print("  - می‌توانید با MongoDB Compass پیام‌ها را مشاهده کنید")
    print("  - از API endpoints برای دریافت و آنالیز داده‌ها استفاده کنید")


if __name__ == "__main__":
    asyncio.run(main())
