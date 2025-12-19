"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# Request Schemas
class RequestQRRequest(BaseModel):
    """Request schema for QR code generation"""
    agent_id: int = Field(..., description="Agent ID")


class VerifyCodeRequest(BaseModel):
    """Request schema for code verification"""
    session_id: str = Field(..., description="Session ID")
    code: str = Field(..., description="Verification code from Telegram")


class VerifyPasswordRequest(BaseModel):
    """Request schema for password verification (2FA)"""
    session_id: str = Field(..., description="Session ID")
    password: str = Field(..., description="2FA password")


class DisconnectRequest(BaseModel):
    """Request schema for disconnection"""
    session_id: str = Field(..., description="Session ID")


class SendMessageRequest(BaseModel):
    """Request schema for sending a message"""
    session_id: str = Field(..., description="Session ID")
    chat_id: int = Field(..., description="Chat ID to send message to")
    message: str = Field(..., description="Message text")
    reply_to: Optional[int] = Field(None, description="Message ID to reply to")


# Response Schemas
class QRCodeResponse(BaseModel):
    """Response schema for QR code generation"""
    success: bool
    session_id: str
    qr_code: str = Field(..., description="Base64 encoded QR code image")
    expires_in: int = Field(..., description="Expiration time in seconds")


class VerifyCodeResponse(BaseModel):
    """Response schema for code verification"""
    success: bool
    connected: bool
    phone: Optional[str] = None
    user_id: Optional[int] = None
    requires_password: Optional[bool] = None


class VerifyPasswordResponse(BaseModel):
    """Response schema for password verification"""
    success: bool
    connected: bool
    phone: str
    user_id: int


class DisconnectResponse(BaseModel):
    """Response schema for disconnection"""
    success: bool
    message: str


class StatusResponse(BaseModel):
    """Response schema for status check"""
    success: bool
    connected: bool
    phone: Optional[str] = None
    user_id: Optional[int] = None
    last_activity: Optional[str] = None


class SendMessageResponse(BaseModel):
    """Response schema for sending a message"""
    success: bool
    message_id: int
    sent_at: str


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    success: bool = False
    error: str


# Webhook Schemas
class WebhookMessageFrom(BaseModel):
    """Webhook message sender information"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None


class WebhookMessageChat(BaseModel):
    """Webhook message chat information"""
    id: int
    type: str


class WebhookMessage(BaseModel):
    """Webhook message information"""
    id: int
    from_: WebhookMessageFrom = Field(..., alias="from")
    chat: WebhookMessageChat
    text: str
    date: str
    reply_to_message_id: Optional[int] = None
    
    class Config:
        populate_by_name = True


class WebhookPayload(BaseModel):
    """Webhook payload schema"""
    event: str = Field(..., description="Event type: new_message, message_edited, session_expired, connection_lost, connection_restored")
    session_id: str
    message: Optional[WebhookMessage] = None
    metadata: Optional[Dict[str, Any]] = None
