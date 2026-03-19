"""Integration tests for UDP/TCP protocol communication."""

import asyncio
import socket
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.protocols.ledo_protocol import LedoProtocol
from app.protocols.udp_client import UdpClient
from app.protocols.tcp_client import TcpClient
from app.models.lamp import Lamp


class TestUdpClient:
    """Test UDP client for gateway discovery."""

    @pytest.mark.asyncio
    async def test_udp_client_start(self):
        """Test UDP client starts successfully."""
        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value.__enter__ = lambda s: s
            mock_socket.return_value.__exit__ = MagicMock()
            mock_socket.return_value.bind = MagicMock()
            mock_socket.return_value.setblocking = MagicMock()
            mock_socket.return_value.setsockopt = MagicMock()

            client = UdpClient()
            await client.start()

            assert client._running is True

            await client.stop()
            assert client._running is False

    @pytest.mark.asyncio
    async def test_udp_client_properties_initial_state(self):
        """Test UDP client initial property values."""
        client = UdpClient()

        assert client.is_connected is False
        assert client.gateway_ip is None
        assert client.gateway_id is None

    @pytest.mark.asyncio
    async def test_udp_client_discovery_timeout(self):
        """Test UDP discovery timeout."""
        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value.__enter__ = lambda s: s
            mock_socket.return_value.__exit__ = MagicMock()
            mock_socket.return_value.bind = MagicMock()
            mock_socket.return_value.setblocking = MagicMock()
            mock_socket.return_value.setsockopt = MagicMock()

            client = UdpClient()
            await client.start()

            # Discover with very short timeout
            result = await client.discover_gateway(timeout=0.1)

            assert result is None

            await client.stop()


class TestTcpClient:
    """Test TCP client for lamp communication."""

    @pytest.mark.asyncio
    async def test_tcp_client_get_lamps_timeout(self):
        """Test TCP client timeout on connection."""
        client = TcpClient()

        # Try to connect to non-routable IP with short timeout
        with patch.object(client.settings, "tcp_connect_timeout", 0.01):
            result = await client.get_lamps("192.0.2.1", 12345)

            assert result is None

    @pytest.mark.asyncio
    async def test_tcp_client_update_lamps_empty_list(self):
        """Test TCP client update with empty lamp list."""
        client = TcpClient()

        result = await client.update_lamps("192.0.2.1", [])

        assert result is False


class TestLedoProtocolIntegration:
    """Test LedoProtocol end-to-end encoding/decoding."""

    def test_round_trip_get_lamps_request(self):
        """Test encoding and decoding GET_LAMPS request/response."""
        gateway_id = 23698115

        # Build request
        request = LedoProtocol.build_get_lamps_request(gateway_id)

        # Simulate response header (10 bytes): Magic(2) + Reserved(6) + Command(1) + DataLength(1)
        response_header = bytes([
            0xF3, 0xD4,              # Magic
            0x00, 0x00, 0x00, 0x00,  # Reserved (4 bytes)
            0x00, 0x00,              # Reserved (2 bytes)
            0x00,                    # Command byte
            0x08,                    # Data length (8 bytes = 1 lamp)
        ])

        # Lamp data
        lamp_data = bytes([
            0xE3, 0x2B, 0x69, 0x01,  # Device ID
            200,                     # Intensity
            255,                     # Red
            200,                     # Green
            100,                     # Blue
        ])

        response = response_header + lamp_data

        # Parse response
        header = LedoProtocol.parse_response_header(response)
        assert header is not None
        assert header["data_length"] == 8

        lamps = LedoProtocol.parse_lamps_from_response(lamp_data)
        assert len(lamps) == 1
        import struct
        expected_id = struct.unpack("<I", bytes([0xE3, 0x2B, 0x69, 0x01]))[0]
        assert lamps[0].device_id == expected_id

    def test_round_trip_update_lamps(self):
        """Test encoding UPDATE_LAMPS request."""
        lamps = [
            Lamp(device_id=1680764563, red=255, green=0, blue=0, intensity=255),
        ]

        request = LedoProtocol.build_update_lamps_request(lamps)

        assert len(request) == 23  # 15 byte header + 8 byte data
        assert request[0:2] == LedoProtocol.MAGIC
        assert request[8] == LedoProtocol.CMD_UPDATE_LAMPS

    def test_round_trip_udp_gateway_discovery(self):
        """Test UDP gateway packet parsing round trip."""
        # Original packet
        gateway_id = 23698115
        removed = 0
        added = 1

        packet = bytes([0xF3, 0xD4]) + gateway_id.to_bytes(4, "little")
        packet += bytes(15)  # Reserved
        packet += bytes([removed, added])

        # Parse
        result = LedoProtocol.parse_gateway_from_udp(packet)

        assert result is not None
        assert result["gateway_id"] == gateway_id
        assert result["removed_devices"] == removed
        assert result["added_devices"] == added


