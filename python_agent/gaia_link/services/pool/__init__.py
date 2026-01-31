"""
Pool 服務層

提供資金池查詢的服務抽象，支援 Mock 和真實實作切換。

環境變數控制:
- USE_BLOCKCHAIN=true: 使用真實區塊鏈服務 (未來實現)
- USE_BLOCKCHAIN=false (默認): 使用 Mock 服務
"""

import logging
from typing import Optional

from gaia_link.services.pool.models import (
    VaultType,
    CreatorType,
    RecommendationPriority,
    PoolInfo,
    PoolListResult,
    PoolRecommendation,
    YieldInfo,
)
from gaia_link.services.pool.base import PoolService
from gaia_link.services.pool.mock_pool import MockPoolService

logger = logging.getLogger(__name__)

# 服務實例 (延遲初始化)
_pool_service: Optional[PoolService] = None


def get_pool_service() -> PoolService:
    """
    獲取 PoolService 實例

    目前默認使用 MockPoolService。
    未來可根據環境變數切換到真實區塊鏈查詢服務。

    Returns:
        PoolService: 資金池服務實例
    """
    global _pool_service
    if _pool_service is None:
        _pool_service = MockPoolService()
        logger.info("[MOCK] Using MockPoolService")
    return _pool_service


def set_pool_service(service: PoolService) -> None:
    """
    設置自定義 PoolService 實例

    用於測試或切換實作。

    Args:
        service: 自定義服務實例
    """
    global _pool_service
    _pool_service = service


def reset_pool_service() -> None:
    """
    重置服務實例

    用於測試時重置狀態。
    """
    global _pool_service
    _pool_service = None


__all__ = [
    # Models
    "VaultType",
    "CreatorType",
    "RecommendationPriority",
    "PoolInfo",
    "PoolListResult",
    "PoolRecommendation",
    "YieldInfo",
    # Abstract Service
    "PoolService",
    # Mock Implementation
    "MockPoolService",
    # Factory Functions
    "get_pool_service",
    "set_pool_service",
    "reset_pool_service",
]
