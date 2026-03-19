"""API dependencies."""

from functools import lru_cache
from typing import Optional

from fastapi import Depends, Header, HTTPException

from app.config import get_settings
from app.services.gateway_service import GatewayService
from app.services.lamp_service import LampService
from app.models.response import ApiResponse

# Singleton services
_gateway_service: Optional[GatewayService] = None
_lamp_service: Optional[LampService] = None


async def get_gateway_service() -> GatewayService:
    """Get gateway service instance."""
    global _gateway_service
    if _gateway_service is None:
        _gateway_service = GatewayService()
        await _gateway_service.start()
    return _gateway_service


async def get_lamp_service(
    gateway: GatewayService = Depends(get_gateway_service)
) -> LampService:
    """Get lamp service instance."""
    global _lamp_service
    if _lamp_service is None:
        _lamp_service = LampService(gateway)
    return _lamp_service


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> bool:
    """Verify API key if configured."""
    settings = get_settings()

    # If no API key configured, allow all requests
    if not settings.api_key:
        return True

    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

    return True
