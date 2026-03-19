"""Smart Lamp API - Main application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import api_router
from app.api.deps import get_gateway_service
from app.config import get_settings
from app.db.database import init_db
from app.logging_config import setup_logging

# Setup logging first
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()

    # Startup
    logger.info(f"Starting Smart Lamp API on {settings.host}:{settings.port}")
    logger.info(f"UDP Port: {settings.udp_port}, TCP Port: {settings.tcp_port}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Log retention: {settings.log_retention}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize gateway service
    gateway = await get_gateway_service()
    logger.info("Gateway service initialized")

    yield

    # Shutdown
    logger.info("Shutting down Smart Lamp API")
    await gateway.stop()
    logger.info("Gateway service stopped")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Smart Lamp API",
        description="REST API for controlling smart lamps via Ledo protocol",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": "Smart Lamp API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
