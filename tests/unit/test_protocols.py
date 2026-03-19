"""Unit tests for LedoProtocol."""

import struct

import pytest

from app.protocols.ledo_protocol import LedoProtocol
from app.models.lamp import Lamp


class TestLedoProtocol:
    """Test LedoProtocol encoder/decoder."""

    def test_magic_bytes(self):
        """Test magic bytes are correct."""
        assert LedoProtocol.MAGIC == bytes([0xF3, 0xD4])

    def test_command_codes(self):
        """Test command codes are defined."""
        assert LedoProtocol.CMD_GET_LAMPS == 0x1D
        assert LedoProtocol.CMD_UPDATE_LAMPS == 0x43

    # UDP parsing tests
    def test_parse_valid_gateway_from_udp(self, valid_udp_packet):
        """Test parsing valid UDP gateway packet."""
        result = LedoProtocol.parse_gateway_from_udp(valid_udp_packet)

        assert result is not None
        # valid_udp_packet uses gateway_id 1680764563
        assert result["gateway_id"] == 1680764563
        assert result["removed_devices"] == 0
        assert result["added_devices"] == 1

    def test_parse_udp_packet_too_short(self):
        """Test UDP packet shorter than minimum is rejected."""
        short_packet = bytes([0xF3, 0xD4, 0x00, 0x00])
        result = LedoProtocol.parse_gateway_from_udp(short_packet)
        assert result is None

    def test_parse_udp_packet_invalid_magic(self):
        """Test UDP packet with invalid magic bytes is rejected."""
        invalid_packet = bytes([0x00, 0x00]) + bytes(21)
        result = LedoProtocol.parse_gateway_from_udp(invalid_packet)
        assert result is None

    def test_parse_udp_exactly_minimum_size(self):
        """Test UDP packet exactly 23 bytes is accepted."""
        # 23 bytes minimum
        packet = bytes([0xF3, 0xD4]) + bytes(21)
        result = LedoProtocol.parse_gateway_from_udp(packet)
        assert result is not None

    # TCP request building tests
    def test_build_get_lamps_request(self):
        """Test building GET_LAMPS request."""
        gateway_id = 23698115  # 0x01692BE3
        request = LedoProtocol.build_get_lamps_request(gateway_id)

        assert len(request) == 15
        assert request[0:2] == LedoProtocol.MAGIC
        assert request[2:6] == struct.pack("<I", gateway_id)
        assert request[8] == LedoProtocol.CMD_GET_LAMPS

    def test_build_get_lamps_request_zero_gateway(self):
        """Test building GET_LAMPS request with gateway_id=0."""
        request = LedoProtocol.build_get_lamps_request(0)

        assert len(request) == 15
        assert request[0:2] == LedoProtocol.MAGIC
        assert request[2:6] == bytes([0x00, 0x00, 0x00, 0x00])

    def test_build_update_lamps_request_single_lamp(self):
        """Test building UPDATE_LAMPS request with one lamp."""
        lamp = Lamp(
            device_id=1680764563,
            red=255,
            green=0,
            blue=0,
            intensity=255
        )

        request = LedoProtocol.build_update_lamps_request([lamp])

        assert len(request) == 23  # 15 byte header + 8 byte lamp data
        assert request[0:2] == LedoProtocol.MAGIC
        assert request[8] == LedoProtocol.CMD_UPDATE_LAMPS
        assert request[9] == 12  # Data length (8 + 4)

    def test_build_update_lamps_request_multiple_lamps(self):
        """Test building UPDATE_LAMPS request with multiple lamps."""
        lamps = [
            Lamp(device_id=1, red=255, green=0, blue=0, intensity=255),
            Lamp(device_id=2, red=0, green=255, blue=0, intensity=200),
        ]

        request = LedoProtocol.build_update_lamps_request(lamps)

        assert len(request) == 31  # 15 byte header + 16 bytes lamp data
        assert request[0:2] == LedoProtocol.MAGIC
        assert request[8] == LedoProtocol.CMD_UPDATE_LAMPS
        assert request[9] == 20  # Data length (16 + 4)

    def test_build_update_lamps_request_empty_list(self):
        """Test building UPDATE_LAMPS request with empty list."""
        request = LedoProtocol.build_update_lamps_request([])

        # Header only
        assert len(request) == 15
        assert request[0:2] == LedoProtocol.MAGIC

    # TCP response parsing tests
    def test_parse_response_header_valid(self):
        """Test parsing valid TCP response header."""
        header = bytes([
            0xF3, 0xD4,              # Magic
            0x00, 0x00, 0x00, 0x00,  # Reserved
            0x00, 0x00,              # Reserved
            0x1D,                    # Command
            0x08,                    # Data length
        ])

        result = LedoProtocol.parse_response_header(header)

        assert result is not None
        assert result["command"] == 0x1D
        assert result["data_length"] == 8

    def test_parse_response_header_too_short(self):
        """Test response header shorter than 10 bytes is rejected."""
        short_header = bytes([0xF3, 0xD4]) + bytes(5)
        result = LedoProtocol.parse_response_header(short_header)
        assert result is None

    def test_parse_response_header_invalid_magic(self):
        """Test response header with invalid magic is rejected."""
        invalid_header = bytes([0x00, 0x00]) + bytes(8)
        result = LedoProtocol.parse_response_header(invalid_header)
        assert result is None

    # Lamp parsing tests
    def test_parse_lamps_from_response_single_lamp(self):
        """Test parsing single lamp from response."""
        # Device ID 1680764563 in little-endian: 0x93, 0x6E, 0x2E, 0x64
        lamp_data = bytes([
            0x93, 0x6E, 0x2E, 0x64,  # Device ID (1680764563 LE)
            200,                     # Intensity
            255,                     # Red
            200,                     # Green
            100,                     # Blue
        ])

        lamps = LedoProtocol.parse_lamps_from_response(lamp_data)

        assert len(lamps) == 1
        assert lamps[0].device_id == 1680764563
        assert lamps[0].intensity == 200
        assert lamps[0].red == 255
        assert lamps[0].green == 200
        assert lamps[0].blue == 100

    def test_parse_lamps_from_response_multiple_lamps(self):
        """Test parsing multiple lamps from response."""
        # Device ID 1680764563 in LE: 0x93 0x6E 0x2E 0x64
        # Device ID 1680764564 in LE: 0x94 0x6E 0x2E 0x64
        lamp_data = bytes([
            # Lamp 1 (1680764563)
            0x93, 0x6E, 0x2E, 0x64, 200, 255, 200, 100,
            # Lamp 2 (1680764564)
            0x94, 0x6E, 0x2E, 0x64, 255, 255, 255, 255,
        ])

        lamps = LedoProtocol.parse_lamps_from_response(lamp_data)

        assert len(lamps) == 2
        assert lamps[0].device_id == 1680764563
        assert lamps[1].device_id == 1680764564

    def test_parse_lamps_from_response_empty(self):
        """Test parsing empty response returns empty list."""
        lamps = LedoProtocol.parse_lamps_from_response(b"")
        assert len(lamps) == 0

    def test_parse_lamps_from_response_too_short(self):
        """Test response shorter than 8 bytes returns empty list."""
        short_data = bytes([0xE3, 0x2B, 0x69, 0x01, 200])
        lamps = LedoProtocol.parse_lamps_from_response(short_data)
        assert len(lamps) == 0

    def test_parse_lamps_partial_lamp_ignored(self):
        """Test partial lamp data at end is ignored."""
        # 16 bytes = 2 full lamps
        lamp_data = bytes([
            0xE3, 0x2B, 0x69, 0x01, 200, 255, 200, 100,
            0xE4, 0x2B, 0x69, 0x01, 255, 255, 255, 255,
            0xE5,  # Partial third lamp
        ])

        lamps = LedoProtocol.parse_lamps_from_response(lamp_data)

        # Should only parse 2 complete lamps
        assert len(lamps) == 2

    # Boundary value tests
    def test_parse_lamp_boundary_values(self):
        """Test parsing lamp with min/max boundary values."""
        lamp_data = bytes([
            0xFF, 0xFF, 0xFF, 0xFF,  # Device ID: max uint32
            0,                       # Intensity: 0 (off)
            0,                       # Red: 0
            0,                       # Green: 0
            0xFF,                    # Blue: 255
        ])

        lamps = LedoProtocol.parse_lamps_from_response(lamp_data)

        assert len(lamps) == 1
        assert lamps[0].device_id == 4294967295
        assert lamps[0].intensity == 0
        assert lamps[0].red == 0
        assert lamps[0].green == 0
        assert lamps[0].blue == 255

    def test_lamp_to_bytes_conversion(self):
        """Test Lamp.to_bytes() produces correct format."""
        lamp = Lamp(
            device_id=1680764563,
            red=255,
            green=200,
            blue=100,
            intensity=200
        )

        data = lamp.to_bytes()

        assert len(data) == 8
        # Device ID in little endian
        assert data[0:4] == struct.pack("<I", 1680764563)
        assert data[4] == 200  # Intensity
        assert data[5] == 255  # Red
        assert data[6] == 200  # Green
        assert data[7] == 100  # Blue
