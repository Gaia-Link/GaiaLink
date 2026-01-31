"""
Pool Service 測試

TDD: RED -> GREEN -> REFACTOR
"""

import pytest
from typing import List

from gaia_link.services.pool import (
    # Models
    VaultType,
    CreatorType,
    RecommendationPriority,
    PoolInfo,
    PoolListResult,
    PoolRecommendation,
    YieldInfo,
    # Service
    PoolService,
    MockPoolService,
    # Factory functions
    get_pool_service,
    set_pool_service,
    reset_pool_service,
)


# =============================================================================
# Models Tests
# =============================================================================


class TestPoolInfo:
    """PoolInfo 數據模型測試"""

    def test_progress_percent_calculation(self):
        """測試進度百分比計算"""
        pool = PoolInfo(
            vault_id="vault_001",
            name="Test Pool",
            vault_type=VaultType.YIELD,
            creator_type=CreatorType.ORGANIZATION,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=65000.0,
            yield_earned=1250.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )
        assert pool.progress_percent == 65.0

    def test_progress_percent_zero_target(self):
        """測試目標金額為 0 時進度為 0"""
        pool = PoolInfo(
            vault_id="vault_001",
            name="Test Pool",
            vault_type=VaultType.DIRECT,
            creator_type=CreatorType.COMMUNITY,
            beneficiary_org_id="org_test",
            target_amount=0.0,
            current_amount=1000.0,
            yield_earned=0.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )
        assert pool.progress_percent == 0.0

    def test_remaining_amount_calculation(self):
        """測試剩餘金額計算"""
        pool = PoolInfo(
            vault_id="vault_001",
            name="Test Pool",
            vault_type=VaultType.YIELD,
            creator_type=CreatorType.ORGANIZATION,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=65000.0,
            yield_earned=1250.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )
        assert pool.remaining_amount == 35000.0

    def test_to_dict(self):
        """測試轉換為字典"""
        pool = PoolInfo(
            vault_id="vault_001",
            name="Test Pool",
            vault_type=VaultType.YIELD,
            creator_type=CreatorType.ORGANIZATION,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=65000.0,
            yield_earned=1250.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )
        data = pool.to_dict()
        assert data["vault_id"] == "vault_001"
        assert data["vault_type"] == "yield"
        assert data["creator_type"] == "organization"
        assert data["progress_percent"] == 65.0
        assert data["remaining_amount"] == 35000.0

    def test_from_dict(self):
        """測試從字典創建"""
        data = {
            "vault_id": "vault_002",
            "name": "Another Pool",
            "vault_type": "direct",
            "creator_type": "community",
            "beneficiary_org_id": "org_test2",
            "target_amount": 50000.0,
            "current_amount": 25000.0,
            "yield_earned": 0.0,
            "region": "Test2",
            "is_active": False,
            "created_at": "2024-02-01",
        }
        pool = PoolInfo.from_dict(data)
        assert pool.vault_id == "vault_002"
        assert pool.vault_type == VaultType.DIRECT
        assert pool.creator_type == CreatorType.COMMUNITY
        assert pool.is_active is False


class TestPoolListResult:
    """PoolListResult 數據模型測試"""

    def test_total_pools(self):
        """測試資金池數量"""
        pools = [
            PoolInfo(
                vault_id=f"vault_{i}",
                name=f"Pool {i}",
                vault_type=VaultType.YIELD,
                creator_type=CreatorType.ORGANIZATION,
                beneficiary_org_id="org_test",
                target_amount=100000.0,
                current_amount=50000.0,
                yield_earned=1000.0,
                region="Test",
                is_active=True,
                created_at="2024-01-15",
            )
            for i in range(3)
        ]
        result = PoolListResult(
            pools=pools,
            total_value=150000.0,
            total_yield=3000.0,
        )
        assert result.total_pools == 3

    def test_to_dict(self):
        """測試轉換為字典"""
        result = PoolListResult(
            pools=[],
            total_value=0.0,
            total_yield=0.0,
        )
        data = result.to_dict()
        assert data["pools"] == []
        assert data["total_value"] == 0.0
        assert data["total_pools"] == 0


