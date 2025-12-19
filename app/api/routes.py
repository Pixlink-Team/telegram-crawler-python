"""
API routes for Telegram service
"""
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import uuid

from app.api.schemas import (
    RequestQRRequest,
    RequestPhoneCodeRequest,
    QRCodeResponse,
    PhoneCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
    VerifyPasswordRequest,
    VerifyPasswordResponse,
    DisconnectRequest,
    DisconnectResponse,
    StatusResponse,
    SendMessageRequest,
    SendMessageResponse,
    ErrorResponse
)
from app.services.telegram import telegram_service
from app.services.mongodb import mongodb_service
from app.utils.qr_generator import generate_qr_code
from app.utils.session_manager import session_manager
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key"""
    if x_api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.post("/request-qr", response_model=QRCodeResponse)
async def request_qr(
    request: RequestQRRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Request QR code for Telegram login
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session record
        session_file = f"{session_id}"
        session_record = await session_manager.create_session(
            agent_id=request.agent_id,
            session_id=session_id,
            session_file=session_file
        )
        
        # Request QR code from Telegram
        qr_url = await telegram_service.request_qr_login(session_id)
        
        # Generate QR code image
        qr_code_base64 = generate_qr_code(qr_url)
        
        logger.info(f"QR code generated for agent {request.agent_id}")
        
        return QRCodeResponse(
            success=True,
            session_id=session_id,
            qr_code=qr_code_base64,
            expires_in=settings.qr_code_expires_in
        )
        
    except Exception as e:
        logger.error(f"Error requesting QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request-phone-code", response_model=PhoneCodeResponse)
async def request_phone_code(
    request: RequestPhoneCodeRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Request phone code for Telegram login
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session record with phone
        session_file = f"{session_id}"
        session_record = await session_manager.create_session(
            agent_id=request.agent_id,
            session_id=session_id,
            session_file=session_file
        )
        
        # Update session with phone number using proper method
        await session_manager.update_session_phone(session_id, request.phone)
        
        # Request code from Telegram
        await telegram_service.send_code_request(session_id, request.phone)
        
        logger.info(f"Phone code requested for agent {request.agent_id}, phone: {request.phone}")
        
        return PhoneCodeResponse(
            success=True,
            session_id=session_id,
            phone=request.phone,
            message="کد تایید به تلگرام شما ارسال شد"
        )
        
    except Exception as e:
        logger.error(f"Error requesting phone code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Verify phone code from Telegram
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Get session record
        session_record = await session_manager.get_session_by_id(request.session_id)
        if not session_record:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # We need phone number - this should be provided in request
        # For now, we'll assume it's stored in metadata
        phone = session_record.get("phone")
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number not found. Use send_code_request first.")
        
        # Verify code
        success, user, requires_password = await telegram_service.verify_code(
            session_id=request.session_id,
            phone=phone,
            code=request.code
        )
        
        if not success:
            return VerifyCodeResponse(
                success=False,
                connected=False,
                error="کد نامعتبر است"
            )
        
        if requires_password:
            return VerifyCodeResponse(
                success=True,
                connected=False,
                requires_password=True
            )
        
        # Update session record
        await session_manager.update_session_connected(
            session_id=request.session_id,
            phone=user.phone or phone,
            user_id=user.id,
            is_active=True
        )
        
        # Setup message handler
        await telegram_service.setup_message_handler(
            session_id=request.session_id,
            agent_id=session_record["agent_id"]
        )
        
        logger.info(f"Code verified successfully for session {request.session_id}")
        
        return VerifyCodeResponse(
            success=True,
            connected=True,
            phone=user.phone or phone,
            user_id=user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-password", response_model=VerifyPasswordResponse)
async def verify_password(
    request: VerifyPasswordRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Verify 2FA password
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Get session record
        session_record = await session_manager.get_session_by_id(request.session_id)
        if not session_record:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify password
        user = await telegram_service.verify_password(
            session_id=request.session_id,
            password=request.password
        )
        
        # Update session record
        await session_manager.update_session_connected(
            session_id=request.session_id,
            phone=user.phone,
            user_id=user.id,
            is_active=True
        )
        
        # Setup message handler
        await telegram_service.setup_message_handler(
            session_id=request.session_id,
            agent_id=session_record["agent_id"]
        )
        
        logger.info(f"Password verified successfully for session {request.session_id}")
        
        return VerifyPasswordResponse(
            success=True,
            connected=True,
            phone=user.phone,
            user_id=user.id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect(
    request: DisconnectRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Disconnect and remove session
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Disconnect client
        await telegram_service.disconnect_client(request.session_id)
        
        # Delete session record
        await session_manager.delete_session(request.session_id)
        
        logger.info(f"Session disconnected: {request.session_id}")
        
        return DisconnectResponse(
            success=True,
            message="اتصال با موفقیت قطع شد"
        )
        
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(
    session_id: str,
    x_api_key: Optional[str] = Header(None)
):
    """
    Get session status
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Get session record
        session_record = await session_manager.get_session_by_id(session_id)
        if not session_record:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if connected
        is_connected = await telegram_service.is_connected(session_id)
        
        # Update activity
        if is_connected:
            await session_manager.update_session_activity(session_id)
        
        return StatusResponse(
            success=True,
            connected=is_connected and session_record.get("is_active"),
            phone=session_record.get("phone"),
            user_id=session_record.get("user_id"),
            last_activity=session_record.get("last_activity").isoformat() if session_record.get("last_activity") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Send message via Telegram
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        # Get session record
        session_record = await session_manager.get_session_by_id(request.session_id)
        if not session_record:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Send message
        message_id, sent_at = await telegram_service.send_message(
            session_id=request.session_id,
            chat_id=request.chat_id,
            message=request.message,
            reply_to=request.reply_to
        )
        
        # Update activity
        await session_manager.update_session_activity(request.session_id)
        
        logger.info(f"Message sent for session {request.session_id}")
        
        return SendMessageResponse(
            success=True,
            message_id=message_id,
            sent_at=sent_at.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{session_id}")
async def get_messages(
    session_id: str,
    limit: int = 100,
    skip: int = 0,
    x_api_key: Optional[str] = Header(None)
):
    """
    Get messages for a session from MongoDB
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        messages = await mongodb_service.get_messages(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        return {
            "success": True,
            "count": len(messages),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat-history/{session_id}/{chat_id}")
async def get_chat_history(
    session_id: str,
    chat_id: int,
    limit: int = 50,
    x_api_key: Optional[str] = Header(None)
):
    """
    Get chat history for a specific chat
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        messages = await mongodb_service.get_chat_history(
            session_id=session_id,
            chat_id=chat_id,
            limit=limit
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "chat_id": chat_id,
            "count": len(messages),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-stats/{agent_id}")
async def get_agent_stats(
    agent_id: int,
    x_api_key: Optional[str] = Header(None)
):
    """
    Get statistics for an agent
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        stats = await mongodb_service.get_agent_stats(agent_id)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{session_id}")
async def get_events(
    session_id: str,
    limit: int = 100,
    x_api_key: Optional[str] = Header(None)
):
    """
    Get events for a session
    """
    try:
        # Verify API key
        verify_api_key(x_api_key)
        
        events = await mongodb_service.get_events(
            session_id=session_id,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(events),
            "events": events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
