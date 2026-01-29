"""
MockPolymarketService - Polymarket Mock 實作

用於開發和測試，提供模擬的危機事件數據
"""

from typing import Optional

from gaia_link.services.polymarket.base import (
    PolymarketService,
    MarketData,
    CrisisSearchResult,
)


# 模擬的危機區域數據
MOCK_CRISIS_REGIONS = {
    "turkey_syria_earthquake": {
        "name": "Turkey-Syria Earthquake Zone",
        "lat_range": (36.0, 39.0),
        "long_range": (35.0, 42.0),
        "markets": [
            MarketData(
                market_id="poly_eq_turkey_2023",
                question="Will there be another major earthquake (>6.0) in Turkey in 2024?",
                description="Resolves YES if USGS reports a 6.0+ magnitude earthquake in Turkey.",
                category="WORLD",
                probability=0.35,
                volume=125000.0,
                liquidity=45000.0,
                source_url="https://polymarket.com/event/turkey-earthquake-2024",
                tags=["earthquake", "turkey", "disaster"],
            )
        ],
        "confidence": 85,
    },
    "philippines_typhoon": {
        "name": "Philippines Typhoon Zone",
        "lat_range": (5.0, 20.0),
        "long_range": (117.0, 127.0),
        "markets": [
            MarketData(
                market_id="poly_typhoon_ph_2024",
                question="Will a Category 5 typhoon hit Philippines in 2024?",
                description="Resolves YES if JTWC classifies a typhoon as Category 5.",
                category="WORLD",
                probability=0.72,
                volume=89000.0,
                liquidity=32000.0,
                source_url="https://polymarket.com/event/philippines-typhoon-2024",
                tags=["typhoon", "philippines", "disaster"],
            )
        ],
        "confidence": 78,
    },
    "ukraine_conflict": {
        "name": "Ukraine Conflict Zone",
        "lat_range": (44.0, 52.0),
        "long_range": (22.0, 40.0),
        "markets": [
            MarketData(
                market_id="poly_ukraine_ceasefire",
                question="Will there be a ceasefire in Ukraine by end of 2024?",
                description="Resolves YES if official ceasefire is declared by both parties.",
                category="WORLD",
                probability=0.15,
                volume=450000.0,
                liquidity=180000.0,
                source_url="https://polymarket.com/event/ukraine-ceasefire-2024",
                tags=["war", "ukraine", "ceasefire", "conflict"],
            ),
            MarketData(
                market_id="poly_ukraine_aid",
                question="Will US approve additional Ukraine aid package in 2024?",
                description="Resolves YES if Congress passes a Ukraine aid bill.",
                category="POLITICS",
                probability=0.65,
                volume=320000.0,
                liquidity=95000.0,
                source_url="https://polymarket.com/event/ukraine-aid-2024",
                tags=["ukraine", "humanitarian", "aid"],
            ),
        ],
        "confidence": 92,
    },
    "gaza_humanitarian": {
        "name": "Gaza Humanitarian Zone",
        "lat_range": (31.0, 32.0),
        "long_range": (34.0, 35.0),
        "markets": [
            MarketData(
                market_id="poly_gaza_aid",
                question="Will humanitarian aid reach Gaza in significant amounts by Q2 2024?",
                description="Resolves YES if UN reports over 500 aid trucks entering Gaza.",
                category="WORLD",
                probability=0.45,
                volume=320000.0,
                liquidity=120000.0,
                source_url="https://polymarket.com/event/gaza-humanitarian-aid",
                tags=["humanitarian", "gaza", "aid", "crisis"],
            ),
            MarketData(
                market_id="poly_gaza_ceasefire",
                question="Will there be a lasting ceasefire in Gaza by mid-2024?",
                description="Resolves YES if ceasefire lasts at least 7 consecutive days.",
                category="WORLD",
                probability=0.28,
                volume=580000.0,
                liquidity=210000.0,
                source_url="https://polymarket.com/event/gaza-ceasefire-2024",
                tags=["ceasefire", "gaza", "conflict"],
            ),
        ],
        "confidence": 88,
    },
    "japan_earthquake": {
        "name": "Japan Earthquake Zone",
        "lat_range": (30.0, 46.0),
        "long_range": (129.0, 146.0),
        "markets": [
            MarketData(
                market_id="poly_japan_eq_2024",
                question="Will a major earthquake (>7.0) hit Japan in 2024?",
                description="Resolves YES if JMA reports a 7.0+ earthquake in Japan.",
                category="WORLD",
                probability=0.42,
                volume=95000.0,
                liquidity=38000.0,
                source_url="https://polymarket.com/event/japan-earthquake-2024",
                tags=["earthquake", "japan", "disaster"],
            )
        ],
        "confidence": 80,
    },
}

# 用於關鍵字搜尋的所有市場
MOCK_ALL_MARKETS = []
for region_data in MOCK_CRISIS_REGIONS.values():
    MOCK_ALL_MARKETS.extend(region_data["markets"])

# 危機相關關鍵字
CRISIS_KEYWORDS = [
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
    "aid",
]


class MockPolymarketService(PolymarketService):
    """
    Mock Polymarket 服務

    用於開發和測試，不需要實際 API 連接
    """

    @property
    def service_name(self) -> str:
        return "mock"

    async def search_markets(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> list[MarketData]:
        """搜尋市場（Mock 實作）"""
        query_lower = query.lower()
        results = []

        for market in MOCK_ALL_MARKETS:
            # 檢查關鍵字匹配
            text = f"{market.question} {market.description}".lower()
            tags_text = " ".join(market.tags).lower()

            if query_lower in text or query_lower in tags_text:
                # 檢查類別過濾
                if category and market.category.upper() != category.upper():
                    continue
                results.append(market)

                if len(results) >= limit:
                    break

        return results

    async def get_market(self, market_id: str) -> Optional[MarketData]:
        """獲取特定市場（Mock 實作）"""
        for market in MOCK_ALL_MARKETS:
            if market.market_id == market_id:
                return market
        return None

    async def search_crisis_by_location(
        self,
        lat: float,
        long: float,
        radius_km: float = 500.0,
    ) -> CrisisSearchResult:
        """根據地理位置搜尋危機（Mock 實作）"""
        # 驗證座標
        if not -90 <= lat <= 90:
            return CrisisSearchResult(
                found=False,
                status="SUSPICIOUS",
                confidence=0,
            )
        if not -180 <= long <= 180:
            return CrisisSearchResult(
                found=False,
                status="SUSPICIOUS",
                confidence=0,
            )

        # 查找匹配的區域
        for region_key, region_data in MOCK_CRISIS_REGIONS.items():
            lat_range = region_data["lat_range"]
            long_range = region_data["long_range"]

            if lat_range[0] <= lat <= lat_range[1] and long_range[0] <= long <= long_range[1]:
                return CrisisSearchResult(
                    found=True,
                    markets=region_data["markets"],
                    region_name=region_data["name"],
                    confidence=region_data["confidence"],
                    status="VERIFIED",
                )

        # 未找到匹配區域
        return CrisisSearchResult(
            found=False,
            markets=[],
            region_name=None,
            confidence=30,
            status="SUSPICIOUS",
        )

    async def get_crisis_keywords(self) -> list[str]:
        """獲取危機關鍵字列表"""
        return CRISIS_KEYWORDS.copy()
