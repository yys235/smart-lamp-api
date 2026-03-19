"""Unit tests for Lamp model."""

import pytest

from app.models.lamp import Lamp, LampControlRequest
from pydantic import ValidationError


class TestLamp:
    """Test Lamp model."""

    def test_create_lamp_with_all_fields(self):
        """Test creating lamp with all fields."""
        lamp = Lamp(
            device_id=1680764563,
            name="living_room",
            red=255,
            green=200,
            blue=100,
            intensity=200
        )

        assert lamp.device_id == 1680764563
        assert lamp.name == "living_room"
        assert lamp.red == 255
        assert lamp.green == 200
        assert lamp.blue == 100
        assert lamp.intensity == 200

    def test_create_lamp_minimal(self):
        """Test creating lamp with only required fields."""
        lamp = Lamp(device_id=123)

        assert lamp.device_id == 123
        assert lamp.name is None
        assert lamp.red == 255  # Default
        assert lamp.green == 255  # Default
        assert lamp.blue == 255  # Default
        assert lamp.intensity == 255  # Default

    def test_lamp_is_on_property(self):
        """Test is_on property."""
        # Lamp with intensity > 0 is on
        lamp_on = Lamp(device_id=1, intensity=1)
        assert lamp_on.is_on is True

        # Lamp with intensity = 0 is off
        lamp_off = Lamp(device_id=1, intensity=0)
        assert lamp_off.is_on is False

        # Lamp with default intensity (255) is on
        lamp_default = Lamp(device_id=1)
        assert lamp_default.is_on is True

    def test_lamp_to_bytes(self):
        """Test lamp to bytes conversion."""
        lamp = Lamp(
            device_id=1680764563,
            red=255,
            green=200,
            blue=100,
            intensity=200
        )

        data = lamp.to_bytes()

        assert len(data) == 8
        # Verify structure: device_id (4 bytes LE) + intensity + r + g + b
        assert data[0:4] == (1680764563).to_bytes(4, byteorder="little")
        assert data[4] == 200
        assert data[5] == 255
        assert data[6] == 200
        assert data[7] == 100

    def test_lamp_boundary_values(self):
        """Test lamp with boundary values."""
        lamp = Lamp(
            device_id=1,
            red=0,
            green=128,
            blue=255,
            intensity=0
        )

        assert lamp.red == 0
        assert lamp.green == 128
        assert lamp.blue == 255
        assert lamp.intensity == 0

    # Validation tests
    def test_red_validation_fails_negative(self):
        """Test red value below 0 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, red=-1)

    def test_red_validation_fails_above_255(self):
        """Test red value above 255 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, red=256)

    def test_green_validation_fails_negative(self):
        """Test green value below 0 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, green=-1)

    def test_green_validation_fails_above_255(self):
        """Test green value above 255 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, green=256)

    def test_blue_validation_fails_negative(self):
        """Test blue value below 0 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, blue=-1)

    def test_blue_validation_fails_above_255(self):
        """Test blue value above 255 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, blue=256)

    def test_intensity_validation_fails_negative(self):
        """Test intensity value below 0 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, intensity=-1)

    def test_intensity_validation_fails_above_255(self):
        """Test intensity value above 255 fails validation."""
        with pytest.raises(ValidationError):
            Lamp(device_id=1, intensity=256)

    def test_boundary_values_accepted(self):
        """Test boundary values are accepted."""
        lamp = Lamp(
            device_id=1,
            red=0,
            green=255,
            blue=128,
            intensity=0
        )

        assert lamp.red == 0
        assert lamp.green == 255
        assert lamp.blue == 128
        assert lamp.intensity == 0


class TestLampControlRequest:
    """Test LampControlRequest model."""

    def test_create_request_with_all_fields(self):
        """Test creating request with all fields."""
        request = LampControlRequest(
            red=100,
            green=150,
            blue=200,
            intensity=180
        )

        assert request.red == 100
        assert request.green == 150
        assert request.blue == 200
        assert request.intensity == 180

    def test_create_request_empty(self):
        """Test creating empty request uses defaults."""
        request = LampControlRequest()

        assert request.red == 255  # Default
        assert request.green == 255  # Default
        assert request.blue == 255  # Default
        assert request.intensity == 255  # Default

    def test_create_request_partial_fields(self):
        """Test creating request with partial fields."""
        request = LampControlRequest(red=100)

        assert request.red == 100
        assert request.green == 255  # Default
        assert request.blue == 255  # Default
        assert request.intensity == 255  # Default

    def test_all_fields_are_optional(self):
        """Test all fields are optional."""
        # Should not raise error
        request = LampControlRequest()
        assert request is not None

    def test_red_validation_fails_negative(self):
        """Test red value below 0 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(red=-1)

    def test_red_validation_fails_above_255(self):
        """Test red value above 255 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(red=256)

    def test_green_validation_fails_negative(self):
        """Test green value below 0 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(green=-1)

    def test_green_validation_fails_above_255(self):
        """Test green value above 255 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(green=256)

    def test_blue_validation_fails_negative(self):
        """Test blue value below 0 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(blue=-1)

    def test_blue_validation_fails_above_255(self):
        """Test blue value above 255 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(blue=256)

    def test_intensity_validation_fails_negative(self):
        """Test intensity value below 0 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(intensity=-1)

    def test_intensity_validation_fails_above_255(self):
        """Test intensity value above 255 fails validation."""
        with pytest.raises(ValidationError):
            LampControlRequest(intensity=256)

    def test_boundary_values_accepted(self):
        """Test boundary values are accepted."""
        request = LampControlRequest(
            red=0,
            green=255,
            blue=128,
            intensity=0
        )

        assert request.red == 0
        assert request.green == 255
        assert request.blue == 128
        assert request.intensity == 0
