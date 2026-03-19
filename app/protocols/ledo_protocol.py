"""Ledo protocol implementation for smart lamp communication."""

import struct
from typing import List, Optional

from app.models.lamp import Lamp


class LedoProtocol:
    """Ledo protocol encoder/decoder for smart lamp communication."""

    # Magic bytes for protocol
    MAGIC = bytes([0xF3, 0xD4])

    # Command codes
    CMD_GET_LAMPS = 0x1D
    CMD_UPDATE_LAMPS = 0x43

    @classmethod
    def build_get_lamps_request(cls, gateway_id: int) -> bytes:
        """Build request to get all lamps from gateway.

        Args:
            gateway_id: Gateway device ID

        Returns:
            Request bytes (15 bytes total)
        """
        gateway_bytes = struct.pack("<I", gateway_id)  # Little endian
        return bytes([
            0xF3, 0xD4,  # Magic
            *gateway_bytes,  # Gateway ID (4 bytes)
            0x00, 0x00,  # Reserved
            cls.CMD_GET_LAMPS,  # Command
            0x05,  # Length
            0x00, 0x00, 0x00, 0x00,  # Data
            0x43,  # Checksum/trailer
        ])

    @classmethod
    def build_update_lamps_request(cls, lamps: List[Lamp]) -> bytes:
        """Build request to update lamp states.

        Args:
            lamps: List of lamps to update

        Returns:
            Request bytes
        """
        lamp_data = b"".join(lamp.to_bytes() for lamp in lamps)
        data_length = len(lamp_data) + 4  # +4 for additional data

        header = bytes([
            0xF3, 0xD4,  # Magic
            0xFF, 0xFF, 0xFF, 0xFF,  # Broadcast gateway ID
            0x00, 0x00,  # Reserved
            cls.CMD_UPDATE_LAMPS,  # Command
            data_length & 0xFF,  # Data length
            0x00, 0x00, 0x00, 0x00,  # Reserved
            0x43,  # Checksum/trailer
        ])

        return header + lamp_data

    @classmethod
    def parse_gateway_from_udp(cls, data: bytes) -> Optional[dict]:
        """Parse gateway info from UDP broadcast packet.

        Args:
            data: Raw UDP packet data

        Returns:
            Dict with gateway_id, removed_devices, added_devices or None
        """
        if len(data) < 23:
            return None

        if data[0:2] != cls.MAGIC:
            return None

        gateway_id = struct.unpack("<I", data[2:6])[0]
        removed_devices = data[21]
        added_devices = data[22]

        return {
            "gateway_id": gateway_id,
            "removed_devices": removed_devices,
            "added_devices": added_devices,
        }

    @classmethod
    def parse_lamps_from_response(cls, data: bytes) -> List[Lamp]:
        """Parse lamp list from TCP response.

        Args:
            data: Response data (after header)

        Returns:
            List of Lamp objects
        """
        lamps = []

        if len(data) < 8:
            return lamps

        # Each lamp is 8 bytes
        lamp_count = len(data) // 8

        for i in range(lamp_count):
            offset = i * 8

            device_id = struct.unpack("<I", data[offset:offset+4])[0]
            intensity = data[offset + 4] & 0xFF
            red = data[offset + 5] & 0xFF
            green = data[offset + 6] & 0xFF
            blue = data[offset + 7] & 0xFF

            lamps.append(Lamp(
                device_id=device_id,
                red=red,
                green=green,
                blue=blue,
                intensity=intensity,
            ))

        return lamps

    @classmethod
    def parse_response_header(cls, data: bytes) -> Optional[dict]:
        """Parse TCP response header.

        Args:
            data: Raw response bytes

        Returns:
            Dict with command and data_length or None
        """
        if len(data) < 10:
            return None

        if data[0:2] != cls.MAGIC:
            return None

        command = data[8]
        data_length = data[9]

        return {
            "command": command,
            "data_length": data_length,
        }