class TestLampToBytesRoundTrip:
    """Test lamp model to bytes conversion round trip."""

    def test_lamp_to_bytes_and_back(self):
        """Test converting lamp to bytes and parsing back."""
        original = Lamp(
            device_id=1680764563,
            red=255,
            green=200,
            blue=100,
            intensity=200
        )

        # Convert to bytes
        lamp_bytes = original.to_bytes()

        # Parse back
        lamps = LedoProtocol.parse_lamps_from_response(lamp_bytes)

        assert len(lamps) == 1
        parsed = lamps[0]

        assert parsed.device_id == original.device_id
        assert parsed.red == original.red
        assert parsed.green == original.green
        assert parsed.blue == original.blue
        assert parsed.intensity == original.intensity

    def test_multiple_lamps_to_bytes_and_back(self):
        """Test converting multiple lamps to bytes and parsing back."""
        original_lamps = [
            Lamp(device_id=1, red=255, green=0, blue=0, intensity=255),
            Lamp(device_id=2, red=0, green=255, blue=0, intensity=200),
            Lamp(device_id=3, red=0, green=0, blue=255, intensity=150),
        ]

        # Convert all to bytes
        lamp_bytes = b"".join(lamp.to_bytes() for lamp in original_lamps)

        # Parse back
        parsed_lamps = LedoProtocol.parse_lamps_from_response(lamp_bytes)

        assert len(parsed_lamps) == 3

        for i, parsed in enumerate(parsed_lamps):
            assert parsed.device_id == original_lamps[i].device_id
            assert parsed.red == original_lamps[i].red
            assert parsed.green == original_lamps[i].green
            assert parsed.blue == original_lamps[i].blue
            assert parsed.intensity == original_lamps[i].intensity


class TestBoundaryValues:
    """Test boundary value handling in protocol."""

    def test_device_id_min_value(self):
        """Test device_id with minimum value (0)."""
        lamp = Lamp(device_id=0, red=0, green=0, blue=0, intensity=0)
        lamp_bytes = lamp.to_bytes()

        lamps = LedoProtocol.parse_lamps_from_response(lamp_bytes)
        assert lamps[0].device_id == 0

    def test_device_id_max_value(self):
        """Test device_id with maximum value (uint32 max)."""
        max_id = 4294967295  # 0xFFFFFFFF
        lamp = Lamp(device_id=max_id, red=255, green=255, blue=255, intensity=255)
        lamp_bytes = lamp.to_bytes()

        lamps = LedoProtocol.parse_lamps_from_response(lamp_bytes)
        assert lamps[0].device_id == max_id

    def test_rgb_values_boundaries(self):
        """Test RGB with boundary values (0 and 255)."""
        lamp = Lamp(device_id=1, red=0, green=128, blue=255, intensity=0)
        lamp_bytes = lamp.to_bytes()

        lamps = LedoProtocol.parse_lamps_from_response(lamp_bytes)
        assert lamps[0].red == 0
        assert lamps[0].green == 128
        assert lamps[0].blue == 255
        assert lamps[0].intensity == 0


class TestErrorHandling:
    """Test error handling in protocol layer."""

    def test_parse_udp_with_invalid_magic(self):
        """Test UDP parsing with invalid magic bytes."""
        invalid_packet = bytes([0x00, 0x01]) + bytes(21)
        result = LedoProtocol.parse_gateway_from_udp(invalid_packet)
        assert result is None

    def test_parse_tcp_with_invalid_magic(self):
        """Test TCP parsing with invalid magic bytes."""
        invalid_header = bytes([0x00, 0x01]) + bytes(8)
        result = LedoProtocol.parse_response_header(invalid_header)
        assert result is None

    def test_parse_udp_short_packet(self):
        """Test UDP parsing with packet shorter than minimum."""
        short_packet = bytes([0xF3, 0xD4]) + bytes(5)
        result = LedoProtocol.parse_gateway_from_udp(short_packet)
        assert result is None

    def test_parse_tcp_short_header(self):
        """Test TCP parsing with header shorter than minimum."""
        short_header = bytes([0xF3, 0xD4]) + bytes(5)
        result = LedoProtocol.parse_response_header(short_header)
        assert result is None

    def test_parse_lamps_empty_data(self):
        """Test parsing lamps from empty data."""
        lamps = LedoProtocol.parse_lamps_from_response(b"")
        assert len(lamps) == 0

    def test_parse_lamps_truncated_data(self):
        """Test parsing lamps from truncated data."""
        truncated = bytes([0xE3, 0x2B, 0x69, 0x01, 200])  # Only 5 bytes
        lamps = LedoProtocol.parse_lamps_from_response(truncated)
        assert len(lamps) == 0
