"""API v1 router."""

from fastapi import APIRouter

from .lamps import router as lamps_router
from .gateway import router as gateway_router
from .health import router as health_router
from .logs import router as logs_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router, tags=["health"])
api_router.include_router(lamps_router, prefix="/lamps", tags=["lamps"])
api_router.include_router(gateway_router, prefix="/gateway", tags=["gateway"])
api_router.include_router(logs_router, tags=["logs"])
