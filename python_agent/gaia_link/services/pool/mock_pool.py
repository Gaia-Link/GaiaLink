"""
Mock Pool 服務

提供 Demo 數據的資金池查詢服務。
"""

from typing import Dict, Optional

from gaia_link.services.pool.base import PoolService
from gaia_link.services.pool.models import (
    PoolInfo,
    PoolListResult,
    PoolRecommendation,
    VaultType,
    CreatorType,
    RecommendationPriority,
)


class MockPoolService(PoolService):
    """
    Mock 資金池服務

    提供預設的 Demo 數據，用於開發和測試。
    與原 analyze_pool.py 的硬編碼數據保持一致。
    """

    def __init__(self):
        """初始化 Mock 數據"""
        self._pools: Dict[str, PoolInfo] = {}
        self._initialize_demo_data()

    def _initialize_demo_data(self):
        """初始化 Demo 數據 - 與原 analyze_pool.py 保持一致"""
        demo_pools = [
            PoolInfo(
                vault_id="vault_001",
                name="Turkey Earthquake Relief",
                vault_type=VaultType.YIELD,
                creator_type=CreatorType.ORGANIZATION,
                beneficiary_org_id="org_redcross",
                target_amount=100000.0,
                current_amount=65000.0,
                yield_earned=1250.0,
                region="Turkey",
                is_active=True,
                created_at="2024-01-15",
            ),
            PoolInfo(
                vault_id="vault_002",
                name="Philippines Typhoon Aid",
                vault_type=VaultType.DIRECT,
                creator_type=CreatorType.COMMUNITY,
                beneficiary_org_id="org_unicef",
                target_amount=50000.0,
                current_amount=32000.0,
                yield_earned=0.0,
                region="Philippines",
                is_active=True,
                created_at="2024-02-01",
            ),
            PoolInfo(
                vault_id="vault_003",
                name="Gaza Humanitarian Fund",
                vault_type=VaultType.YIELD,
                creator_type=CreatorType.ORGANIZATION,
                beneficiary_org_id="org_who",
                target_amount=200000.0,
                current_amount=180000.0,
                yield_earned=4500.0,
                region="Gaza",
                is_active=True,
                created_at="2024-01-01",
            ),
        ]

        for pool in demo_pools:
            self._pools[pool.vault_id] = pool

    async def get_pool(self, pool_id: str) -> Optional[PoolInfo]:
        """
        獲取單個資金池信息

        Args:
            pool_id: 資金池 ID

        Returns:
            PoolInfo: 資金池信息，不存在則返回 None
        """
        if not pool_id:
            return None
        return self._pools.get(pool_id)

    async def list_pools(self, active_only: bool = True) -> PoolListResult:
        """
        列出所有資金池

        Args:
            active_only: 是否只返回啟用的資金池

        Returns:
            PoolListResult: 資金池列表結果
        """
        pools = list(self._pools.values())

        if active_only:
            pools = [p for p in pools if p.is_active]

        total_value = sum(p.current_amount for p in pools)
        total_yield = sum(p.yield_earned for p in pools)

        return PoolListResult(
            pools=pools,
            total_value=total_value,
            total_yield=total_yield,
        )

    async def get_pool_recommendation(
        self, pool: PoolInfo
    ) -> PoolRecommendation:
        """
        獲取資金池建議

        根據資金池狀態生成操作建議。
        邏輯與原 analyze_pool.py 的 get_pool_recommendation 保持一致。

        Args:
            pool: 資金池信息

        Returns:
            PoolRecommendation: 資金池建議
        """
        recommendations = []
        priority = RecommendationPriority.NORMAL

        # 計算進度
        if pool.target_amount > 0:
            progress = pool.current_amount / pool.target_amount
        else:
            progress = 0

        # 根據進度設置優先級和建議
        if progress >= 0.9:
            recommendations.append(
                "Pool is nearly at target. Consider opening a new pool."
            )
            priority = RecommendationPriority.LOW
        elif progress < 0.3:
            recommendations.append(
                "Pool needs more funding. Consider promoting on social media."
            )
            priority = RecommendationPriority.HIGH

        # Yield 池有收益時建議分配
        if pool.vault_type == VaultType.YIELD and pool.yield_earned > 0:
            recommendations.append(
                f"Yield earned: ${pool.yield_earned}. "
                "Consider distributing to beneficiary."
            )

        return PoolRecommendation(
            priority=priority,
            items=recommendations,
        )
