"""Gateway status endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_gateway_service, verify_api_key
from app.models.response import ApiResponse
from app.services.gateway_service import GatewayService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse,
    summary="Get gateway status",
    description="Get current gateway connection status"
)
async def get_gateway_status(
    gateway: GatewayService = Depends(get_gateway_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Get gateway status."""
    status = gateway.get_status()
    return ApiResponse.success(status)
