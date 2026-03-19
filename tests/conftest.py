"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.models.lamp import Lamp
from app.services.gateway_service import GatewayService
from app.services.lamp_service import LampService


@pytest.fixture
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def app():
    """Create test FastAPI application."""
    app = create_app()
    yield app
    # Cleanup


@pytest_asyncio.fixture
async def client(app):
    """Create async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def mock_gateway_service():
    """Create mock GatewayService."""
    from unittest.mock import PropertyMock

    mock = MagicMock(spec=GatewayService)
    mock._lamps = []
    mock._on_lamps_updated = None

    # Configure property mocks
    type(mock).is_connected = PropertyMock(return_value=False)
    type(mock).gateway_ip = PropertyMock(return_value=None)
    type(mock).gateway_id = PropertyMock(return_value=None)

    def get_all_off():
        return all(l.intensity == 0 for l in mock._lamps)

    def get_lamps_list():
        return mock._lamps.copy()

    type(mock).all_off = PropertyMock(side_effect=get_all_off)
    type(mock).last_communication = PropertyMock(return_value=None)
    type(mock).lamps = PropertyMock(side_effect=get_lamps_list)

    # Configure method mocks
    mock.get_lamps = AsyncMock(side_effect=get_lamps_list)
    mock.update_lamps = AsyncMock(return_value=True)
    mock.get_status = MagicMock(side_effect=lambda: {
        "connected": mock.is_connected,
        "gateway_ip": mock.gateway_ip,
        "gateway_id": mock.gateway_id,
        "lamp_count": len(mock._lamps),
        "all_off": mock.all_off,
        "last_communication": mock.last_communication
    })

    return mock


@pytest.fixture
def mock_lamp_service(mock_gateway_service):
    """Create mock LampService."""
    mock = AsyncMock(spec=LampService)
    mock._gateway = mock_gateway_service

    async def mock_get_all_lamps():
        return await mock_gateway_service.get_lamps()

    async def mock_get_lamp(device_id):
        lamps = await mock_gateway_service.get_lamps()
        for lamp in lamps:
            if lamp.device_id == device_id:
                return lamp
        return None

    mock.get_all_lamps = mock_get_all_lamps
    mock.get_lamp = mock_get_lamp

    return mock


@pytest.fixture
def sample_lamp():
    """Create sample lamp for testing."""
    return Lamp(
        device_id=1680764563,
        name="test_lamp",
        red=255,
        green=200,
        blue=100,
        intensity=200
    )


@pytest.fixture
def sample_lamps():
    """Create multiple sample lamps for testing."""
    return [
        Lamp(
            device_id=1680764563,
            name="living_room",
            red=255,
            green=200,
            blue=100,
            intensity=200
        ),
        Lamp(
            device_id=1680764191,
            name="bedroom",
            red=255,
            green=255,
            blue=255,
            intensity=255
        ),
    ]


@pytest.fixture
def mock_udp_client():
    """Create mock UDP client."""
    mock = AsyncMock()
    mock.is_connected = False
    mock.gateway_ip = None
    mock.gateway_id = None

    async def mock_discover_gateway(timeout=5.0):
        return {"gateway_ip": "192.168.1.100", "gateway_id": 1234567890}

    mock.discover_gateway = mock_discover_gateway
    return mock


@pytest.fixture
def mock_tcp_client():
    """Create mock TCP client."""
    mock = AsyncMock()
    mock.last_communication = None

    async def mock_get_lamps(gateway_ip, gateway_id):
        return [
            Lamp(
                device_id=1680764563,
                name="living_room",
                red=255,
                green=200,
                blue=100,
                intensity=200
            )
        ]

    async def mock_update_lamps(gateway_ip, lamps):
        return True

    mock.get_lamps = mock_get_lamps
    mock.update_lamps = mock_update_lamps
    return mock


# Test data fixtures
@pytest.fixture
def valid_udp_packet():
    """Valid UDP broadcast packet."""
    # Gateway ID 1680764563 in little-endian
    gateway_id = 1680764563
    gateway_bytes = gateway_id.to_bytes(4, byteorder="little")
    return bytes([
        0xF3, 0xD4,              # Magic
    ]) + gateway_bytes + bytes(15) + bytes([0x00, 0x01])  # Reserved + removed/added devices


@pytest.fixture
def valid_tcp_get_lamps_request():
    """Valid TCP GET_LAMPS request."""
    # Gateway ID 1680764563 in little-endian
    gateway_id = 1680764563
    gateway_bytes = gateway_id.to_bytes(4, byteorder="little")
    return bytes([
        0xF3, 0xD4,              # Magic
    ]) + gateway_bytes + bytes([
        0x00, 0x00,              # Reserved
        0x1D,                    # CMD_GET_LAMPS
        0x05,                    # Data length
        0x00, 0x00, 0x00, 0x00,  # Data
        0x43,                    # Trailer
    ])


@pytest.fixture
def valid_tcp_lamp_response():
    """Valid TCP lamp response with one lamp."""
    # Header (10 bytes): Magic(2) + Reserved(6) + Command(1) + DataLength(1)
    header = bytes([
        0xF3, 0xD4,              # Magic
        0x00, 0x00, 0x00, 0x00,  # Reserved (4 bytes)
        0x00, 0x00,              # Reserved (2 bytes)
        0x00,                    # Command byte
        0x08,                    # Data length (8 bytes = 1 lamp)
    ])

    # Lamp: device_id bytes, intensity=200, r=255, g=200, b=100
    lamp_data = bytes([
        0xE3, 0x2B, 0x69, 0x01,  # Device ID bytes (little-endian value)
        200,                     # Intensity
        255,                     # Red
        200,                     # Green
        100,                     # Blue
    ])

    return header + lamp_data


@pytest.fixture
def valid_tcp_update_lamps_request():
    """Valid TCP UPDATE_LAMPS request."""
    # Header (15 bytes)
    header = bytes([
        0xF3, 0xD4,              # Magic
        0xFF, 0xFF, 0xFF, 0xFF,  # Broadcast gateway ID
        0x00, 0x00,              # Reserved
        0x43,                    # CMD_UPDATE_LAMPS
        0x0C,                    # Data length (8 + 4)
        0x00, 0x00, 0x00, 0x00,  # Reserved
        0x43,                    # Trailer
    ])

    # Lamp data
    lamp_data = bytes([
        0xE3, 0x2B, 0x69, 0x01,  # Device ID
        255,                     # Intensity
        255,                     # Red
        0,                       # Green
        0,                       # Blue
    ])

    return header + lamp_data
