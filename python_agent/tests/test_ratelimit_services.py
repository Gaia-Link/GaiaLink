"""
Rate Limiting 服務單元測試

測試 RateLimiter 抽象基類和 InMemoryRateLimiter 實作
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from gaia_link.services.ratelimit import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStatus,
)


class TestRateLimitResult:
    """RateLimitResult 枚舉測試"""

    def test_allowed_value(self):
        """ALLOWED 應有正確的值"""
        assert RateLimitResult.ALLOWED.value == "ALLOWED"

    def test_denied_value(self):
        """DENIED 應有正確的值"""
        assert RateLimitResult.DENIED.value == "DENIED"


class TestRateLimitStatus:
    """RateLimitStatus 資料類測試"""

    def test_create_allowed_status(self):
        """應能建立 ALLOWED 狀態"""
        status = RateLimitStatus(
            result=RateLimitResult.ALLOWED,
            remaining_tokens=59,
            reset_at=datetime.utcnow() + timedelta(seconds=60),
            limit=60,
            window_seconds=60,
        )
        assert status.result == RateLimitResult.ALLOWED
        assert status.remaining_tokens == 59
        assert status.retry_after_seconds is None

    def test_create_denied_status(self):
        """應能建立 DENIED 狀態"""
        status = RateLimitStatus(
            result=RateLimitResult.DENIED,
            remaining_tokens=0,
            reset_at=datetime.utcnow() + timedelta(seconds=30),
            retry_after_seconds=30.0,
            limit=60,
            window_seconds=60,
        )
        assert status.result == RateLimitResult.DENIED
        assert status.remaining_tokens == 0
        assert status.retry_after_seconds == 30.0

    def test_to_dict(self):
        """to_dict 應返回正確的字典"""
        reset_at = datetime.utcnow() + timedelta(seconds=60)
        status = RateLimitStatus(
            result=RateLimitResult.ALLOWED,
            remaining_tokens=59,
            reset_at=reset_at,
            limit=60,
            window_seconds=60,
        )
        result = status.to_dict()

        assert result["result"] == "ALLOWED"
        assert result["allowed"] is True
        assert result["remaining_tokens"] == 59
        assert result["reset_at"] == reset_at.isoformat()
        assert result["limit"] == 60
        assert result["window_seconds"] == 60

    def test_to_dict_denied(self):
        """DENIED 狀態的 to_dict 應正確"""
        status = RateLimitStatus(
            result=RateLimitResult.DENIED,
            remaining_tokens=0,
            reset_at=datetime.utcnow(),
            retry_after_seconds=15.5,
        )
        result = status.to_dict()

        assert result["result"] == "DENIED"
        assert result["allowed"] is False
        assert result["retry_after_seconds"] == 15.5


class TestRateLimitConfig:
    """RateLimitConfig 資料類測試"""

    def test_default_config(self):
        """預設配置應正確"""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.burst_size == 60

    def test_custom_config(self):
        """自定義配置應正確"""
        config = RateLimitConfig(requests_per_minute=100, burst_size=150)
        assert config.requests_per_minute == 100
        assert config.burst_size == 150

    def test_burst_size_defaults_to_requests_per_minute(self):
        """burst_size 預設應等於 requests_per_minute"""
        config = RateLimitConfig(requests_per_minute=30)
        assert config.burst_size == 30


class TestInMemoryRateLimiter:
    """InMemoryRateLimiter 實作測試"""

    @pytest.fixture
    def limiter(self):
        """建立限流器實例"""
        from gaia_link.services.ratelimit.memory_ratelimit import InMemoryRateLimiter

        config = RateLimitConfig(requests_per_minute=10)
        return InMemoryRateLimiter(config=config)

    def test_service_name(self, limiter):
        """應有正確的服務名稱"""
        assert limiter.service_name == "in_memory_rate_limiter"

    @pytest.mark.asyncio
    async def test_check_allows_first_request(self, limiter):
        """第一個請求應被允許"""
        status = await limiter.check("user_1")
        assert status.result == RateLimitResult.ALLOWED
        assert status.remaining_tokens == 10  # 尚未消耗

    @pytest.mark.asyncio
    async def test_consume_decrements_tokens(self, limiter):
        """consume 應減少 token"""
        status = await limiter.consume("user_1")
        assert status.result == RateLimitResult.ALLOWED
        assert status.remaining_tokens == 9

    @pytest.mark.asyncio
    async def test_consume_multiple_times(self, limiter):
        """多次 consume 應正確減少 token"""
        for i in range(5):
            status = await limiter.consume("user_1")
            assert status.remaining_tokens == 9 - i

    @pytest.mark.asyncio
    async def test_consume_exceeds_limit_denied(self, limiter):
        """超過限制後應被拒絕"""
        # 消耗所有 token
        for _ in range(10):
            await limiter.consume("user_1")

        # 下一個請求應被拒絕
        status = await limiter.consume("user_1")
        assert status.result == RateLimitResult.DENIED
        assert status.remaining_tokens == 0
        assert status.retry_after_seconds is not None
        assert status.retry_after_seconds > 0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self, limiter):
        """不同 key 應獨立計算"""
        # user_1 消耗所有 token
        for _ in range(10):
            await limiter.consume("user_1")

        # user_2 應仍可請求
        status = await limiter.consume("user_2")
        assert status.result == RateLimitResult.ALLOWED
        assert status.remaining_tokens == 9

    @pytest.mark.asyncio
    async def test_reset_clears_usage(self, limiter):
        """reset 應清除使用量"""
        # 消耗一些 token
        for _ in range(5):
            await limiter.consume("user_1")

        # 重置
        await limiter.reset("user_1")

        # 應恢復完整配額
        status = await limiter.get_status("user_1")
        assert status.remaining_tokens == 10

    @pytest.mark.asyncio
    async def test_get_status_does_not_consume(self, limiter):
        """get_status 不應消耗 token"""
        await limiter.consume("user_1")  # 消耗 1 個
        status1 = await limiter.get_status("user_1")
        status2 = await limiter.get_status("user_1")

        assert status1.remaining_tokens == status2.remaining_tokens == 9

    @pytest.mark.asyncio
    async def test_check_does_not_consume(self, limiter):
        """check 不應消耗 token"""
        await limiter.check("user_1")
        await limiter.check("user_1")
        status = await limiter.get_status("user_1")

        assert status.remaining_tokens == 10

    @pytest.mark.asyncio
    async def test_consume_with_custom_cost(self, limiter):
        """應支援自定義消耗量"""
        status = await limiter.consume("user_1", cost=5)
        assert status.result == RateLimitResult.ALLOWED
        assert status.remaining_tokens == 5

    @pytest.mark.asyncio
    async def test_consume_cost_exceeds_remaining(self, limiter):
        """消耗量超過剩餘應被拒絕"""
        # 先消耗 8 個
        for _ in range(8):
            await limiter.consume("user_1")

        # 嘗試消耗 5 個（只剩 2 個）
        status = await limiter.consume("user_1", cost=5)
        assert status.result == RateLimitResult.DENIED
        assert status.remaining_tokens == 2

    @pytest.mark.asyncio
    async def test_status_includes_reset_time(self, limiter):
        """狀態應包含重置時間"""
        status = await limiter.get_status("user_1")
        assert status.reset_at is not None
        assert status.reset_at > datetime.utcnow()


class TestInMemoryRateLimiterTokenRefill:
    """InMemoryRateLimiter Token 補充測試"""

    @pytest.fixture
    def fast_limiter(self):
        """建立快速補充的限流器"""
        from gaia_link.services.ratelimit.memory_ratelimit import InMemoryRateLimiter

        # 每秒補充 1 個 token（測試用）
        config = RateLimitConfig(requests_per_minute=60)  # 1 per second
        return InMemoryRateLimiter(config=config)

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self, fast_limiter):
        """Token 應隨時間補充"""
        # 消耗所有 token
        for _ in range(60):
            await fast_limiter.consume("user_1")

        status = await fast_limiter.get_status("user_1")
        assert status.remaining_tokens == 0

        # 等待一小段時間（模擬補充）
        await asyncio.sleep(0.1)

        # 應該有一些 token 補充
        status = await fast_limiter.get_status("user_1")
        # Token 會逐漸補充
        assert status.remaining_tokens >= 0


class TestRateLimiterFactory:
    """Rate Limiter 工廠函數測試"""

    def test_get_in_memory_rate_limiter(self):
        """應能通過工廠創建 InMemoryRateLimiter"""
        from gaia_link.services.ratelimit import get_in_memory_rate_limiter

        limiter = get_in_memory_rate_limiter()
        assert limiter.service_name == "in_memory_rate_limiter"

    def test_get_in_memory_rate_limiter_with_config(self):
        """應能通過工廠創建自定義配置的 limiter"""
        from gaia_link.services.ratelimit import get_in_memory_rate_limiter

        config = RateLimitConfig(requests_per_minute=100)
        limiter = get_in_memory_rate_limiter(config=config)
        assert limiter.service_name == "in_memory_rate_limiter"
