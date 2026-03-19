"""Logging configuration with automatic cleanup."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from app.config import get_settings


def setup_logging() -> None:
    """Configure loguru with file rotation and automatic cleanup."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )

    # Create log directory if not exists
    log_path = settings.log_path
    log_path.mkdir(parents=True, exist_ok=True)

    # Main log file with rotation and retention
    logger.add(
        log_path / "smartlamp_{time:YYYY-MM-DD}.log",
        rotation=settings.log_rotation,  # Rotate when file reaches specified size
        retention=settings.log_retention,  # Keep logs for specified duration
        compression=settings.log_compression,  # Compress rotated logs
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        enqueue=True,  # Thread-safe logging
        serialize=False,
    )

    # Error log file - separate file for errors
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        enqueue=True,
        filter=lambda record: record["level"].name == "ERROR",
    )

    # API access log - for HTTP requests
    logger.add(
        log_path / "access_{time:YYYY-MM-DD}.log",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        enqueue=True,
        filter=lambda record: "api_access" in record["extra"],
    )

    logger.info(f"Logging configured: dir={log_path}, rotation={settings.log_rotation}, retention={settings.log_retention}")


def get_log_disk_usage() -> dict:
    """Get current log disk usage statistics.

    Returns:
        Dict with total_size, file_count, and oldest_file info
    """
    settings = get_settings()
    log_path = settings.log_path

    if not log_path.exists():
        return {"total_size": 0, "file_count": 0, "oldest_file": None}

    log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.zip"))

    if not log_files:
        return {"total_size": 0, "file_count": 0, "oldest_file": None}

    total_size = sum(f.stat().st_size for f in log_files)
    oldest = min(log_files, key=lambda f: f.stat().st_mtime)

    return {
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": len(log_files),
        "oldest_file": str(oldest),
        "oldest_file_age_days": (datetime.now().timestamp() - oldest.stat().st_mtime) / 86400,
    }


def cleanup_old_logs(max_age_days: int = 30) -> int:
    """Manually clean up logs older than specified days.

    Args:
        max_age_days: Maximum age of log files to keep

    Returns:
        Number of files deleted
    """
    settings = get_settings()
    log_path = settings.log_path

    if not log_path.exists():
        return 0

    cutoff_time = datetime.now().timestamp() - (max_age_days * 86400)
    deleted_count = 0

    for log_file in log_path.glob("*.log") + list(log_path.glob("*.zip")):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

    return deleted_count
