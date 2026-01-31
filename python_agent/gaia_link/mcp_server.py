#!/usr/bin/env python3
"""
Gaia Link MCP Server - 將 Gaia Link 功能暴露為 MCP 服務

運行方式:
  python -m gaia_link.mcp_server        # stdio 模式
  python -m gaia_link.mcp_server --sse  # SSE 模式

此 MCP Server 允許其他 SpoonOS Agent 調用 Gaia Link 的核心功能：
- verify_crisis: 驗證危機真實性
- analyze_crisis_sentiment: 分析危機相關文本情感
- estimate_donation: 估算捐款成本
"""

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Optional

from gaia_link.config import (
    get_polymarket_service,
    get_sentiment_service,
    get_blockchain_service,
)

# 創建 FastMCP 實例
mcp = FastMCP(
    name="gaia-link",
    instructions="人道救援危機驗證與捐款協調 MCP 服務"
)


class CrisisLocation(BaseModel):
    """危機位置模型"""
    lat: float = Field(ge=-90, le=90, description="緯度 (-90 到 90)")
    long: float = Field(ge=-180, le=180, description="經度 (-180 到 180)")


@mcp.tool()
async def verify_crisis(location: CrisisLocation, ctx: Context) -> dict:
    """
    驗證危機真實性

    根據提供的座標查詢 Polymarket 預測市場數據，
    判斷該位置的危機是否為真實事件。

    Args:
        location: 危機位置 (lat, long)
        ctx: MCP 上下文

    Returns:
        包含驗證狀態、信心度和相關事件的字典
    """
    service = get_polymarket_service()
    result = await service.search_crisis_by_location(
        lat=location.lat,
        long=location.long
    )

    return {
        "status": result.status,
        "confidence": result.confidence,
        "polymarket_events": [m.to_dict() for m in result.markets] if result.markets else [],
        "risk_factors": result.risk_factors if hasattr(result, 'risk_factors') else [],
    }


@mcp.tool()
async def analyze_crisis_sentiment(text: str, ctx: Context) -> dict:
    """
    分析危機相關文本的情感

    分析求助貼文或危機描述的緊急程度和真實性。

    Args:
        text: 要分析的文本
        ctx: MCP 上下文

    Returns:
        包含緊急程度、真實性分數和情緒指標的字典
    """
    service = get_sentiment_service()
    result = await service.analyze(text=text)
    return result.to_dict()


@mcp.tool()
async def estimate_donation(
    amount: float,
    token: str,
    recipient: str,
    ctx: Context
) -> dict:
    """
    估算捐款成本

    計算捐款的總成本，包括 gas 費用。

    Args:
        amount: 捐款金額
        token: 代幣類型 (USDC, USDT, ETH, DAI)
        recipient: 接收者地址
        ctx: MCP 上下文

    Returns:
        包含估算費用的字典
    """
    blockchain = get_blockchain_service()

    # 估算 gas 費用
    gas_fee_eth = await blockchain.estimate_gas(
        amount=amount,
        token=token,
        recipient_address=recipient
    )

    # 計算 USD 費用 (假設 ETH = $2500)
    eth_price_usd = 2500.0
    gas_fee_usd = gas_fee_eth * eth_price_usd

    # 計算總成本
    token_usd_rates = {"USDC": 1.0, "USDT": 1.0, "ETH": eth_price_usd, "DAI": 1.0}
    amount_usd = amount * token_usd_rates.get(token, 1.0)
    total_cost_usd = amount_usd + gas_fee_usd

    return {
        "success": True,
        "amount": amount,
        "token": token,
        "recipient": recipient,
        "gas_fee_eth": round(gas_fee_eth, 6),
        "gas_fee_usd": round(gas_fee_usd, 2),
        "total_cost_usd": round(total_cost_usd, 2),
    }


@mcp.resource("gaia://status")
def get_service_status() -> str:
    """
    獲取 Gaia Link 服務狀態

    Returns:
        服務狀態字符串
    """
    return "Gaia Link MCP Server: Online"


def main():
    """MCP Server 入口點"""
    import sys
    if "--sse" in sys.argv:
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
