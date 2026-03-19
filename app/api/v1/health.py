"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.deps import get_gateway_service, verify_api_key
from app.models.response import ApiResponse
from app.services.gateway_service import GatewayService

router = APIRouter()


@router.get(
    "/health",
    response_model=ApiResponse,
    summary="Health check",
    description="Check service health status"
)
async def health_check(
    gateway: GatewayService = Depends(get_gateway_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Health check endpoint."""
    status = gateway.get_status()

    return ApiResponse.success({
        "status": "healthy" if status["connected"] else "degraded",
        "gateway_connected": status["connected"],
        "lamp_count": status["lamp_count"],
        "all_off": status["all_off"],
        "last_communication": status["last_communication"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
