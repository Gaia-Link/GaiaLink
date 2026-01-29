"""
RealPolymarketService - Polymarket 真實 API 實作

使用 Polymarket Gamma API 獲取市場數據
"""

import logging
from typing import Optional

import aiohttp

from gaia_link.services.polymarket.base import (
    PolymarketService,
    MarketData,
    CrisisSearchResult,
)


logger = logging.getLogger(__name__)

# Polymarket API 配置
POLYMARKET_API_BASE = "https://gamma-api.polymarket.com"
DEFAULT_TIMEOUT = 30
DEFAULT_LIMIT = 100

# 危機相關搜尋關鍵字
CRISIS_SEARCH_KEYWORDS = [
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
]

# 地理區域到搜尋關鍵字的映射
GEO_KEYWORD_MAP = {
    # 東亞
    "japan": {"lat_range": (30.0, 46.0), "long_range": (129.0, 146.0)},
    "china": {"lat_range": (18.0, 54.0), "long_range": (73.0, 135.0)},
    "taiwan": {"lat_range": (21.0, 26.0), "long_range": (119.0, 122.0)},
    "korea": {"lat_range": (33.0, 43.0), "long_range": (124.0, 132.0)},
    # 東南亞
    "philippines": {"lat_range": (5.0, 20.0), "long_range": (117.0, 127.0)},
    "indonesia": {"lat_range": (-11.0, 6.0), "long_range": (95.0, 141.0)},
    "vietnam": {"lat_range": (8.0, 24.0), "long_range": (102.0, 110.0)},
    "thailand": {"lat_range": (5.0, 21.0), "long_range": (97.0, 106.0)},
    # 中東
    "turkey": {"lat_range": (36.0, 42.0), "long_range": (26.0, 45.0)},
    "syria": {"lat_range": (32.0, 37.0), "long_range": (35.0, 42.0)},
    "israel": {"lat_range": (29.0, 33.0), "long_range": (34.0, 36.0)},
    "gaza": {"lat_range": (31.0, 32.0), "long_range": (34.0, 35.0)},
    "palestine": {"lat_range": (31.0, 33.0), "long_range": (34.0, 36.0)},
    "iran": {"lat_range": (25.0, 40.0), "long_range": (44.0, 63.0)},
    "iraq": {"lat_range": (29.0, 38.0), "long_range": (38.0, 49.0)},
    "lebanon": {"lat_range": (33.0, 35.0), "long_range": (35.0, 37.0)},
    # 歐洲
    "ukraine": {"lat_range": (44.0, 52.0), "long_range": (22.0, 40.0)},
    "russia": {"lat_range": (41.0, 82.0), "long_range": (19.0, 180.0)},
    # 非洲
    "sudan": {"lat_range": (8.0, 23.0), "long_range": (21.0, 39.0)},
    "ethiopia": {"lat_range": (3.0, 15.0), "long_range": (33.0, 48.0)},
    "somalia": {"lat_range": (-2.0, 12.0), "long_range": (41.0, 51.0)},
    # 美洲
    "haiti": {"lat_range": (18.0, 20.0), "long_range": (-75.0, -71.0)},
    "mexico": {"lat_range": (14.0, 33.0), "long_range": (-118.0, -86.0)},
    # 南亞
    "pakistan": {"lat_range": (23.0, 37.0), "long_range": (60.0, 77.0)},
    "afghanistan": {"lat_range": (29.0, 39.0), "long_range": (60.0, 75.0)},
    "bangladesh": {"lat_range": (20.0, 27.0), "long_range": (88.0, 93.0)},
    "india": {"lat_range": (6.0, 36.0), "long_range": (68.0, 98.0)},
}


