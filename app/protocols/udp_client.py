"""UDP client for gateway discovery."""

import asyncio
import socket
from typing import Callable, Optional

from loguru import logger

from app.config import get_settings
from app.protocols.ledo_protocol import LedoProtocol


class UdpClient:
    """UDP client for receiving gateway broadcast messages."""

    # Discovery broadcast message (based on protocol analysis)
    DISCOVERY_MESSAGE = bytes([
        0xF3, 0xD4,  # Magic bytes
        0xFF, 0xFF, 0xFF, 0xFF,  # Broadcast
        0x00, 0x00,  # Reserved
        0x00,  # Command (discovery)
        0x00,  # Length
        0x00, 0x00, 0x00, 0x00,  # Data
        0x00,  # Checksum
    ])

    def __init__(self) -> None:
        self.settings = get_settings()
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._gateway_ip: Optional[str] = None
        self._gateway_id: Optional[int] = None
        self._on_gateway_discovered: Optional[Callable] = None
        self._on_lamp_state_changed: Optional[Callable] = None
        self._removed_devices: int = 0
        self._added_devices: int = 0
        self._discovery_event: Optional[asyncio.Event] = None

    @property
    def gateway_ip(self) -> Optional[str]:
        """Get discovered gateway IP."""
        return self._gateway_ip

    @property
    def gateway_id(self) -> Optional[int]:
        """Get discovered gateway ID."""
        return self._gateway_id

    @property
    def is_connected(self) -> bool:
        """Check if gateway has been discovered."""
        return self._gateway_ip is not None

    def on_gateway_discovered(self, callback: Callable) -> None:
        """Set callback for gateway discovery event."""
        self._on_gateway_discovered = callback

    def on_lamp_state_changed(self, callback: Callable) -> None:
        """Set callback for lamp state change event."""
        self._on_lamp_state_changed = callback

    async def start(self) -> None:
        """Start UDP listener."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(("0.0.0.0", self.settings.udp_port))
            self._socket.setblocking(False)

            self._running = True
            logger.info(f"UDP client started on port {self.settings.udp_port}")

            # Start listening task
            asyncio.create_task(self._listen_loop())

        except Exception as e:
            logger.error(f"Failed to start UDP client: {e}")
            raise

    async def stop(self) -> None:
        """Stop UDP listener."""
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None
        logger.info("UDP client stopped")

    async def discover_gateway(self, timeout: float = 5.0) -> Optional[dict]:
        """Actively discover gateway by sending broadcast.

        Args:
            timeout: Maximum time to wait for gateway response in seconds

        Returns:
            Dict with gateway_ip and gateway_id if found, None otherwise
        """
        if self._gateway_ip:
            # Already discovered
            return {
                "gateway_ip": self._gateway_ip,
                "gateway_id": self._gateway_id,
            }

        if not self._running:
            logger.warning("UDP client not running, cannot discover")
            return None

        # Create discovery event
        self._discovery_event = asyncio.Event()

        # Send broadcast discovery message
        try:
            broadcast_addr = "255.255.255.255"
            self._socket.sendto(
                self.DISCOVERY_MESSAGE,
                (broadcast_addr, self.settings.udp_port)
            )
            logger.info(f"Sent discovery broadcast to {broadcast_addr}:{self.settings.udp_port}")

            # Wait for discovery event or timeout
            try:
                await asyncio.wait_for(
                    self._discovery_event.wait(),
                    timeout=timeout
                )
                return {
                    "gateway_ip": self._gateway_ip,
                    "gateway_id": self._gateway_id,
                }
            except asyncio.TimeoutError:
                logger.warning(f"Gateway discovery timeout after {timeout}s")
                return None

        except Exception as e:
            logger.error(f"Discovery broadcast failed: {e}")
            return None
        finally:
            self._discovery_event = None

    async def _listen_loop(self) -> None:
        """Main UDP listening loop."""
        loop = asyncio.get_event_loop()

        while self._running and self._socket:
            try:
                data, addr = await loop.sock_recvfrom(
                    self._socket,
                    self.settings.udp_buffer_size
                )

                await self._process_packet(data, addr[0])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"UDP receive error: {e}")
                await asyncio.sleep(0.1)

    async def _process_packet(self, data: bytes, source_ip: str) -> None:
        """Process received UDP packet."""
        gateway_info = LedoProtocol.parse_gateway_from_udp(data)

        if not gateway_info:
            return

        gateway_id = gateway_info["gateway_id"]
        removed = gateway_info["removed_devices"]
        added = gateway_info["added_devices"]

        # Check for device changes
        state_changed = (removed != self._removed_devices or added != self._added_devices)

        # First discovery
        if not self._gateway_ip:
            self._gateway_ip = source_ip
            self._gateway_id = gateway_id
            logger.info(f"Gateway discovered: IP={source_ip}, ID={gateway_id}")

            # Signal discovery event if waiting
            if self._discovery_event:
                self._discovery_event.set()

            if self._on_gateway_discovered:
                await self._on_gateway_discovered(source_ip, gateway_id)

        # State change detected
        elif state_changed:
            logger.info(f"Lamp state changed: removed={removed}, added={added}")

            if self._on_lamp_state_changed:
                await self._on_lamp_state_changed()

        self._removed_devices = removed
        self._added_devices = added
