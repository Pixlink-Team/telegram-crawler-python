"""
Main FastAPI application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from app.services.mongodb import mongodb_service
from app.services.telegram import telegram_service
from app.utils.session_manager import session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting Telegram Service...")

    # Connect to MongoDB and initialize session manager
    try:
        await mongodb_service.connect()
        session_manager.set_mongodb_service(mongodb_service)
        logger.info("Connected to MongoDB and initialized session manager")
    except Exception as exc:
        logger.error(f"Failed to connect to MongoDB: {exc}")
        raise

    # Reconnect existing sessions
    try:
        active_sessions = await session_manager.get_all_active_sessions()
        logger.info(
            f"Found {len(active_sessions)} active sessions to reconnect")

        for session in active_sessions:
            session_id = session.get("session_id")
            agent_id = session.get("agent_id")
            if not session_id:
                continue

            try:
                success = await telegram_service.reconnect_client(session_id)
                if success:
                    logger.info(f"Reconnected session: {session_id}")
                    await telegram_service.setup_message_handler(
                        session_id=session_id,
                        agent_id=agent_id,
                    )
                else:
                    logger.warning(
                        f"Failed to reconnect session: {session_id}")
                    await session_manager.deactivate_session(session_id)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(f"Error reconnecting session {session_id}: {exc}")
                await session_manager.deactivate_session(session_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"Error during startup reconnection: {exc}")

    logger.info("Telegram Service started successfully")

    # Application is running
    yield

    # Shutdown sequence
    logger.info("Shutting down Telegram Service...")

    # Disconnect Telegram clients
    for session_id, client in list(telegram_service.clients.items()):
        try:
            if client.is_connected():
                await client.disconnect()
            logger.info(f"Disconnected session: {session_id}")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Error disconnecting session {session_id}: {exc}")

    # Disconnect from MongoDB
    try:
        await mongodb_service.disconnect()
        logger.info("Disconnected from MongoDB")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"Error disconnecting from MongoDB: {exc}")

    logger.info("Telegram Service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Telegram Service API",
    description="A Python service for managing Telegram connections and messages",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (allow all origins for simplicity; tighten if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "Telegram Service", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    active_sessions = len(telegram_service.clients)
    return {"status": "healthy", "active_sessions": active_sessions}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
