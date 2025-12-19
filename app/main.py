"""
Main FastAPI application
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import router
from app.services.telegram import telegram_service
from app.utils.session_manager import session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Telegram Service...")
    
    # Reconnect existing sessions
    try:
        active_sessions = session_manager.get_all_active_sessions()
        logger.info(f"Found {len(active_sessions)} active sessions to reconnect")
        
        for session in active_sessions:
            try:
                success = await telegram_service.reconnect_client(session.session_id)
                if success:
                    logger.info(f"Reconnected session: {session.session_id}")
                    # Setup message handler
                    await telegram_service.setup_message_handler(
                        session_id=session.session_id,
                        agent_id=session.agent_id
                    )
                else:
                    logger.warning(f"Failed to reconnect session: {session.session_id}")
                    session_manager.deactivate_session(session.session_id)
            except Exception as e:
                logger.error(f"Error reconnecting session {session.session_id}: {e}")
                session_manager.deactivate_session(session.session_id)
    except Exception as e:
        logger.error(f"Error during startup reconnection: {e}")
    
    logger.info("Telegram Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Telegram Service...")
    
    # Disconnect all clients gracefully
    for session_id in list(telegram_service.clients.keys()):
        try:
            client = telegram_service.clients[session_id]
            if client.is_connected():
                await client.disconnect()
            logger.info(f"Disconnected session: {session_id}")
        except Exception as e:
            logger.error(f"Error disconnecting session {session_id}: {e}")
    
    logger.info("Telegram Service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Telegram Service API",
    description="A Python service for managing Telegram connections and messages",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Telegram Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    active_sessions = len(telegram_service.clients)
    return {
        "status": "healthy",
        "active_sessions": active_sessions
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