class TestPoolRecommendation:
    """PoolRecommendation 數據模型測試"""

    def test_to_dict(self):
        """測試轉換為字典"""
        rec = PoolRecommendation(
            priority=RecommendationPriority.HIGH,
            items=["Item 1", "Item 2"],
        )
        data = rec.to_dict()
        assert data["priority"] == "HIGH"
        assert len(data["items"]) == 2


class TestYieldInfo:
    """YieldInfo 數據模型測試"""

    def test_to_dict_with_protocol(self):
        """測試轉換為字典 (有協議)"""
        info = YieldInfo(
            earned_usd=1250.0,
            apy_estimate=4.5,
            protocol="Euler",
        )
        data = info.to_dict()
        assert data["earned_usd"] == 1250.0
        assert data["apy_estimate"] == 4.5
        assert data["protocol"] == "Euler"

    def test_to_dict_without_protocol(self):
        """測試轉換為字典 (無協議)"""
        info = YieldInfo(
            earned_usd=0.0,
            apy_estimate=0.0,
            protocol=None,
        )
        data = info.to_dict()
        assert data["protocol"] is None


# =============================================================================
# MockPoolService Tests
# =============================================================================


class TestMockPoolService:
    """MockPoolService 測試"""

    @pytest.fixture
    def service(self):
        """創建服務實例"""
        return MockPoolService()

    @pytest.mark.asyncio
    async def test_get_pool_returns_correct_format(self, service):
        """測試 get_pool 返回正確格式"""
        result = await service.get_pool("vault_001")

        assert result is not None
        assert isinstance(result, PoolInfo)
        assert result.vault_id == "vault_001"
        assert result.name == "Turkey Earthquake Relief"
        assert result.vault_type == VaultType.YIELD
        assert result.creator_type == CreatorType.ORGANIZATION

    @pytest.mark.asyncio
    async def test_get_pool_not_found_returns_none(self, service):
        """測試 get_pool 不存在返回 None"""
        result = await service.get_pool("nonexistent_pool")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_pools_returns_all_pools(self, service):
        """測試 list_pools 返回所有池子"""
        result = await service.list_pools(active_only=False)

        assert isinstance(result, PoolListResult)
        assert len(result.pools) >= 3
        assert result.total_value > 0
        assert result.total_yield >= 0

    @pytest.mark.asyncio
    async def test_list_pools_active_only_filter(self, service):
        """測試 list_pools active_only 過濾"""
        result = await service.list_pools(active_only=True)

        assert isinstance(result, PoolListResult)
        for pool in result.pools:
            assert pool.is_active is True

    @pytest.mark.asyncio
    async def test_get_pool_recommendation_high_progress_low_priority(
        self, service
    ):
        """測試高進度返回 LOW 優先級"""
        # 創建一個高進度的池子 (>= 90%)
        pool = PoolInfo(
            vault_id="vault_high",
            name="High Progress Pool",
            vault_type=VaultType.YIELD,
            creator_type=CreatorType.ORGANIZATION,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=95000.0,  # 95%
            yield_earned=2000.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )

        recommendation = await service.get_pool_recommendation(pool)

        assert recommendation.priority == RecommendationPriority.LOW
        assert len(recommendation.items) > 0

    @pytest.mark.asyncio
    async def test_get_pool_recommendation_low_progress_high_priority(
        self, service
    ):
        """測試低進度返回 HIGH 優先級"""
        # 創建一個低進度的池子 (< 30%)
        pool = PoolInfo(
            vault_id="vault_low",
            name="Low Progress Pool",
            vault_type=VaultType.DIRECT,
            creator_type=CreatorType.COMMUNITY,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=20000.0,  # 20%
            yield_earned=0.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )

        recommendation = await service.get_pool_recommendation(pool)

        assert recommendation.priority == RecommendationPriority.HIGH
        assert len(recommendation.items) > 0

    @pytest.mark.asyncio
    async def test_get_pool_recommendation_normal_progress(self, service):
        """測試正常進度返回 NORMAL 優先級"""
        # 創建一個中間進度的池子 (30% - 90%)
        pool = PoolInfo(
            vault_id="vault_normal",
            name="Normal Progress Pool",
            vault_type=VaultType.YIELD,
            creator_type=CreatorType.ORGANIZATION,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=50000.0,  # 50%
            yield_earned=500.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )

        recommendation = await service.get_pool_recommendation(pool)

        assert recommendation.priority == RecommendationPriority.NORMAL

    @pytest.mark.asyncio
    async def test_get_pool_recommendation_yield_pool_has_distribution_advice(
        self, service
    ):
        """測試 yield 池有收益時建議分配"""
        pool = PoolInfo(
            vault_id="vault_yield",
            name="Yield Pool",
            vault_type=VaultType.YIELD,
            creator_type=CreatorType.ORGANIZATION,
            beneficiary_org_id="org_test",
            target_amount=100000.0,
            current_amount=50000.0,
            yield_earned=1500.0,  # 有收益
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )

        recommendation = await service.get_pool_recommendation(pool)

        # 應該包含收益分配建議
        has_yield_advice = any(
            "yield" in item.lower() or "distribute" in item.lower()
            for item in recommendation.items
        )
        assert has_yield_advice


