"""
Polymarket 服務層

提供 Polymarket API 的抽象，支援 Mock 和 Real 實作切換
"""

from gaia_link.services.polymarket.base import (
    PolymarketService,
    MarketData,
    CrisisSearchResult,
)
from gaia_link.services.polymarket.mock_polymarket import MockPolymarketService


def get_real_polymarket_service(*args, **kwargs):
    """Factory function for RealPolymarketService (避免直接導入 aiohttp)"""
    from gaia_link.services.polymarket.real_polymarket import RealPolymarketService

    return RealPolymarketService(*args, **kwargs)


__all__ = [
    "PolymarketService",
    "MarketData",
    "CrisisSearchResult",
    "MockPolymarketService",
    "get_real_polymarket_service",
]
