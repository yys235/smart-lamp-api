"""Lamp data models."""

from typing import Optional

from pydantic import BaseModel, Field


class Lamp(BaseModel):
    """Lamp model representing a smart lamp device."""

    device_id: int = Field(..., description="Device unique identifier")
    name: Optional[str] = Field(None, description="Lamp name/alias")
    red: int = Field(255, ge=0, le=255, description="Red color value (0-255)")
    green: int = Field(255, ge=0, le=255, description="Green color value (0-255)")
    blue: int = Field(255, ge=0, le=255, description="Blue color value (0-255)")
    intensity: int = Field(255, ge=0, le=255, description="Brightness intensity (0-255)")

    @property
    def is_on(self) -> bool:
        """Check if lamp is on (intensity > 0)."""
        return self.intensity > 0

    def to_bytes(self) -> bytes:
        """Convert lamp state to bytes for TCP protocol."""
        # Device ID in little endian (4 bytes)
        device_id_bytes = self.device_id.to_bytes(4, byteorder="little")
        # Intensity, R, G, B (4 bytes)
        return device_id_bytes + bytes([
            self.intensity & 0xFF,
            self.red & 0xFF,
            self.green & 0xFF,
            self.blue & 0xFF,
        ])

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1680764563,
                "name": "living_room",
                "red": 255,
                "green": 200,
                "blue": 100,
                "intensity": 200,
            }
        }


class LampControlRequest(BaseModel):
    """Request model for controlling a lamp."""

    red: Optional[int] = Field(255, ge=0, le=255, description="Red color (0-255)")
    green: Optional[int] = Field(255, ge=0, le=255, description="Green color (0-255)")
    blue: Optional[int] = Field(255, ge=0, le=255, description="Blue color (0-255)")
    intensity: Optional[int] = Field(255, ge=0, le=255, description="Brightness (0-255)")

    class Config:
        json_schema_extra = {
            "example": {
                "red": 255,
                "green": 200,
                "blue": 100,
                "intensity": 200,
            }
        }
