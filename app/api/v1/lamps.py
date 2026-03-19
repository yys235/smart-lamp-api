"""Lamp control endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.deps import get_lamp_service, verify_api_key
from app.models.lamp import Lamp, LampControlRequest
from app.models.response import ApiResponse
from app.services.lamp_service import LampService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse,
    summary="Get all lamps",
    description="Get status of all lamps connected to the gateway"
)
async def get_all_lamps(
    lamp_service: LampService = Depends(get_lamp_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Get all lamps status."""
    lamps = await lamp_service.get_all_lamps()
    return ApiResponse.success({
        "lamps": [lamp.model_dump() for lamp in lamps],
        "count": len(lamps)
    })


@router.get(
    "/{device_id}",
    response_model=ApiResponse,
    summary="Get lamp by ID",
    description="Get status of a specific lamp"
)
async def get_lamp(
    device_id: int = Path(..., description="Device ID", ge=1),
    lamp_service: LampService = Depends(get_lamp_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Get specific lamp status."""
    lamp = await lamp_service.get_lamp(device_id)

    if not lamp:
        raise HTTPException(status_code=404, detail=f"Lamp {device_id} not found")

    return ApiResponse.success(lamp.model_dump())


@router.post(
    "/{device_id}/on",
    response_model=ApiResponse,
    summary="Turn on lamp",
    description="Turn on a specific lamp with optional RGB and intensity"
)
async def turn_on_lamp(
    device_id: int = Path(..., description="Device ID", ge=1),
    request: LampControlRequest = LampControlRequest(),
    lamp_service: LampService = Depends(get_lamp_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Turn on a specific lamp."""
    lamp = await lamp_service.turn_on(device_id, request)

    if not lamp:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to turn on lamp {device_id}"
        )

    return ApiResponse.success(lamp.model_dump(), "Lamp turned on")


@router.post(
    "/{device_id}/off",
    response_model=ApiResponse,
    summary="Turn off lamp",
    description="Turn off a specific lamp"
)
async def turn_off_lamp(
    device_id: int = Path(..., description="Device ID", ge=1),
    lamp_service: LampService = Depends(get_lamp_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Turn off a specific lamp."""
    lamp = await lamp_service.turn_off(device_id)

    if not lamp:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to turn off lamp {device_id}"
        )

    return ApiResponse.success(lamp.model_dump(), "Lamp turned off")


@router.post(
    "/all/on",
    response_model=ApiResponse,
    summary="Turn on all lamps",
    description="Turn on all lamps with optional RGB and intensity"
)
async def turn_on_all_lamps(
    request: LampControlRequest = LampControlRequest(),
    lamp_service: LampService = Depends(get_lamp_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Turn on all lamps."""
    lamps = await lamp_service.turn_all_on(request)

    return ApiResponse.success({
        "lamps": [lamp.model_dump() for lamp in lamps],
        "count": len(lamps)
    }, "All lamps turned on")


@router.post(
    "/all/off",
    response_model=ApiResponse,
    summary="Turn off all lamps",
    description="Turn off all lamps"
)
async def turn_off_all_lamps(
    lamp_service: LampService = Depends(get_lamp_service),
    _: bool = Depends(verify_api_key)
) -> ApiResponse:
    """Turn off all lamps."""
    lamps = await lamp_service.turn_all_off()

    return ApiResponse.success({
        "lamps": [lamp.model_dump() for lamp in lamps],
        "count": len(lamps)
    }, "All lamps turned off")
