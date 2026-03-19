"""Log management API endpoints."""

from fastapi import APIRouter

from app.models.response import ApiResponse
from app.logging_config import cleanup_old_logs, get_log_disk_usage

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/status")
async def get_log_status() -> dict:
    """Get current log disk usage status."""
    return get_log_disk_usage()


@router.post("/cleanup")
async def trigger_log_cleanup(max_age_days: int = 30) -> ApiResponse:
    """Trigger manual cleanup of old log files.

    Args:
        max_age_days: Delete logs older than this many days
    """
    deleted_count = cleanup_old_logs(max_age_days)
    return ApiResponse(
        success=True,
        message=f"Cleaned up {deleted_count} old log files",
        data={"deleted_count": deleted_count}
    )
