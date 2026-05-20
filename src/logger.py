import sys
from pathlib import Path
from loguru import logger
from src.config_manager import ConfigManager


def setup_logger(config: ConfigManager):
    log_config = config.config.logging
    log_file = Path(log_config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level=log_config.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    logger.add(
        log_file,
        level=log_config.level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=log_config.max_size,
        retention=log_config.backup_count,
        encoding="utf-8"
    )

    return logger
