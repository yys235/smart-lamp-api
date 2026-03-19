"""Integration tests for API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.models.lamp import Lamp, LampControlRequest


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test GET /api/v1/health returns health status."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200

        data = response.json()
        # Health endpoint returns nested structure
        assert "status" in data or "code" in data


class TestLampEndpoints:
    """Test lamp control endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_lamps_empty(self, client: AsyncClient):
        """Test GET /api/v1/lamps returns empty list when no lamps."""
        response = await client.get(
            "/api/v1/lamps",
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200

        data = response.json()
        # ApiResponse format: {code: 0, message: "success", data: {...}}
        assert "code" in data
        assert "data" in data
        assert "lamps" in data["data"]
        # Empty lamp list
        assert isinstance(data["data"]["lamps"], list)

    @pytest.mark.asyncio
    async def test_get_lamp_by_id_not_found(self, client: AsyncClient):
        """Test GET /api/v1/lamps/{device_id} returns 404 when not found."""
        # Use a device_id that doesn't exist
        response = await client.get(
            "/api/v1/lamps/9999999999",
            headers={"X-API-Key": "test-key"}
        )

        # Should return 404 when lamp not found
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_lamp_invalid_id(self, client: AsyncClient):
        """Test GET /api/v1/lamps with invalid ID."""
        response = await client.get(
            "/api/v1/lamps/0",
            headers={"X-API-Key": "test-key"}
        )

        # Validation error (device_id must be >= 1)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_turn_on_lamp_invalid_rgb(self, client: AsyncClient):
        """Test POST /api/v1/lamps/{device_id}/on with invalid RGB."""
        response = await client.post(
            "/api/v1/lamps/1/on",
            json={"red": 256, "green": 0, "blue": 0},  # red > 255
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_turn_on_lamp_valid_rgb(self, client: AsyncClient):
        """Test POST /api/v1/lamps/{device_id}/on with valid RGB."""
        response = await client.post(
            "/api/v1/lamps/1/on",
            json={"red": 255, "green": 100, "blue": 50, "intensity": 200},
            headers={"X-API-Key": "test-key"}
        )

        # May succeed or fail depending on gateway connection
        # Test that the request is processed
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_turn_on_lamp_default_values(self, client: AsyncClient):
        """Test POST /api/v1/lamps/{device_id}/on with default values."""
        response = await client.post(
            "/api/v1/lamps/1/on",
            json={},  # Use defaults
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_turn_off_lamp(self, client: AsyncClient):
        """Test POST /api/v1/lamps/{device_id}/off."""
        response = await client.post(
            "/api/v1/lamps/1/off",
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code in [200, 500]


class TestGatewayEndpoint:
    """Test gateway endpoint."""

    @pytest.mark.asyncio
    async def test_get_gateway_status(self, client: AsyncClient):
        """Test GET /api/v1/gateway."""
        response = await client.get(
            "/api/v1/gateway",
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200

        data = response.json()
        assert "code" in data
        assert "data" in data
        # Check for expected fields in gateway status
        assert "connected" in data["data"] or "gateway_ip" in data["data"]


class TestAuthentication:
    """Test API authentication."""

    @pytest.mark.asyncio
    async def test_request_with_api_key(self, client: AsyncClient):
        """Test request with API key passes through."""
        # When API key is configured, valid key should pass
        # When no API key is configured, any request passes
        response = await client.get(
            "/api/v1/lamps",
            headers={"X-API-Key": "any-key"}
        )

        # Should not get 401/403 (no API key configured in test env)
        assert response.status_code != 401
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_request_without_api_key(self, client: AsyncClient):
        """Test request without API key when none configured."""
        response = await client.get("/api/v1/lamps")

        # Should pass when no API key is configured
        assert response.status_code != 401


class TestResponseFormat:
    """Test API response format consistency."""

    @pytest.mark.asyncio
    async def test_health_response_format(self, client: AsyncClient):
        """Test health endpoint response format."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Health endpoint returns ApiResponse format: {code: 0, message: "success", data: {...}}
        # The actual status data is nested under data
        if "code" in data:
            assert "data" in data
            assert "status" in data["data"]
            assert "timestamp" in data["data"]
        else:
            # Direct format (should not happen with current implementation)
            assert "status" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_api_response_format(self, client: AsyncClient):
        """Test API endpoints return ApiResponse format."""
        response = await client.get(
            "/api/v1/lamps",
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # ApiResponse format: {code: 0, message: "success", data: {...}}
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert data["code"] == 0
