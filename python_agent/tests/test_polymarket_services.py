"""
Polymarket 服務層單元測試

測試 PolymarketService、MockPolymarketService 和相關數據類
"""

import pytest

from gaia_link.services.polymarket.base import (
    PolymarketService,
    MarketData,
    CrisisSearchResult,
)
from gaia_link.services.polymarket.mock_polymarket import (
    MockPolymarketService,
    MOCK_CRISIS_REGIONS,
    CRISIS_KEYWORDS,
)


class TestMarketData:
    """MarketData 數據類測試"""

    def test_create_market_data(self):
        """應能創建 MarketData 實例"""
        market = MarketData(
            market_id="test_123",
            question="Will event X happen?",
            probability=0.65,
            volume=100000.0,
        )
        assert market.market_id == "test_123"
        assert market.question == "Will event X happen?"
        assert market.probability == 0.65
        assert market.volume == 100000.0

    def test_market_data_defaults(self):
        """應有正確的默認值"""
        market = MarketData(market_id="test", question="Test?")
        assert market.description == ""
        assert market.category == ""
        assert market.probability == 0.0
        assert market.volume == 0.0
        assert market.liquidity == 0.0
        assert market.source_url is None
        assert market.closes_at is None
        assert market.resolved is False
        assert market.outcome is None
        assert market.tags == []

    def test_to_dict(self):
        """to_dict 應返回正確的字典格式"""
        market = MarketData(
            market_id="poly_123",
            question="Test question?",
            probability=0.45,
            volume=50000.0,
            source_url="https://polymarket.com/test",
        )
        d = market.to_dict()
        assert d["event_id"] == "poly_123"
        assert d["title"] == "Test question?"
        assert d["probability"] == 0.45
        assert d["volume"] == 50000.0
        assert d["source_url"] == "https://polymarket.com/test"


class TestCrisisSearchResult:
    """CrisisSearchResult 數據類測試"""

    def test_found_result(self):
        """成功找到危機的結果"""
        market = MarketData(market_id="m1", question="Test?")
        result = CrisisSearchResult(
            found=True,
            markets=[market],
            region_name="Test Region",
            confidence=85,
            status="VERIFIED",
        )
        assert result.found is True
        assert len(result.markets) == 1
        assert result.region_name == "Test Region"
        assert result.confidence == 85
        assert result.status == "VERIFIED"

    def test_not_found_result(self):
        """未找到危機的結果"""
        result = CrisisSearchResult(
            found=False,
            status="SUSPICIOUS",
            confidence=30,
        )
        assert result.found is False
        assert result.markets == []
        assert result.region_name is None
        assert result.confidence == 30
        assert result.status == "SUSPICIOUS"

    def test_to_dict(self):
        """to_dict 應返回正確的字典格式"""
        market = MarketData(market_id="m1", question="Test?", probability=0.5)
        result = CrisisSearchResult(
            found=True,
            markets=[market],
            region_name="Region",
            confidence=80,
            status="VERIFIED",
        )
        d = result.to_dict()
        assert d["found"] is True
        assert len(d["markets"]) == 1
        assert d["region_name"] == "Region"
        assert d["confidence"] == 80
        assert d["status"] == "VERIFIED"


