"""
Polymarket 服務抽象基類

定義 Polymarket API 操作的介面
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MarketData:
    """Polymarket 市場數據"""

    market_id: str
    question: str
    description: str = ""
    category: str = ""
    probability: float = 0.0  # Yes 的機率 (0-1)
    volume: float = 0.0  # 交易量 (USD)
    liquidity: float = 0.0  # 流動性 (USD)
    source_url: Optional[str] = None
    closes_at: Optional[str] = None
    resolved: bool = False
    outcome: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "event_id": self.market_id,
            "title": self.question,
            "probability": self.probability,
            "volume": self.volume,
            "source_url": self.source_url,
        }


@dataclass
class CrisisSearchResult:
    """危機搜尋結果"""

    found: bool
    markets: list[MarketData] = field(default_factory=list)
    region_name: Optional[str] = None
    confidence: int = 0  # 0-100
    status: str = "UNKNOWN"  # VERIFIED, SUSPICIOUS, SCAM

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "found": self.found,
            "markets": [m.to_dict() for m in self.markets],
            "region_name": self.region_name,
            "confidence": self.confidence,
            "status": self.status,
        }


class PolymarketService(ABC):
    """
    Polymarket 服務抽象基類

    定義與 Polymarket 預測市場互動的標準介面
    """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """服務名稱 (mock/real)"""
        pass

    @abstractmethod
    async def search_markets(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> list[MarketData]:
        """
        搜尋市場

        Args:
            query: 搜尋關鍵字
            limit: 返回結果數量上限
            category: 類別過濾 (可選)

        Returns:
            匹配的市場列表
        """
        pass

    @abstractmethod
    async def get_market(self, market_id: str) -> Optional[MarketData]:
        """
        獲取特定市場詳情

        Args:
            market_id: 市場 ID

        Returns:
            市場數據，如果不存在則返回 None
        """
        pass

    @abstractmethod
    async def search_crisis_by_location(
        self,
        lat: float,
        long: float,
        radius_km: float = 500.0,
    ) -> CrisisSearchResult:
        """
        根據地理位置搜尋危機相關市場

        Args:
            lat: 緯度
            long: 經度
            radius_km: 搜尋半徑（公里）

        Returns:
            危機搜尋結果
        """
        pass

    @abstractmethod
    async def get_crisis_keywords(self) -> list[str]:
        """
        獲取危機相關的搜尋關鍵字列表

        Returns:
            關鍵字列表
        """
        pass

    def is_crisis_related(self, market: MarketData) -> bool:
        """
        判斷市場是否與危機相關

        Args:
            market: 市場數據

        Returns:
            是否為危機相關市場
        """
        crisis_keywords = [
            "earthquake",
            "hurricane",
            "typhoon",
            "flood",
            "tsunami",
            "volcano",
            "wildfire",
            "pandemic",
            "war",
            "conflict",
            "ceasefire",
            "humanitarian",
            "disaster",
            "emergency",
            "crisis",
            "refugee",
            "famine",
            "drought",
        ]

        text_to_check = f"{market.question} {market.description}".lower()

        for keyword in crisis_keywords:
            if keyword in text_to_check:
                return True

        for tag in market.tags:
            if tag.lower() in crisis_keywords:
                return True

        return False
