"""
Example client for testing Telegram Service API
"""
import httpx
import asyncio
import json
from typing import Optional


class TelegramServiceClient:
    """Client for Telegram Service API"""
    
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
    
    async def verify_code(self, session_id: str, code: str) -> dict:
        """Verify phone code"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/telegram/verify-code",
                json={
                    "session_id": session_id,
                    "code": code
                },
                headers=self.headers
            )
            return response.json()
    
    async def verify_password(self, session_id: str, password: str) -> dict:
        """Verify 2FA password"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/telegram/verify-password",
                json={
                    "session_id": session_id,
                    "password": password
                },
                headers=self.headers
            )
            return response.json()
    
    async def get_status(self, session_id: str) -> dict:
        """Get session status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/telegram/status/{session_id}",
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
    
    async def disconnect(self, session_id: str) -> dict:
        """Disconnect session"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/telegram/disconnect",
                json={"session_id": session_id},
                headers=self.headers
            )
            return response.json()


async def main():
    """Example usage"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    API_KEY = "your-api-secret-key"
    AGENT_ID = 123
    
    # Create client
    client = TelegramServiceClient(BASE_URL, API_KEY)
    
    print("🚀 Telegram Service Client Example")
    print("=" * 50)
    print()
    
    # Step 1: Request QR Code
    print("📱 Step 1: Requesting QR code...")
    qr_response = await client.request_qr(AGENT_ID)
    
    if qr_response.get("success"):
        session_id = qr_response["session_id"]
        print(f"✓ Session ID: {session_id}")
        print(f"✓ QR Code (base64): {qr_response['qr_code'][:50]}...")
        print(f"✓ Expires in: {qr_response['expires_in']} seconds")
        print()
        
        # You would display the QR code to the user here
        # They scan it with their Telegram app
        
        # Step 2: After QR scan or phone code entry
        print("📝 Step 2: Waiting for verification...")
        print("(In real scenario, user scans QR or enters code)")
        print()
        
        # If using phone code instead:
        # code = input("Enter verification code: ")
        # verify_response = await client.verify_code(session_id, code)
        # print(json.dumps(verify_response, indent=2))
        
        # Step 3: Check status
        print("📊 Step 3: Checking session status...")
        status = await client.get_status(session_id)
        print(json.dumps(status, indent=2))
        print()
        
        # Step 4: Send message (if connected)
        if status.get("connected"):
            print("💬 Step 4: Sending test message...")
            message_response = await client.send_message(
                session_id=session_id,
                chat_id=123456789,  # Replace with actual chat ID
                message="سلام، این یک پیام تست است"
            )
            print(json.dumps(message_response, indent=2))
            print()
        
        # Step 5: Disconnect (optional)
        # print("🔌 Step 5: Disconnecting...")
        # disconnect_response = await client.disconnect(session_id)
        # print(json.dumps(disconnect_response, indent=2))
    
    else:
        print("❌ Failed to request QR code")
        print(json.dumps(qr_response, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
