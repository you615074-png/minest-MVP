"""
指数退避重试装饰器。
"""
import time
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    OSError,
)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    exceptions: tuple = RETRYABLE_EXCEPTIONS,
):
    """
    指数退避重试装饰器。

    参数:
        max_attempts: 最大尝试次数 (含首次)
        base_delay: 初始延迟 (秒)
        backoff_factor: 延迟倍增系数
        max_delay: 最大延迟上限 (秒)
        exceptions: 触发重试的异常类型元组
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"[retry] {func.__name__} 第 {attempt}/{max_attempts} 次失败: {e}. "
                        f"等待 {delay:.1f} 秒后重试..."
                    )
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
