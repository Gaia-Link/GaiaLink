#!/usr/bin/env python3
"""
查詢 Polymarket 預測市場數據

此腳本作為 crisis-response 技能的一部分，
用於查詢指定座標的危機相關預測市場數據。

輸入 (stdin JSON):
    {"lat": 37.5, "long": 37.0}

輸出 (stdout JSON):
    {"found": true, "status": "VERIFIED", "confidence": 85, ...}
"""

import sys
import json
import asyncio

try:
    from gaia_link.config import get_polymarket_service
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False


async def search_polymarket(lat: float, long: float) -> dict:
    """
    查詢 Polymarket 預測市場數據

    Args:
        lat: 緯度
        long: 經度

    Returns:
        包含驗證結果的字典
    """
    if HAS_SERVICE:
        service = get_polymarket_service()
        result = await service.search_crisis_by_location(lat=lat, long=long)
        return {
            "found": result.found,
            "status": result.status,
            "confidence": result.confidence,
            "region_name": result.region_name if hasattr(result, 'region_name') else None,
            "events": [m.to_dict() for m in result.markets] if result.markets else [],
        }
    else:
        # Mock 回應 (當服務不可用時)
        return {
            "found": True,
            "status": "VERIFIED",
            "confidence": 75,
            "region_name": "Demo Region",
            "events": [{"event_id": "demo_001", "title": "Demo Event"}],
        }


def main():
    """主入口點"""
    # 讀取 stdin 輸入
    input_data = sys.stdin.read().strip()
    if not input_data:
        print(json.dumps({"error": "No input provided"}))
        sys.exit(1)

    # 解析 JSON
    try:
        params = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    # 驗證參數
    lat = params.get("lat")
    long = params.get("long")

    if lat is None or long is None:
        print(json.dumps({"error": "Missing required parameters: lat, long"}))
        sys.exit(1)

    # 驗證座標範圍
    if not -90 <= lat <= 90:
        print(json.dumps({"error": f"Invalid latitude: {lat}. Must be between -90 and 90"}))
        sys.exit(1)

    if not -180 <= long <= 180:
        print(json.dumps({"error": f"Invalid longitude: {long}. Must be between -180 and 180"}))
        sys.exit(1)

    # 執行查詢
    result = asyncio.run(search_polymarket(lat, long))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
