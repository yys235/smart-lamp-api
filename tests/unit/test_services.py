"""Unit tests for service layer."""

import pytest

from app.models.lamp import Lamp, LampControlRequest


class TestLampService:
    """Test LampService."""

    @pytest.mark.asyncio
    async def test_get_all_lamps_returns_empty_list_when_no_lamps(self, mock_lamp_service):
        """Test get_all_lamps returns empty list when no lamps available."""
        lamps = await mock_lamp_service.get_all_lamps()
        assert lamps == []

    @pytest.mark.asyncio
    async def test_get_all_lamps_returns_lamps(self, mock_lamp_service, sample_lamps):
        """Test get_all_lamps returns all lamps."""
        mock_lamp_service._gateway._lamps = sample_lamps

        lamps = await mock_lamp_service.get_all_lamps()

        assert len(lamps) == 2
        assert lamps[0].device_id == 1680764563
        assert lamps[1].device_id == 1680764191

    @pytest.mark.asyncio
    async def test_get_lamp_found(self, mock_lamp_service, sample_lamps):
        """Test get_lamp returns lamp when found."""
        mock_lamp_service._gateway._lamps = sample_lamps

        lamp = await mock_lamp_service.get_lamp(1680764563)

        assert lamp is not None
        assert lamp.device_id == 1680764563
        assert lamp.name == "living_room"

    @pytest.mark.asyncio
    async def test_get_lamp_not_found(self, mock_lamp_service, sample_lamps):
        """Test get_lamp returns None when not found."""
        mock_lamp_service._gateway._lamps = sample_lamps

        lamp = await mock_lamp_service.get_lamp(9999999)

        assert lamp is None

    @pytest.mark.asyncio
    async def test_get_lamp_empty_list(self, mock_lamp_service):
        """Test get_lamp returns None when lamp list is empty."""
        lamp = await mock_lamp_service.get_lamp(1680764563)
        assert lamp is None


class TestGatewayService:
    """Test GatewayService."""

    def test_initial_state(self, mock_gateway_service):
        """Test gateway service initial state."""
        assert mock_gateway_service.is_connected is False
        assert mock_gateway_service.gateway_ip is None
        assert mock_gateway_service.gateway_id is None
        assert mock_gateway_service.all_off is True
        assert len(mock_gateway_service.lamps) == 0

    def test_all_off_property_true_when_empty(self, mock_gateway_service):
        """Test all_off property returns True when no lamps."""
        assert mock_gateway_service.all_off is True

    def test_all_off_property_true_when_all_off(self, mock_gateway_service):
        """Test all_off property returns True when all lamps off."""
        mock_gateway_service._lamps = [
            Lamp(device_id=1, intensity=0),
            Lamp(device_id=2, intensity=0),
        ]
        assert mock_gateway_service.all_off is True

    def test_all_off_property_false_when_one_on(self, mock_gateway_service):
        """Test all_off property returns False when one lamp is on."""
        mock_gateway_service._lamps = [
            Lamp(device_id=1, intensity=0),
            Lamp(device_id=2, intensity=100),
        ]
        assert mock_gateway_service.all_off is False

    def test_lamps_property_returns_copy(self, mock_gateway_service, sample_lamps):
        """Test lamps property returns a copy of the list."""
        mock_gateway_service._lamps = sample_lamps

        lamps = mock_gateway_service.lamps
        lamps.append(Lamp(device_id=999))

        assert len(mock_gateway_service._lamps) == 2
        assert len(lamps) == 3

    def test_get_status(self, mock_gateway_service):
        """Test get_status returns correct status dict."""
        status = mock_gateway_service.get_status()

        assert status["connected"] is False
        assert status["gateway_ip"] is None
        assert status["gateway_id"] is None
        assert status["lamp_count"] == 0
        assert status["all_off"] is True
        assert status["last_communication"] is None

    def test_get_status_with_lamps(self, mock_gateway_service, sample_lamps):
        """Test get_status with lamps."""
        mock_gateway_service._lamps = sample_lamps

        status = mock_gateway_service.get_status()

        assert status["lamp_count"] == 2
        assert status["all_off"] is False  # At least one lamp is on


class TestLampIsOnProperty:
    """Test Lamp.is_on property edge cases."""

    def test_is_on_with_zero_intensity(self):
        """Test is_on returns False when intensity is 0."""
        lamp = Lamp(device_id=1, intensity=0)
        assert lamp.is_on is False

    def test_is_on_with_one_intensity(self):
        """Test is_on returns True when intensity is 1."""
        lamp = Lamp(device_id=1, intensity=1)
        assert lamp.is_on is True

    def test_is_on_with_max_intensity(self):
        """Test is_on returns True when intensity is 255."""
        lamp = Lamp(device_id=1, intensity=255)
        assert lamp.is_on is True


class TestLampControlRequestDefaults:
    """Test LampControlRequest default values."""

    def test_default_rgb_white(self):
        """Test default RGB is white (255, 255, 255)."""
        request = LampControlRequest()
        assert request.red == 255
        assert request.green == 255
        assert request.blue == 255

    def test_default_intensity_max(self):
        """Test default intensity is 255 (max)."""
        request = LampControlRequest()
        assert request.intensity == 255

    def test_partial_request_uses_defaults_for_unset(self):
        """Test unset fields use default values."""
        request = LampControlRequest(red=100)
        assert request.red == 100
        assert request.green == 255  # Default
        assert request.blue == 255  # Default
        assert request.intensity == 255  # Default
