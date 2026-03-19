"""API response models."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response model."""

    code: int = Field(0, description="Status code (0 = success)")
    message: str = Field("success", description="Response message")
    data: Optional[T] = Field(None, description="Response data")

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "success") -> "ApiResponse[T]":
        """Create a success response."""
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 1, data: Optional[T] = None) -> "ApiResponse[T]":
        """Create an error response."""
        return cls(code=code, message=message, data=data)

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "success",
                "data": {"key": "value"}
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    gateway_connected: bool = Field(..., description="Gateway connection status")
    lamp_count: int = Field(..., description="Number of lamps")
    all_off: bool = Field(..., description="Whether all lamps are off")
    last_communication: Optional[str] = Field(None, description="Last communication time")
    timestamp: str = Field(..., description="Response timestamp")


class GatewayStatusResponse(BaseModel):
    """Gateway status response."""

    connected: bool = Field(..., description="Gateway connection status")
    gateway_ip: Optional[str] = Field(None, description="Gateway IP address")
    gateway_id: Optional[int] = Field(None, description="Gateway device ID")
    lamp_count: int = Field(..., description="Number of lamps")
    all_off: bool = Field(..., description="Whether all lamps are off")
    last_communication: Optional[str] = Field(None, description="Last communication time")
