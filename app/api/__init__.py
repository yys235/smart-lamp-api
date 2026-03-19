"""API package."""

from .deps import get_gateway_service, get_lamp_service
from .v1.router import api_router

__all__ = ["api_router", "get_gateway_service", "get_lamp_service"]
