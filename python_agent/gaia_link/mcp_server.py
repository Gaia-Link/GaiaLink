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
- get_donation_history: 獲取用戶捐款歷史
- get_transaction_status: 查詢單筆交易狀態
"""

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Optional

from gaia_link.config import (
    get_polymarket_service,
    get_sentiment_service,
    get_blockchain_service,
)
from gaia_link.services.donation_history import get_donation_history_service

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


# =============================================================================
# Donation History Tools
# =============================================================================

# 有效的時間範圍
VALID_TIME_RANGES = {"7d", "30d", "90d", "365d", "all"}

# Sepolia Etherscan URL
ETHERSCAN_BASE_URL = "https://sepolia.etherscan.io/tx"


def _mask_wallet_address(address: str) -> str:
    """
    部分遮蔽錢包地址

    Args:
        address: 錢包地址

    Returns:
        遮蔽後的地址 (例如: 0x1234...5678)
    """
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"


@mcp.tool()
async def get_donation_history(
    wallet_address: str,
    time_range: str = "30d",
    limit: int = 50,
    ctx: Context = None
) -> dict:
    """
    獲取用戶捐款歷史

    查詢指定錢包的捐款記錄，支援時間範圍過濾和數量限制。

    Args:
        wallet_address: 用戶錢包地址
        time_range: 時間範圍 (7d, 30d, 90d, 365d, all)，預設 30d
        limit: 返回最大筆數，預設 50
        ctx: MCP 上下文

    Returns:
        包含捐款列表和統計數據的字典
    """
    # 驗證 time_range
    if time_range not in VALID_TIME_RANGES:
        return {
            "success": False,
            "error": f"無效的時間範圍: {time_range}。有效值: {', '.join(VALID_TIME_RANGES)}",
            "wallet_address": _mask_wallet_address(wallet_address),
            "time_range": time_range,
        }

    service = get_donation_history_service()
    result = await service.get_history(
        wallet_address=wallet_address,
        time_range=time_range,
        limit=limit,
    )

    # 轉換捐款記錄為字典格式
    donations = [d.to_dict() for d in result.donations]

    return {
        "success": True,
        "wallet_address": _mask_wallet_address(wallet_address),
        "donations": donations,
        "total_amount_usd": result.total_amount_usd,
        "total_count": result.total_count,
        "time_range": result.time_range,
    }


@mcp.tool()
async def get_transaction_status(
    tx_hash: str,
    ctx: Context = None
) -> dict:
    """
    查詢單筆交易狀態

    根據交易哈希查詢捐款交易的詳細資訊。

    Args:
        tx_hash: 交易哈希
        ctx: MCP 上下文

    Returns:
        包含交易詳情和區塊鏈瀏覽器連結的字典
    """
    service = get_donation_history_service()
    record = await service.get_transaction(tx_hash)

    if record is None:
        return {
            "success": False,
            "found": False,
            "tx_hash": tx_hash,
            "error": "找不到此交易記錄",
        }

    return {
        "success": True,
        "found": True,
        "tx_hash": record.tx_hash,
        "amount": record.amount,
        "token": record.token,
        "recipient": record.recipient,
        "recipient_address": _mask_wallet_address(record.recipient_address),
        "timestamp": record.timestamp.isoformat(),
        "status": record.status.value,
        "vault_type": record.vault_type.value,
        "explorer_url": f"{ETHERSCAN_BASE_URL}/{record.tx_hash}",
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
