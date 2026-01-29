"""
verify_crisis 工具 - 驗證危機真實性

基於 SpoonOS BaseTool 實現，查詢 Polymarket 數據進行危機驗證
支援 Mock 和 Real Polymarket API 切換
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.services.polymarket import PolymarketService


class VerifyCrisisTool(BaseTool):
    """
    驗證危機求助貼文的真實性

    透過查詢 Polymarket 預測市場數據，比對地理位置附近的災難事件，
    判斷求助貼文的可信度。

    支援依賴注入 PolymarketService，可在測試時使用 Mock 服務。
    """

    name: str = "verify_crisis"
    description: str = (
        "Verify the authenticity of a crisis help post by cross-referencing "
        "with Polymarket prediction market data and news sources. "
        "Returns verification status (VERIFIED/SUSPICIOUS/SCAM), confidence score, "
        "and related prediction market events."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "lat": {
                "type": "number",
                "description": "Latitude of the crisis location (-90 to 90)",
            },
            "long": {
                "type": "number",
                "description": "Longitude of the crisis location (-180 to 180)",
            },
        },
        "required": ["lat", "long"],
    }

    # 私有屬性：Polymarket 服務（可注入）
    _polymarket_service: Optional[PolymarketService] = None

    def __init__(
        self,
        polymarket_service: Optional[PolymarketService] = None,
        **data,
    ):
        """
        初始化工具

        Args:
            polymarket_service: 可選的 Polymarket 服務實例（依賴注入）
            **data: 其他 Pydantic 欄位
        """
        super().__init__(**data)
        self._polymarket_service = polymarket_service

    def _get_service(self) -> PolymarketService:
        """獲取 Polymarket 服務實例"""
        if self._polymarket_service is not None:
            return self._polymarket_service

        # 從配置獲取默認服務
        from gaia_link.config import get_polymarket_service

        return get_polymarket_service()

    async def execute(self, lat: float, long: float) -> dict:
        """
        執行危機驗證

        Args:
            lat: 緯度 (-90 到 90)
            long: 經度 (-180 到 180)

        Returns:
            驗證結果字典，包含 status, confidence, polymarket_events, risk_factors, recommendation
        """
        # 驗證輸入範圍
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not -180 <= long <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {long}")

        # 獲取服務並搜尋危機
        service = self._get_service()
        result = await service.search_crisis_by_location(lat=lat, long=long)

        if result.found:
            return self._build_verified_response(result, lat, long)
        else:
            return self._build_suspicious_response(result, lat, long)

    def _build_verified_response(self, result, lat: float, long: float) -> dict:
        """建立已驗證的回應"""
        polymarket_events = [m.to_dict() for m in result.markets]
        region_info = f" ({result.region_name})" if result.region_name else ""

        return {
            "status": result.status,
            "confidence": result.confidence,
            "polymarket_events": polymarket_events,
            "risk_factors": [],
            "recommendation": (
                f"此位置 ({lat:.2f}, {long:.2f}){region_info} "
                f"已在 Polymarket 預測市場中找到相關危機事件。"
                f"可信度評分: {result.confidence}%。建議可以考慮提供援助。"
            ),
        }

    def _build_suspicious_response(self, result, lat: float, long: float) -> dict:
        """建立可疑的回應"""
        risk_factors = [
            "無法在 Polymarket 預測市場中找到相關危機事件",
            "建議進一步查證當地新聞來源",
            "建議聯繫當地 NGO 或官方機構確認",
        ]

        region_info = f" ({result.region_name})" if result.region_name else ""

        return {
            "status": result.status,
            "confidence": result.confidence,
            "polymarket_events": [],
            "risk_factors": risk_factors,
            "recommendation": (
                f"此位置 ({lat:.2f}, {long:.2f}){region_info} 未在已知危機區域中。"
                f"無法透過 Polymarket 數據驗證。建議進一步查證後再提供援助。"
            ),
        }
