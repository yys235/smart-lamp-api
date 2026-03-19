"""Service for logging operations to database."""

from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_context
from app.db.models import LampState, OperationLog, GatewayConnection


class LogService:
    """Service for managing operation logs in database."""

    @staticmethod
    async def log_operation(
        operation: str,
        device_id: Optional[int] = None,
        details: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an operation to database.

        Args:
            operation: Operation name (e.g., 'lamp_on', 'lamp_off', 'set_color')
            device_id: Device ID if applicable
            details: Additional details about the operation
            success: Whether the operation succeeded
            error_message: Error message if operation failed
        """
        async with get_db_context() as db:
            log_entry = OperationLog(
                operation=operation,
                device_id=device_id,
                details=details,
                success=success,
                error_message=error_message,
            )
            db.add(log_entry)
            logger.debug(f"Logged operation: {operation} (success={success})")

    @staticmethod
    async def log_lamp_state(
        device_id: int,
        red: int,
        green: int,
        blue: int,
        intensity: int,
    ) -> None:
        """Log lamp state change to database.

        Args:
            device_id: Lamp device ID
            red: Red color value (0-255)
            green: Green color value (0-255)
            blue: Blue color value (0-255)
            intensity: Intensity value (0-255)
        """
        async with get_db_context() as db:
            state_entry = LampState(
                device_id=device_id,
                red=red,
                green=green,
                blue=blue,
                intensity=intensity,
                is_on=intensity > 0,
            )
            db.add(state_entry)

    @staticmethod
    async def log_gateway_connection(
        gateway_ip: str,
        gateway_id: int,
        connected: bool = True,
    ) -> None:
        """Log gateway connection event.

        Args:
            gateway_ip: Gateway IP address
            gateway_id: Gateway ID
            connected: True if connected, False if disconnected
        """
        async with get_db_context() as db:
            conn_entry = GatewayConnection(
                gateway_ip=gateway_ip,
                gateway_id=gateway_id,
                connected=connected,
            )
            db.add(conn_entry)
            logger.info(f"Logged gateway connection: {gateway_ip} (connected={connected})")

    @staticmethod
    async def cleanup_old_logs(days: int = 30) -> dict:
        """Clean up logs older than specified days.

        Args:
            days: Delete logs older than this many days

        Returns:
            Dict with cleanup statistics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        stats = {}

        async with get_db_context() as db:
            # Clean operation logs
            op_result = await db.execute(
                delete(OperationLog).where(OperationLog.created_at < cutoff)
            )
            stats["operation_logs_deleted"] = op_result.rowcount

            # Clean lamp states
            state_result = await db.execute(
                delete(LampState).where(LampState.created_at < cutoff)
            )
            stats["lamp_states_deleted"] = state_result.rowcount

            # Clean gateway connections
            conn_result = await db.execute(
                delete(GatewayConnection).where(GatewayConnection.created_at < cutoff)
            )
            stats["gateway_connections_deleted"] = conn_result.rowcount

        logger.info(f"Cleaned up {sum(stats.values())} old database records")
        return stats

    @staticmethod
    async def get_recent_operations(
        limit: int = 100,
        device_id: Optional[int] = None,
    ) -> List[OperationLog]:
        """Get recent operation logs.

        Args:
            limit: Maximum number of records to return
            device_id: Filter by device ID if specified

        Returns:
            List of OperationLog records
        """
        async with get_db_context() as db:
            query = select(OperationLog).order_by(
                OperationLog.created_at.desc()
            ).limit(limit)

            if device_id:
                query = query.where(OperationLog.device_id == device_id)

            result = await db.execute(query)
            return list(result.scalars().all())

    @staticmethod
    async def get_lamp_state_history(
        device_id: int,
        limit: int = 50,
    ) -> List[LampState]:
        """Get lamp state history for a device.

        Args:
            device_id: Lamp device ID
            limit: Maximum number of records to return

        Returns:
            List of LampState records
        """
        async with get_db_context() as db:
            query = select(LampState).where(
                LampState.device_id == device_id
            ).order_by(
                LampState.created_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())
