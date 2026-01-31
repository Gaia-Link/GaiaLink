#!/usr/bin/env python3
"""
優化捐款路徑和 Gas 費用

此腳本作為 donation-advisor 技能的一部分，
用於計算最優的捐款路徑和預估費用。

輸入 (stdin JSON):
    {"amount": 100, "token": "USDC", "recipient": "0x..."}

輸出 (stdout JSON):
    {"optimal_route": {...}, "cost_breakdown": {...}, ...}
"""

import sys
import json
import asyncio

try:
    from gaia_link.config import get_blockchain_service
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False


# 代幣對 USD 的匯率
TOKEN_USD_RATES = {
    "USDC": 1.0,
    "USDT": 1.0,
    "ETH": 2500.0,
    "DAI": 1.0,
}

# 支援的代幣
SUPPORTED_TOKENS = list(TOKEN_USD_RATES.keys())


async def optimize_donation_route(amount: float, token: str, recipient: str) -> dict:
    """
    優化捐款路徑

    Args:
        amount: 捐款金額
        token: 代幣類型
        recipient: 接收者地址

    Returns:
        包含優化結果的字典
    """
    # 驗證代幣
    if token not in SUPPORTED_TOKENS:
        return {
            "success": False,
            "error": f"Unsupported token: {token}. Supported: {', '.join(SUPPORTED_TOKENS)}"
        }

    # 驗證金額
    if amount <= 0:
        return {
            "success": False,
            "error": "Amount must be positive"
        }

    # 估算 Gas 費用
    if HAS_SERVICE:
        service = get_blockchain_service()
        gas_fee_eth = await service.estimate_gas(
            amount=amount,
            token=token,
            recipient_address=recipient
        )
    else:
        # Mock Gas 費用
        gas_fee_eth = 0.003

    # 計算費用
    eth_price = TOKEN_USD_RATES["ETH"]
    gas_fee_usd = gas_fee_eth * eth_price
    amount_usd = amount * TOKEN_USD_RATES.get(token, 1.0)
    total_cost_usd = amount_usd + gas_fee_usd

    return {
        "success": True,
        "optimal_route": {
            "method": "direct_transfer",
            "chain": "ethereum",
            "estimated_time": "2-5 minutes"
        },
        "cost_breakdown": {
            "donation_amount": amount,
            "donation_token": token,
            "donation_amount_usd": round(amount_usd, 2),
            "gas_fee_eth": round(gas_fee_eth, 6),
            "gas_fee_usd": round(gas_fee_usd, 2),
            "total_cost_usd": round(total_cost_usd, 2)
        },
        "recommendation": {
            "proceed": True,
            "gas_status": "normal" if gas_fee_usd < 10 else "high",
            "notes": []
        }
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

    # 提取參數
    amount = params.get("amount")
    token = params.get("token", "USDC")
    recipient = params.get("recipient")

    if amount is None:
        print(json.dumps({"error": "Missing required parameter: amount"}))
        sys.exit(1)

    if recipient is None:
        print(json.dumps({"error": "Missing required parameter: recipient"}))
        sys.exit(1)

    # 執行優化
    result = asyncio.run(optimize_donation_route(amount, token, recipient))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
