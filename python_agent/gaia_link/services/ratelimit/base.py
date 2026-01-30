"""
Rate Limiting 服務抽象基類

提供 Token Bucket 算法的抽象介面，支援 Mock 和 Redis 實作切換
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RateLimitResult(str, Enum):
    """Rate Limit 檢查結果"""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


@dataclass
class RateLimitStatus:
    """Rate Limit 狀態"""

    result: RateLimitResult
    remaining_tokens: int
    reset_at: datetime
    retry_after_seconds: Optional[float] = None
    limit: int = 60
    window_seconds: int = 60

    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "result": self.result.value,
            "allowed": self.result == RateLimitResult.ALLOWED,
            "remaining_tokens": self.remaining_tokens,
            "reset_at": self.reset_at.isoformat(),
            "retry_after_seconds": self.retry_after_seconds,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
        }


@dataclass
class RateLimitConfig:
    """Rate Limit 配置"""

    requests_per_minute: int = 60
    burst_size: Optional[int] = None  # 如果為 None，使用 requests_per_minute

    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.requests_per_minute

    @classmethod
    def from_settings(cls, settings) -> "RateLimitConfig":
        """從 Settings 建立配置"""
        return cls(
            requests_per_minute=settings.rate_limit_requests_per_minute,
        )


class RateLimiter(ABC):
    """
    Rate Limiter 抽象基類

    使用 Token Bucket 算法限制請求頻率
    """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """服務名稱"""
        pass

    @abstractmethod
    async def check(self, key: str, cost: int = 1) -> RateLimitStatus:
        """
        檢查請求是否被允許

        Args:
            key: 識別鍵（如 user_id, ip_address）
            cost: 此請求消耗的 token 數量

        Returns:
            RateLimitStatus: 包含是否允許和剩餘配額
        """
        pass

    @abstractmethod
    async def consume(self, key: str, cost: int = 1) -> RateLimitStatus:
        """
        消耗 token 並返回狀態

        Args:
            key: 識別鍵
            cost: 消耗的 token 數量

        Returns:
            RateLimitStatus: 消耗後的狀態
        """
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """
        重置指定 key 的限制

        Args:
            key: 識別鍵
        """
        pass

    @abstractmethod
    async def get_status(self, key: str) -> RateLimitStatus:
        """
        獲取當前狀態（不消耗 token）

        Args:
            key: 識別鍵

        Returns:
            RateLimitStatus: 當前狀態
        """
        pass