class RealPolymarketService(PolymarketService):
    """
    真實 Polymarket API 服務

    使用 aiohttp 連接 Polymarket Gamma API
    """

    def __init__(
        self,
        api_base: str = POLYMARKET_API_BASE,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        初始化服務

        Args:
            api_base: API 基礎 URL
            timeout: 請求超時時間（秒）
        """
        self._api_base = api_base
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def service_name(self) -> str:
        return "real"

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建 HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """關閉 HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> Optional[dict | list]:
        """
        發送 API 請求

        Args:
            endpoint: API 端點
            params: 查詢參數

        Returns:
            API 響應數據
        """
        session = await self._get_session()
        url = f"{self._api_base}{endpoint}"

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning("Polymarket API rate limit reached")
                    return None
                else:
                    logger.error(f"Polymarket API error: {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Polymarket API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Polymarket request: {e}")
            return None

    def _parse_market(self, data: dict) -> MarketData:
        """將 API 響應轉換為 MarketData"""
        # 計算 Yes 的機率
        probability = 0.0
        outcomes = data.get("outcomes", [])
        for outcome in outcomes:
            if outcome.get("name", "").lower() == "yes":
                probability = float(outcome.get("price", 0.0))
                break

        # 如果沒有 outcomes，嘗試其他欄位
        if probability == 0.0:
            probability = float(data.get("outcomePrices", [0.0])[0] if data.get("outcomePrices") else 0.0)

        return MarketData(
            market_id=data.get("id", data.get("condition_id", "")),
            question=data.get("question", data.get("title", "")),
            description=data.get("description", ""),
            category=data.get("category", ""),
            probability=probability,
            volume=float(data.get("volume", 0.0)),
            liquidity=float(data.get("liquidity", 0.0)),
            source_url=f"https://polymarket.com/event/{data.get('slug', data.get('id', ''))}",
            closes_at=data.get("closesAt", data.get("end_date_iso")),
            resolved=data.get("resolved", False),
            outcome=data.get("outcome"),
            tags=data.get("tags", []),
        )

    async def search_markets(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
    ) -> list[MarketData]:
        """搜尋市場"""
        params = {
            "limit": min(limit, DEFAULT_LIMIT),
        }

        # 添加搜尋關鍵字
        if query:
            params["_q"] = query

        # 添加類別過濾
        if category:
            params["tag"] = category.lower()

        data = await self._make_request("/markets", params)

        if not data:
            return []

        # API 返回的可能是列表或帶有 data 欄位的對象
        markets_data = data if isinstance(data, list) else data.get("data", data.get("markets", []))

        results = []
        for item in markets_data:
            try:
                market = self._parse_market(item)
                results.append(market)
            except Exception as e:
                logger.warning(f"Failed to parse market data: {e}")
                continue

        return results[:limit]

    async def get_market(self, market_id: str) -> Optional[MarketData]:
        """獲取特定市場"""
        data = await self._make_request(f"/markets/{market_id}")

        if not data:
            return None

        try:
            return self._parse_market(data)
        except Exception as e:
            logger.error(f"Failed to parse market {market_id}: {e}")
            return None

    async def search_crisis_by_location(
        self,
        lat: float,
        long: float,
        radius_km: float = 500.0,
    ) -> CrisisSearchResult:
        """根據地理位置搜尋危機相關市場"""
        # 驗證座標
        if not -90 <= lat <= 90 or not -180 <= long <= 180:
            return CrisisSearchResult(
                found=False,
                status="SUSPICIOUS",
                confidence=0,
            )

        # 根據座標找到可能的地區關鍵字
        region_keywords = self._find_region_keywords(lat, long)

        if not region_keywords:
            # 無法確定地區，使用通用危機關鍵字搜尋
            return CrisisSearchResult(
                found=False,
                markets=[],
                region_name=None,
                confidence=30,
                status="SUSPICIOUS",
            )

        # 搜尋相關市場
        all_markets = []
        region_name = region_keywords[0].title()

        for keyword in region_keywords:
            # 搜尋包含地區名稱和危機關鍵字的市場
            for crisis_keyword in CRISIS_SEARCH_KEYWORDS[:5]:  # 限制搜尋次數
                query = f"{keyword} {crisis_keyword}"
                markets = await self.search_markets(query, limit=5)

                for market in markets:
                    if self.is_crisis_related(market) and market not in all_markets:
                        all_markets.append(market)

        if all_markets:
            # 根據找到的市場數量和交易量計算信心分數
            total_volume = sum(m.volume for m in all_markets)
            confidence = min(90, 50 + len(all_markets) * 5 + int(total_volume / 100000))

            return CrisisSearchResult(
                found=True,
                markets=all_markets[:10],  # 限制返回數量
                region_name=region_name,
                confidence=confidence,
                status="VERIFIED",
            )

        return CrisisSearchResult(
            found=False,
            markets=[],
            region_name=region_name,
            confidence=40,
            status="SUSPICIOUS",
        )

    def _find_region_keywords(self, lat: float, long: float) -> list[str]:
        """根據座標找到可能的地區關鍵字"""
        keywords = []

        for region, bounds in GEO_KEYWORD_MAP.items():
            lat_range = bounds["lat_range"]
            long_range = bounds["long_range"]

            if lat_range[0] <= lat <= lat_range[1] and long_range[0] <= long <= long_range[1]:
                keywords.append(region)

        return keywords

    async def get_crisis_keywords(self) -> list[str]:
        """獲取危機關鍵字列表"""
        return CRISIS_SEARCH_KEYWORDS.copy()