class TestMockPolymarketService:
    """MockPolymarketService 測試"""

    @pytest.fixture
    def service(self):
        """建立服務實例"""
        return MockPolymarketService()

    def test_service_name(self, service):
        """應返回 mock 服務名稱"""
        assert service.service_name == "mock"

    @pytest.mark.asyncio
    async def test_search_markets_by_keyword(self, service):
        """應能按關鍵字搜尋市場"""
        results = await service.search_markets("earthquake", limit=5)
        assert len(results) > 0
        for market in results:
            assert isinstance(market, MarketData)

    @pytest.mark.asyncio
    async def test_search_markets_no_results(self, service):
        """搜尋無結果應返回空列表"""
        results = await service.search_markets("nonexistent_keyword_xyz", limit=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_markets_limit(self, service):
        """應遵守 limit 參數"""
        results = await service.search_markets("", limit=2)
        # 可能返回更少，但不應超過 limit
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_get_market_existing(self, service):
        """應能獲取存在的市場"""
        market = await service.get_market("poly_eq_turkey_2023")
        assert market is not None
        assert market.market_id == "poly_eq_turkey_2023"

    @pytest.mark.asyncio
    async def test_get_market_not_found(self, service):
        """不存在的市場應返回 None"""
        market = await service.get_market("nonexistent_id")
        assert market is None

    @pytest.mark.asyncio
    async def test_search_crisis_turkey(self, service):
        """土耳其座標應找到危機"""
        result = await service.search_crisis_by_location(lat=37.5, long=38.0)
        assert result.found is True
        assert result.status == "VERIFIED"
        assert result.confidence > 0
        assert len(result.markets) > 0

    @pytest.mark.asyncio
    async def test_search_crisis_philippines(self, service):
        """菲律賓座標應找到危機"""
        result = await service.search_crisis_by_location(lat=14.5, long=121.0)
        assert result.found is True
        assert result.status == "VERIFIED"

    @pytest.mark.asyncio
    async def test_search_crisis_ukraine(self, service):
        """烏克蘭座標應找到危機"""
        result = await service.search_crisis_by_location(lat=50.0, long=30.0)
        assert result.found is True
        assert result.status == "VERIFIED"

    @pytest.mark.asyncio
    async def test_search_crisis_gaza(self, service):
        """加薩座標應找到危機"""
        result = await service.search_crisis_by_location(lat=31.5, long=34.5)
        assert result.found is True
        assert result.status == "VERIFIED"

    @pytest.mark.asyncio
    async def test_search_crisis_japan(self, service):
        """日本座標應找到危機"""
        result = await service.search_crisis_by_location(lat=35.0, long=139.0)
        assert result.found is True
        assert result.status == "VERIFIED"

    @pytest.mark.asyncio
    async def test_search_crisis_unknown_location(self, service):
        """未知位置應返回 SUSPICIOUS"""
        # 太平洋中央，無危機區域
        result = await service.search_crisis_by_location(lat=0.0, long=-150.0)
        assert result.found is False
        assert result.status == "SUSPICIOUS"
        assert result.confidence < 50

    @pytest.mark.asyncio
    async def test_search_crisis_invalid_coordinates(self, service):
        """無效座標應返回 SUSPICIOUS"""
        result = await service.search_crisis_by_location(lat=100.0, long=200.0)
        assert result.found is False
        assert result.confidence == 0

    @pytest.mark.asyncio
    async def test_get_crisis_keywords(self, service):
        """應返回危機關鍵字列表"""
        keywords = await service.get_crisis_keywords()
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "earthquake" in keywords
        assert "hurricane" in keywords

    def test_is_crisis_related_true(self, service):
        """危機相關市場應返回 True"""
        market = MarketData(
            market_id="test",
            question="Will there be an earthquake?",
        )
        assert service.is_crisis_related(market) is True

    def test_is_crisis_related_false(self, service):
        """非危機相關市場應返回 False"""
        market = MarketData(
            market_id="test",
            question="Will Bitcoin reach 100k?",
        )
        assert service.is_crisis_related(market) is False

    def test_is_crisis_related_by_tags(self, service):
        """通過標籤判斷危機相關"""
        market = MarketData(
            market_id="test",
            question="Some event?",
            tags=["disaster", "emergency"],
        )
        assert service.is_crisis_related(market) is True


class TestPolymarketServiceInterface:
    """PolymarketService 抽象介面測試"""

    def test_mock_service_implements_interface(self):
        """MockPolymarketService 應實現 PolymarketService 介面"""
        service = MockPolymarketService()
        assert isinstance(service, PolymarketService)

    def test_interface_has_required_methods(self):
        """PolymarketService 應定義必要的抽象方法"""
        abstract_methods = PolymarketService.__abstractmethods__
        assert "search_markets" in abstract_methods
        assert "get_market" in abstract_methods
        assert "search_crisis_by_location" in abstract_methods
        assert "get_crisis_keywords" in abstract_methods

    def test_interface_has_required_properties(self):
        """PolymarketService 應定義必要的屬性"""
        abstract_methods = PolymarketService.__abstractmethods__
        assert "service_name" in abstract_methods


class TestMockCrisisRegions:
    """Mock 危機區域數據測試"""

    def test_all_regions_have_required_fields(self):
        """所有區域應有必要欄位"""
        for region_key, region_data in MOCK_CRISIS_REGIONS.items():
            assert "name" in region_data
            assert "lat_range" in region_data
            assert "long_range" in region_data
            assert "markets" in region_data
            assert "confidence" in region_data
            assert len(region_data["markets"]) > 0

    def test_all_markets_have_required_fields(self):
        """所有市場應有必要欄位"""
        for region_data in MOCK_CRISIS_REGIONS.values():
            for market in region_data["markets"]:
                assert market.market_id
                assert market.question
                assert market.probability >= 0
                assert market.volume >= 0

    def test_confidence_in_valid_range(self):
        """信心分數應在有效範圍內"""
        for region_data in MOCK_CRISIS_REGIONS.values():
            assert 0 <= region_data["confidence"] <= 100