# =============================================================================
# Factory Functions Tests
# =============================================================================


class TestFactoryFunctions:
    """工廠函數測試"""

    def setup_method(self):
        """每個測試前重置服務"""
        reset_pool_service()

    def teardown_method(self):
        """每個測試後重置服務"""
        reset_pool_service()

    def test_get_pool_service_returns_mock_by_default(self):
        """測試默認返回 MockPoolService"""
        service = get_pool_service()
        assert isinstance(service, MockPoolService)

    def test_get_pool_service_singleton(self):
        """測試單例模式"""
        service1 = get_pool_service()
        service2 = get_pool_service()
        assert service1 is service2

    def test_set_pool_service_custom(self):
        """測試設置自定義服務"""
        custom_service = MockPoolService()
        set_pool_service(custom_service)
        service = get_pool_service()
        assert service is custom_service

    def test_reset_pool_service(self):
        """測試重置服務"""
        service1 = get_pool_service()
        reset_pool_service()
        service2 = get_pool_service()
        assert service1 is not service2


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """邊界情況測試"""

    @pytest.fixture
    def service(self):
        """創建服務實例"""
        return MockPoolService()

    @pytest.mark.asyncio
    async def test_get_pool_empty_id(self, service):
        """測試空 ID"""
        result = await service.get_pool("")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_pool_special_characters(self, service):
        """測試特殊字符 ID"""
        result = await service.get_pool("vault_@#$%")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_pools_all_inactive(self, service):
        """測試所有池子都不活躍時"""
        # 這應該返回空列表
        # 由於 Mock 數據有活躍池子，這裡測試過濾邏輯正確
        result = await service.list_pools(active_only=True)
        assert isinstance(result, PoolListResult)
        # 驗證返回的都是活躍的
        for pool in result.pools:
            assert pool.is_active is True

    @pytest.mark.asyncio
    async def test_recommendation_zero_target(self, service):
        """測試目標金額為 0"""
        pool = PoolInfo(
            vault_id="vault_zero",
            name="Zero Target Pool",
            vault_type=VaultType.DIRECT,
            creator_type=CreatorType.COMMUNITY,
            beneficiary_org_id="org_test",
            target_amount=0.0,
            current_amount=0.0,
            yield_earned=0.0,
            region="Test",
            is_active=True,
            created_at="2024-01-15",
        )

        recommendation = await service.get_pool_recommendation(pool)

        # 應該不會崩潰，返回合理的建議
        assert isinstance(recommendation, PoolRecommendation)
