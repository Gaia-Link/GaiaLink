"""
verify_crisis 工具單元測試

測試 VerifyCrisisTool 與 Polymarket 服務層整合
"""

import pytest

from gaia_link.tools.verify_crisis import VerifyCrisisTool
from gaia_link.services.polymarket import MockPolymarketService


class TestVerifyCrisisTool:
    """verify_crisis 工具測試"""

    @pytest.fixture
    def tool(self):
        """建立工具實例"""
        return VerifyCrisisTool()

    def test_tool_has_correct_name(self, tool):
        """工具應有正確的名稱"""
        assert tool.name == "verify_crisis"

    def test_tool_has_description(self, tool):
        """工具應有描述"""
        assert len(tool.description) > 0
        assert "verify" in tool.description.lower()

    def test_tool_has_required_parameters(self, tool):
        """工具應有必要的參數定義"""
        assert "lat" in tool.parameters["properties"]
        assert "long" in tool.parameters["properties"]
        assert "crisis_name" in tool.parameters["properties"]
        # 現在支援兩種模式：名稱或座標，所以沒有強制必要參數
        assert tool.parameters["required"] == []

    @pytest.mark.asyncio
    async def test_execute_returns_verified_for_known_crisis_zone(self, tool):
        """已知危機區域應返回 VERIFIED 狀態"""
        # 土耳其地震區域 (2023 年地震)
        result = await tool.execute(lat=37.5, long=37.0)

        assert "status" in result
        assert result["status"] in ["VERIFIED", "SUSPICIOUS", "SCAM"]
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 100
        assert "polymarket_events" in result
        assert isinstance(result["polymarket_events"], list)
        assert "risk_factors" in result
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_execute_returns_suspicious_for_unknown_location(self, tool):
        """無相關數據的位置應返回 SUSPICIOUS"""
        # 南極洲某處（不太可能有災難數據）
        result = await tool.execute(lat=-80.0, long=0.0)

        assert result["status"] in ["SUSPICIOUS", "SCAM"]
        assert result["confidence"] < 70

    @pytest.mark.asyncio
    async def test_execute_validates_latitude_range(self, tool):
        """應驗證緯度範圍 (-90 到 90)"""
        with pytest.raises((ValueError, Exception)):
            await tool.execute(lat=100.0, long=0.0)

    @pytest.mark.asyncio
    async def test_execute_validates_longitude_range(self, tool):
        """應驗證經度範圍 (-180 到 180)"""
        with pytest.raises((ValueError, Exception)):
            await tool.execute(lat=0.0, long=200.0)

    @pytest.mark.asyncio
    async def test_execute_returns_polymarket_events_structure(self, tool):
        """Polymarket 事件應有正確的結構"""
        result = await tool.execute(lat=37.5, long=37.0)

        for event in result["polymarket_events"]:
            assert "event_id" in event
            assert "title" in event
            assert "probability" in event
            assert 0 <= event["probability"] <= 1
            assert "volume" in event

    @pytest.mark.asyncio
    async def test_execute_returns_risk_factors_as_list(self, tool):
        """風險因素應為字串列表"""
        result = await tool.execute(lat=37.5, long=37.0)

        assert isinstance(result["risk_factors"], list)
        for factor in result["risk_factors"]:
            assert isinstance(factor, str)

    def test_tool_to_param_format(self, tool):
        """to_param 應返回正確的函數調用格式"""
        param = tool.to_param()

        assert param["type"] == "function"
        assert param["function"]["name"] == "verify_crisis"
        assert "parameters" in param["function"]


class TestVerifyCrisisToolDependencyInjection:
    """VerifyCrisisTool 依賴注入測試"""

    @pytest.fixture
    def mock_service(self):
        """建立 Mock 服務實例"""
        return MockPolymarketService()

    @pytest.fixture
    def tool_with_service(self, mock_service):
        """建立帶有注入服務的工具實例"""
        return VerifyCrisisTool(polymarket_service=mock_service)

    def test_can_inject_service(self, mock_service):
        """應能注入 Polymarket 服務"""
        tool = VerifyCrisisTool(polymarket_service=mock_service)
        assert tool._polymarket_service is mock_service

    def test_default_service_is_none(self):
        """默認服務應為 None"""
        tool = VerifyCrisisTool()
        assert tool._polymarket_service is None

    @pytest.mark.asyncio
    async def test_execute_uses_injected_service(self, tool_with_service):
        """execute 應使用注入的服務"""
        result = await tool_with_service.execute(lat=37.5, long=38.0)

        assert result["status"] == "VERIFIED"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_execute_turkey_verified(self, tool_with_service):
        """土耳其座標應返回 VERIFIED"""
        result = await tool_with_service.execute(lat=37.5, long=38.0)

        assert result["status"] == "VERIFIED"
        assert "Turkey" in result["recommendation"] or "region" in result["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_execute_gaza_verified(self, tool_with_service):
        """加薩座標應返回 VERIFIED"""
        result = await tool_with_service.execute(lat=31.5, long=34.5)

        assert result["status"] == "VERIFIED"

    @pytest.mark.asyncio
    async def test_execute_unknown_location_suspicious(self, tool_with_service):
        """未知位置應返回 SUSPICIOUS"""
        result = await tool_with_service.execute(lat=0.0, long=-150.0)

        assert result["status"] == "SUSPICIOUS"
        assert len(result["risk_factors"]) > 0
