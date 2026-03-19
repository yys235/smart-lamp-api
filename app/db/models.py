"""Database models for Smart Lamp API."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class LampState(Base):
    """Model for storing lamp state history."""

    __tablename__ = "lamp_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    red: Mapped[int] = mapped_column(Integer, default=0)
    green: Mapped[int] = mapped_column(Integer, default=0)
    blue: Mapped[int] = mapped_column(Integer, default=0)
    intensity: Mapped[int] = mapped_column(Integer, default=0)
    is_on: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    def __repr__(self) -> str:
        return f"<LampState(device_id={self.device_id}, intensity={self.intensity})>"


class OperationLog(Base):
    """Model for storing operation logs."""

    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    device_id: Mapped[int] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    def __repr__(self) -> str:
        return f"<OperationLog(operation={self.operation}, success={self.success})>"


class GatewayConnection(Base):
    """Model for storing gateway connection history."""

    __tablename__ = "gateway_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gateway_ip: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_id: Mapped[int] = mapped_column(Integer, nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    def __repr__(self) -> str:
        return f"<GatewayConnection(gateway_ip={self.gateway_ip}, connected={self.connected})>"
