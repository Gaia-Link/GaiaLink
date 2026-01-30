"""
InMemory Rate Limiter 實作

使用 Token Bucket 算法的內存實作，適用於單實例應用
"""

from datetime import datetime, timedelta
from typing import Optional

from gaia_link.services.ratelimit.base import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStatus,
)


class TokenBucket:
    """Token Bucket 實作"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化 Token Bucket

        Args:
            capacity: 桶容量（最大 token 數）
            refill_rate: 每秒補充的 token 數
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_update = datetime.utcnow()

    def _refill(self) -> None:
        """補充 token"""
        now = datetime.utcnow()
        elapsed = (now - self.last_update).total_seconds()
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

    def consume(self, cost: int = 1) -> tuple[bool, int]:
        """
        嘗試消耗 token

        Args:
            cost: 消耗的 token 數量

        Returns:
            tuple[bool, int]: (是否成功, 剩餘 token 數)
        """
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True, int(self.tokens)
        return False, int(self.tokens)

    def get_remaining(self) -> int:
        """獲取剩餘 token 數"""
        self._refill()
        return int(self.tokens)

    def reset(self) -> None:
        """重置桶"""
        self.tokens = float(self.capacity)
        self.last_update = datetime.utcnow()

    def get_time_to_refill(self, cost: int = 1) -> float:
        """
        獲取恢復足夠 token 所需的時間（秒）

        Args:
            cost: 需要的 token 數量

        Returns:
            float: 等待時間（秒）
        """
        self._refill()
        if self.tokens >= cost:
            return 0.0
        needed = cost - self.tokens
        return needed / self.refill_rate


class InMemoryRateLimiter(RateLimiter):
    """
    內存 Rate Limiter 實作

    使用 Token Bucket 算法，適用於單實例應用
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        初始化 Rate Limiter

        Args:
            config: Rate Limit 配置，如未提供則使用預設值
        """
        self._config = config or RateLimitConfig()
        self._buckets: dict[str, TokenBucket] = {}

    @property
    def service_name(self) -> str:
        """服務名稱"""
        return "in_memory_rate_limiter"

    def _get_bucket(self, key: str) -> TokenBucket:
        """獲取或創建 Token Bucket"""
        if key not in self._buckets:
            refill_rate = self._config.requests_per_minute / 60.0  # 每秒補充
            self._buckets[key] = TokenBucket(
                capacity=self._config.burst_size,
                refill_rate=refill_rate,
            )
        return self._buckets[key]

    def _build_status(
        self,
        result: RateLimitResult,
        remaining: int,
        retry_after: Optional[float] = None,
    ) -> RateLimitStatus:
        """建立狀態物件"""
        return RateLimitStatus(
            result=result,
            remaining_tokens=remaining,
            reset_at=datetime.utcnow() + timedelta(seconds=60),
            retry_after_seconds=retry_after,
            limit=self._config.requests_per_minute,
            window_seconds=60,
        )

    async def check(self, key: str, cost: int = 1) -> RateLimitStatus:
        """
        檢查請求是否被允許（不消耗 token）

        Args:
            key: 識別鍵
            cost: 請求消耗量

        Returns:
            RateLimitStatus: 檢查結果
        """
        bucket = self._get_bucket(key)
        remaining = bucket.get_remaining()

        if remaining >= cost:
            return self._build_status(RateLimitResult.ALLOWED, remaining)
        else:
            retry_after = bucket.get_time_to_refill(cost)
            return self._build_status(RateLimitResult.DENIED, remaining, retry_after)

    async def consume(self, key: str, cost: int = 1) -> RateLimitStatus:
        """
        消耗 token 並返回狀態

        Args:
            key: 識別鍵
            cost: 消耗量

        Returns:
            RateLimitStatus: 消耗後狀態
        """
        bucket = self._get_bucket(key)
        allowed, remaining = bucket.consume(cost)

        if allowed:
            return self._build_status(RateLimitResult.ALLOWED, remaining)
        else:
            retry_after = bucket.get_time_to_refill(cost)
            return self._build_status(RateLimitResult.DENIED, remaining, retry_after)

    async def reset(self, key: str) -> None:
        """
        重置指定 key 的限制

        Args:
            key: 識別鍵
        """
        if key in self._buckets:
            self._buckets[key].reset()
        else:
            # 創建新的完整桶
            self._get_bucket(key)

    async def get_status(self, key: str) -> RateLimitStatus:
        """
        獲取當前狀態（不消耗 token）

        Args:
            key: 識別鍵

        Returns:
            RateLimitStatus: 當前狀態
        """
        bucket = self._get_bucket(key)
        remaining = bucket.get_remaining()
        return self._build_status(RateLimitResult.ALLOWED, remaining)
