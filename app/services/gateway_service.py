"""Gateway service for managing gateway connection."""

import asyncio
from typing import Callable, List, Optional

from loguru import logger

from app.config import get_settings
from app.models.lamp import Lamp
from app.protocols.tcp_client import TcpClient
from app.protocols.udp_client import UdpClient


class GatewayService:
    """Service for managing smart lamp gateway connection."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.udp_client = UdpClient()
        self.tcp_client = TcpClient()
        self._lamps: List[Lamp] = []
        self._on_lamps_updated: Optional[Callable] = None

    @property
    def gateway_ip(self) -> Optional[str]:
        """Get gateway IP address."""
        return self.udp_client.gateway_ip

    @property
    def gateway_id(self) -> Optional[int]:
        """Get gateway ID."""
        return self.udp_client.gateway_id

    @property
    def is_connected(self) -> bool:
        """Check if gateway is connected."""
        return self.udp_client.is_connected

    @property
    def lamps(self) -> List[Lamp]:
        """Get current lamp list."""
        return self._lamps.copy()

    @property
    def last_communication(self) -> Optional[str]:
        """Get last communication time."""
        return self.tcp_client.last_communication

    @property
    def all_off(self) -> bool:
        """Check if all lamps are off."""
        return all(lamp.intensity == 0 for lamp in self._lamps)

    def on_lamps_updated(self, callback: Callable) -> None:
        """Set callback for lamp updates."""
        self._on_lamps_updated = callback

    async def start(self) -> None:
        """Start gateway service."""
        # Set up callbacks
        self.udp_client.on_gateway_discovered(self._on_gateway_discovered)
        self.udp_client.on_lamp_state_changed(self._refresh_lamps)

        # Start UDP discovery
        await self.udp_client.start()
        logger.info("Gateway service started")

    async def stop(self) -> None:
        """Stop gateway service."""
        await self.udp_client.stop()
        logger.info("Gateway service stopped")

    async def _on_gateway_discovered(self, ip: str, gateway_id: int) -> None:
        """Handle gateway discovery event."""
        logger.info(f"Gateway discovered at {ip} (ID: {gateway_id})")
        await self._refresh_lamps()

    async def _refresh_lamps(self) -> None:
        """Refresh lamp list from gateway."""
        if not self.is_connected:
            return

        lamps = await self.tcp_client.get_lamps(
            self.gateway_ip,
            self.gateway_id
        )

        if lamps:
            self._lamps = lamps
            logger.info(f"Refreshed {len(lamps)} lamps")

            if self._on_lamps_updated:
                await self._on_lamps_updated(self._lamps)

    async def discover(self, timeout: float = 5.0) -> Optional[dict]:
        """Actively discover gateway.

        Args:
            timeout: Maximum time to wait for discovery in seconds

        Returns:
            Discovery result dict or None
        """
        return await self.udp_client.discover_gateway(timeout)

    async def get_lamps(self) -> List[Lamp]:
        """Get all lamps (refreshed)."""
        if not self.is_connected:
            return []

        lamps = await self.tcp_client.get_lamps(
            self.gateway_ip,
            self.gateway_id
        )

        if lamps:
            self._lamps = lamps

        return self._lamps.copy()

    async def update_lamps(self, lamps: List[Lamp]) -> bool:
        """Update lamp states on gateway."""
        if not self.is_connected:
            logger.warning("Gateway not connected")
            return False

        success = await self.tcp_client.update_lamps(
            self.gateway_ip,
            lamps
        )

        if success:
            # Verify update
            await asyncio.sleep(0.5)
            updated = await self.get_lamps()

            # Check if update was applied
            for lamp in lamps:
                for updated_lamp in updated:
                    if lamp.device_id == updated_lamp.device_id:
                        if lamp.intensity != updated_lamp.intensity:
                            # Retry once
                            logger.info(f"Retrying update for lamp {lamp.device_id}")
                            await self.tcp_client.update_lamps(
                                self.gateway_ip,
                                lamps
                            )
                        break

        return success

    def get_status(self) -> dict:
        """Get gateway status."""
        return {
            "connected": self.is_connected,
            "gateway_ip": self.gateway_ip,
            "gateway_id": self.gateway_id,
            "lamp_count": len(self._lamps),
            "all_off": self.all_off,
            "last_communication": self.last_communication,
        }
