import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

JSON_LOG_FORMAT = (
    '{{"time": "{time:YYYY-MM-DD HH:mm:ss}", '
    '"level": "{level}", '
    '"name": "{name}", '
    '"function": "{function}", '
    '"line": {line}, '
    '"message": "{message}"}}'
)


def setup_logger(
    log_file: str = "boss_auto_apply.log",
    json_log_file: Optional[str] = "boss_auto_apply.jsonl",
    rotation: str = "10 MB",
    retention: str = "30 days",
    level: str = "INFO",
    console_level: Optional[str] = None,
    file_level: Optional[str] = None,
):
    """配置日志系统

    Args:
        log_file: 普通日志文件名
        json_log_file: JSON格式日志文件名，None表示不记录
        rotation: 日志轮转大小
        retention: 日志保留时间
        level: 默认日志级别
        console_level: 控制台日志级别，默认与level相同
        file_level: 文件日志级别，默认与level相同
    """
    logger.remove()

    console_level = console_level or level
    file_level = file_level or level

    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=console_level,
        colorize=True,
    )

    log_path = LOG_DIR / log_file
    logger.add(
        str(log_path),
        format=LOG_FORMAT,
        level=file_level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    if json_log_file:
        json_log_path = LOG_DIR / json_log_file
        logger.add(
            str(json_log_path),
            format=JSON_LOG_FORMAT,
            level=file_level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            serialize=False,
        )

    logger.info(f"日志系统初始化完成，日志目录: {LOG_DIR}")
    return logger


def get_logger(name: Optional[str] = None):
    """获取带名称的logger"""
    if name:
        return logger.bind(name=name)
    return logger


logger = setup_logger()
