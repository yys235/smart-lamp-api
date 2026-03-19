"""Lamp service for controlling smart lamps."""

from typing import List, Optional

from loguru import logger

from app.models.lamp import Lamp, LampControlRequest
from app.services.gateway_service import GatewayService


class LampService:
    """Service for controlling smart lamps."""

    def __init__(self, gateway_service: GatewayService) -> None:
        self._gateway = gateway_service

    async def get_all_lamps(self) -> List[Lamp]:
        """Get all lamps with current state."""
        return await self._gateway.get_lamps()

    async def get_lamp(self, device_id: int) -> Optional[Lamp]:
        """Get a specific lamp by device ID."""
        lamps = await self._gateway.get_lamps()
        for lamp in lamps:
            if lamp.device_id == device_id:
                return lamp
        return None

    async def turn_on(
        self,
        device_id: Optional[int],
        request: LampControlRequest
    ) -> Optional[Lamp]:
        """Turn on lamp(s).

        Args:
            device_id: Device ID, or None/0 for all lamps
            request: Control request with RGB and intensity

        Returns:
            Updated lamp or None on failure
        """
        lamps = await self._gateway.get_lamps()

        if not lamps:
            logger.warning("No lamps available")
            return None

        # Update lamp(s)
        for lamp in lamps:
            if device_id is None or device_id == 0 or lamp.device_id == device_id:
                lamp.red = request.red
                lamp.green = request.green
                lamp.blue = request.blue
                lamp.intensity = request.intensity

        # Send update
        success = await self._gateway.update_lamps(lamps)

        if success:
            if device_id:
                return await self.get_lamp(device_id)
            return lamps[0] if lamps else None

        return None

    async def turn_off(self, device_id: Optional[int]) -> Optional[Lamp]:
        """Turn off lamp(s).

        Args:
            device_id: Device ID, or None/0 for all lamps

        Returns:
            Updated lamp or None on failure
        """
        lamps = await self._gateway.get_lamps()

        if not lamps:
            logger.warning("No lamps available")
            return None

        # Set intensity to 0
        for lamp in lamps:
            if device_id is None or device_id == 0 or lamp.device_id == device_id:
                lamp.intensity = 0

        # Send update
        success = await self._gateway.update_lamps(lamps)

        if success:
            if device_id:
                return await self.get_lamp(device_id)
            return lamps[0] if lamps else None

        return None

    async def turn_all_on(self, request: LampControlRequest) -> List[Lamp]:
        """Turn on all lamps."""
        await self.turn_on(None, request)
        return await self._gateway.get_lamps()

    async def turn_all_off(self) -> List[Lamp]:
        """Turn off all lamps."""
        await self.turn_off(None)
        return await self._gateway.get_lamps()
