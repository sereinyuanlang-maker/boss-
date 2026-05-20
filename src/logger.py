import os
import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger(
    log_file: str = "boss_auto_apply.log",
    rotation: str = "10 MB",
    retention: str = "30 days",
    level: str = "INFO",
):
    logger.remove()

    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=level,
        colorize=True,
    )

    log_path = LOG_DIR / log_file
    logger.add(
        str(log_path),
        format=LOG_FORMAT,
        level=level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )

    return logger


logger = setup_logger()
