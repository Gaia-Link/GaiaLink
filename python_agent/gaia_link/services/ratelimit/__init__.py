"""
Rate Limiting 服務

提供 Token Bucket 算法的請求限制功能
"""

from gaia_link.services.ratelimit.base import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStatus,
)
from gaia_link.services.ratelimit.memory_ratelimit import InMemoryRateLimiter

__all__ = [
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitStatus",
    "InMemoryRateLimiter",
    "get_in_memory_rate_limiter",
]


def get_in_memory_rate_limiter(*args, **kwargs):
    """工廠函數：創建 InMemoryRateLimiter 實例"""
    return InMemoryRateLimiter(*args, **kwargs)
