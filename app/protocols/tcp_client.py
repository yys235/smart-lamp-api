"""TCP client for lamp control communication."""

import asyncio
import socket
from typing import List, Optional

from loguru import logger

from app.config import get_settings
from app.models.lamp import Lamp
from app.protocols.ledo_protocol import LedoProtocol


class TcpClient:
    """TCP client for communicating with smart lamp gateway."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._last_communication: Optional[str] = None

    async def get_lamps(
        self,
        gateway_ip: str,
        gateway_id: int
    ) -> Optional[List[Lamp]]:
        """Get all lamps from gateway.

        Args:
            gateway_ip: Gateway IP address
            gateway_id: Gateway device ID

        Returns:
            List of Lamp objects or None on failure
        """
        request = LedoProtocol.build_get_lamps_request(gateway_id)
        response = await self._send_request(gateway_ip, request)

        if not response:
            return None

        # Parse response header
        header = LedoProtocol.parse_response_header(response)
        if not header or header["data_length"] == 0:
            return None

        # Extract lamp data (after 10-byte header)
        lamp_data = response[10:10 + header["data_length"]]
        lamps = LedoProtocol.parse_lamps_from_response(lamp_data)

        logger.info(f"Retrieved {len(lamps)} lamps from gateway")
        return lamps

    async def update_lamps(
        self,
        gateway_ip: str,
        lamps: List[Lamp]
    ) -> bool:
        """Update lamp states on gateway.

        Args:
            gateway_ip: Gateway IP address
            lamps: List of lamps with new states

        Returns:
            True on success, False on failure
        """
        if not lamps:
            return False

        request = LedoProtocol.build_update_lamps_request(lamps)
        response = await self._send_request(gateway_ip, request)

        if response:
            logger.info(f"Updated {len(lamps)} lamps")
            return True

        return False

    async def _send_request(
        self,
        gateway_ip: str,
        request: bytes
    ) -> Optional[bytes]:
        """Send TCP request and receive response.

        Args:
            gateway_ip: Gateway IP address
            request: Request bytes

        Returns:
            Response bytes or None on failure
        """
        loop = asyncio.get_event_loop()

        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Connect
            await asyncio.wait_for(
                loop.sock_connect(
                    sock,
                    (gateway_ip, self.settings.tcp_port)
                ),
                timeout=self.settings.tcp_connect_timeout
            )

            try:
                # Send request
                await loop.sock_sendall(sock, request)

                # Receive header (10 bytes)
                header = b""
                while len(header) < 10:
                    chunk = await asyncio.wait_for(
                        loop.sock_recv(sock, 10 - len(header)),
                        timeout=self.settings.tcp_timeout
                    )
                    if not chunk:
                        break
                    header += chunk

                if len(header) < 10:
                    logger.warning("Incomplete response header")
                    return None

                # Get data length from header
                data_length = header[9]

                # Receive data
                data = b""
                while len(data) < data_length:
                    chunk = await asyncio.wait_for(
                        loop.sock_recv(sock, data_length - len(data)),
                        timeout=self.settings.tcp_timeout
                    )
                    if not chunk:
                        break
                    data += chunk

                # Update last communication time
                from datetime import datetime
                self._last_communication = datetime.now().strftime("%H:%M:%S")

                return header + data

            finally:
                sock.close()

        except asyncio.TimeoutError:
            logger.error("TCP request timeout")
            return None
        except ConnectionRefusedError:
            logger.error(f"Connection refused to {gateway_ip}:{self.settings.tcp_port}")
            return None
        except Exception as e:
            logger.error(f"TCP request failed: {e}")
            return None

    @property
    def last_communication(self) -> Optional[str]:
        """Get last communication timestamp."""
        return self._last_communication
