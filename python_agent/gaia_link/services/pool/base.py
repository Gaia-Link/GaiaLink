"""
Pool 服務抽象基類

定義資金池查詢服務的接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from gaia_link.services.pool.models import (
    PoolInfo,
    PoolListResult,
    PoolRecommendation,
)


class PoolService(ABC):
    """
    資金池服務抽象基類

    定義查詢資金池的標準接口，支援 Mock 和真實實作切換。
    """

    @abstractmethod
    async def get_pool(self, pool_id: str) -> Optional[PoolInfo]:
        """
        獲取單個資金池信息

        Args:
            pool_id: 資金池 ID

        Returns:
            PoolInfo: 資金池信息，不存在則返回 None
        """
        pass

    @abstractmethod
    async def list_pools(self, active_only: bool = True) -> PoolListResult:
        """
        列出所有資金池

        Args:
            active_only: 是否只返回啟用的資金池

        Returns:
            PoolListResult: 資金池列表結果
        """
        pass

    @abstractmethod
    async def get_pool_recommendation(
        self, pool: PoolInfo
    ) -> PoolRecommendation:
        """
        獲取資金池建議

        根據資金池狀態生成操作建議。

        Args:
            pool: 資金池信息

        Returns:
            PoolRecommendation: 資金池建議
        """
        pass
