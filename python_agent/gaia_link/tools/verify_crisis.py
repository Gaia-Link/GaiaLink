"""
verify_crisis 工具 - 驗證危機真實性

基於 SpoonOS BaseTool 實現，查詢 Polymarket 數據進行危機驗證
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

# 模擬的 Polymarket 危機數據（Hackathon Demo 用）
MOCK_CRISIS_DATA = {
    # 土耳其-敘利亞地震區域
    "turkey_earthquake": {
        "lat_range": (36.0, 39.0),
        "long_range": (35.0, 42.0),
        "events": [
            {
                "event_id": "poly_eq_turkey_2023",
                "title": "Will there be another major earthquake (>6.0) in Turkey in 2024?",
                "probability": 0.35,
                "volume": 125000.0,
                "source_url": "https://polymarket.com/event/turkey-earthquake-2024"
            }
        ],
        "status": "VERIFIED",
        "confidence": 85
    },
    # 菲律賓颱風區域
    "philippines_typhoon": {
        "lat_range": (5.0, 20.0),
        "long_range": (117.0, 127.0),
        "events": [
            {
                "event_id": "poly_typhoon_ph_2024",
                "title": "Will a Category 5 typhoon hit Philippines in 2024?",
                "probability": 0.72,
                "volume": 89000.0,
                "source_url": "https://polymarket.com/event/philippines-typhoon-2024"
            }
        ],
        "status": "VERIFIED",
        "confidence": 78
    },
    # 烏克蘭衝突區域
    "ukraine_conflict": {
        "lat_range": (44.0, 52.0),
        "long_range": (22.0, 40.0),
        "events": [
            {
                "event_id": "poly_ukraine_ceasefire",
                "title": "Will there be a ceasefire in Ukraine by end of 2024?",
                "probability": 0.15,
                "volume": 450000.0,
                "source_url": "https://polymarket.com/event/ukraine-ceasefire-2024"
            }
        ],
        "status": "VERIFIED",
        "confidence": 92
    },
    # 加薩人道危機
    "gaza_humanitarian": {
        "lat_range": (31.0, 32.0),
        "long_range": (34.0, 35.0),
        "events": [
            {
                "event_id": "poly_gaza_aid",
                "title": "Will humanitarian aid reach Gaza in significant amounts by Q2 2024?",
                "probability": 0.45,
                "volume": 320000.0,
                "source_url": "https://polymarket.com/event/gaza-humanitarian-aid"
            }
        ],
        "status": "VERIFIED",
        "confidence": 88
    }
}


class VerifyCrisisTool(BaseTool):
    """
    驗證危機求助貼文的真實性

    透過查詢 Polymarket 預測市場數據，比對地理位置附近的災難事件，
    判斷求助貼文的可信度。
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
                "description": "Latitude of the crisis location (-90 to 90)"
            },
            "long": {
                "type": "number",
                "description": "Longitude of the crisis location (-180 to 180)"
            }
        },
        "required": ["lat", "long"]
    }

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

        # 查找匹配的危機區域
        matched_crisis = self._find_matching_crisis(lat, long)

        if matched_crisis:
            return self._build_verified_response(matched_crisis, lat, long)
        else:
            return self._build_suspicious_response(lat, long)

    def _find_matching_crisis(self, lat: float, long: float) -> Optional[dict]:
        """查找匹配的危機區域"""
        for crisis_data in MOCK_CRISIS_DATA.values():
            lat_range = crisis_data["lat_range"]
            long_range = crisis_data["long_range"]

            if (lat_range[0] <= lat <= lat_range[1] and
                long_range[0] <= long <= long_range[1]):
                return crisis_data

        return None

    def _build_verified_response(self, crisis_data: dict, lat: float, long: float) -> dict:
        """建立已驗證的回應"""
        return {
            "status": crisis_data["status"],
            "confidence": crisis_data["confidence"],
            "polymarket_events": crisis_data["events"],
            "risk_factors": [],
            "recommendation": (
                f"此位置 ({lat:.2f}, {long:.2f}) 已在 Polymarket 預測市場中找到相關危機事件。"
                f"可信度評分: {crisis_data['confidence']}%。建議可以考慮提供援助。"
            )
        }

    def _build_suspicious_response(self, lat: float, long: float) -> dict:
        """建立可疑的回應"""
        risk_factors = [
            "無法在 Polymarket 預測市場中找到相關危機事件",
            "建議進一步查證當地新聞來源",
            "建議聯繫當地 NGO 或官方機構確認"
        ]

        return {
            "status": "SUSPICIOUS",
            "confidence": 30,
            "polymarket_events": [],
            "risk_factors": risk_factors,
            "recommendation": (
                f"此位置 ({lat:.2f}, {long:.2f}) 未在已知危機區域中。"
                f"無法透過 Polymarket 數據驗證。建議進一步查證後再提供援助。"
            )
        }
