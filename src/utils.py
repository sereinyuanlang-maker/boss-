"""工具函数模块"""

import random
import re
import string
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar

from src.logger import logger

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """重试装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 1
            current_delay = delay
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    logger.warning(
                        f"{func.__name__} 第 {attempt} 次尝试失败: {e}, "
                        f"{current_delay:.1f}秒后重试..."
                    )
                    if on_retry:
                        on_retry(attempt, e)
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            return None  # type: ignore
        return wrapper
    return decorator


def generate_random_string(length: int = 8) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """生成随机邮箱"""
    return f"{generate_random_string(10)}@example.com"


def parse_salary_range(salary_str: str) -> tuple:
    """解析薪资范围，返回 (min, max)"""
    numbers = re.findall(r'(\d+)', salary_str)
    if not numbers:
        return (0, 0)
    nums = [int(n) for n in numbers]
    return (nums[0], nums[-1])


def format_datetime(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def safe_get(d: dict, *keys, default: Any = None) -> Any:
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def is_within_business_hours(
    start_hour: int = 9,
    end_hour: int = 18,
    timezone_offset: int = 8,
) -> bool:
    """检查当前时间是否在业务时间内"""
    now = datetime.utcnow() + timedelta(hours=timezone_offset)
    return start_hour <= now.hour < end_hour


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def calculate_success_rate(success: int, total: int) -> float:
    """计算成功率"""
    if total == 0:
        return 0.0
    return round(success / total * 100, 2)


def sleep_with_jitter(base_seconds: float, jitter_ratio: float = 0.2):
    """带抖动的睡眠"""
    jitter = base_seconds * jitter_ratio
    sleep_time = base_seconds + random.uniform(-jitter, jitter)
    sleep_time = max(0.1, sleep_time)
    time.sleep(sleep_time)


def mask_sensitive_info(text: str, visible_chars: int = 3) -> str:
    """脱敏处理"""
    if not text or len(text) <= visible_chars * 2:
        return "*" * len(text)
    return text[:visible_chars] + "*" * (len(text) - visible_chars * 2) + text[-visible_chars:]


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    return bool(re.match(r'^1[3-9]\d{9}$', phone))


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
