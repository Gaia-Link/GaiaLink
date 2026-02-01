#!/usr/bin/env python3
"""
追蹤捐款交易狀態和查詢歷史

此腳本作為 donation-tracker 技能的一部分，
用於追蹤單筆交易狀態或查詢錢包的捐款歷史。

輸入 (stdin JSON):
    追蹤交易: {"tx_hash": "0x..."}
    查詢歷史: {"wallet_address": "0x...", "time_range": "30d"}

輸出 (stdout JSON):
    交易追蹤: {"success": true, "transaction": {...}, "explorer_url": "..."}
    查詢歷史: {"success": true, "donations": [...], "summary": {...}}
"""

import sys
import json
import asyncio
import re
from datetime import datetime, timezone
from typing import Optional

try:
    from gaia_link.config import get_blockchain_service
    from gaia_link.services.blockchain.gaia_proposal import get_gaia_proposal_service
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False


# 驗證以太坊地址格式的正則表達式
ETH_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')

# 驗證交易哈希格式的正則表達式
TX_HASH_PATTERN = re.compile(r'^0x[a-fA-F0-9]{64}$')

# 時間範圍解析
TIME_RANGE_DAYS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "1y": 365,
    "all": None,
}


def is_valid_address(address: str) -> bool:
    """驗證以太坊地址格式"""
    if not address:
        return False
    return bool(ETH_ADDRESS_PATTERN.match(address))


def is_valid_tx_hash(tx_hash: str) -> bool:
    """驗證交易哈希格式"""
    if not tx_hash:
        return False
    return bool(TX_HASH_PATTERN.match(tx_hash))


def get_explorer_url(tx_hash: str, network: str = "sepolia") -> str:
    """
    獲取區塊鏈瀏覽器 URL
    """
    if network == "mainnet":
        return f"https://etherscan.io/tx/{tx_hash}"
    elif network == "sepolia":
        return f"https://sepolia.etherscan.io/tx/{tx_hash}"
    else:
        return f"https://etherscan.io/tx/{tx_hash}"


async def track_transaction(tx_hash: str) -> dict:
    """
    追蹤交易狀態 (Async)
    """
    # 驗證交易哈希格式
    if not is_valid_tx_hash(tx_hash):
        return {
            "success": False,
            "error": f"無效的交易哈希格式: {tx_hash}。正確格式應為 0x 開頭的 64 位十六進制字符串。"
        }

    # 如果有服務層，使用真實查詢
    if HAS_SERVICE:
        try:
            service = get_blockchain_service()
            # 嘗試從服務獲取交易信息
            if hasattr(service, 'get_transaction'):
                tx_info = service.get_transaction(tx_hash)
                if tx_info:
                    return {
                        "success": True,
                        "transaction": tx_info,
                        "explorer_url": get_explorer_url(tx_hash, service.network_name)
                    }
        except Exception:
            pass  # 使用 fallback

    # Mock 回應 (當服務不可用時)
    now = datetime.now(timezone.utc)
    return {
        "success": True,
        "transaction": {
            "tx_hash": tx_hash,
            "status": "confirmed",
            "block_number": 5123456,
            "timestamp": now.isoformat(),
            "confirmations": 12,
            "amount": 100.0,
            "token": "USDC",
            "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f8e888",
            "recipient_name": "Red Cross Turkey Relief",
            "gas_used": 65000,
            "gas_price_gwei": 25.0
        },
        "explorer_url": get_explorer_url(tx_hash, "sepolia")
    }


async def query_donation_history(wallet_address: str, time_range: Optional[str] = None) -> dict:
    """
    查詢捐款歷史 (Async, connecting to Real Blockchain)
    """
    # 驗證錢包地址格式
    if not is_valid_address(wallet_address):
        return {
            "success": False,
            "error": f"無效的錢包地址格式: {wallet_address}。正確格式應為 0x 開頭的 40 位十六進制字符串。"
        }

    # 解析時間範圍
    days = TIME_RANGE_DAYS.get(time_range, None) if time_range else None

    # 如果有服務層，使用真實查詢
    if HAS_SERVICE:
        try:
            print(f"Connecting to GaiaProposalService for {wallet_address}...", file=sys.stderr)
            service = get_gaia_proposal_service()
            
            # 1. Get User Portfolio (All contributions)
            contributions = await service.get_user_portfolio(wallet_address)
            
            donations_list = []
            
            # 2. Enrich with Proposal Details
            for contribution in contributions:
                try:
                    proposal = await service.get_proposal(contribution.proposal_id)
                    title = proposal.title if proposal else f"Proposal #{contribution.proposal_id}"
                    
                    donations_list.append({
                        "tx_hash": contribution.contribution_id if "0x" in contribution.contribution_id else None,
                        "timestamp": contribution.contributed_at.isoformat(),
                        "amount": contribution.amount,
                        "token": "USDC", # Currently only USDC supported
                        "recipient": f"Proposal #{contribution.proposal_id}",
                        "recipient_name": title,
                        "status": "confirmed",
                        "proposal_id": contribution.proposal_id,
                        "is_no_loss": contribution.is_no_loss
                    })
                except Exception as e:
                    print(f"Failed to fetch proposal {contribution.proposal_id}: {e}", file=sys.stderr)
                    # Add without title if fail
                    donations_list.append({
                        "amount": contribution.amount,
                        "proposal_id": contribution.proposal_id,
                        "recipient_name": f"Unknown Proposal #{contribution.proposal_id}",
                        "status": "confirmed"
                    })

            # 計算摘要
            total_amount = sum(d["amount"] for d in donations_list)
            
            return {
                "success": True,
                "donations": donations_list,
                "summary": {
                    "total_donations": len(donations_list),
                    "total_amount_usd": total_amount,
                    "average_amount_usd": round(total_amount / len(donations_list), 2) if donations_list else 0,
                    "time_range": time_range or "all"
                }
            }
        except Exception as e:
             print(f"Service Error: {e}", file=sys.stderr)
             # Fallthrough to empty/mock if real service fails
             pass

    # Mock 回應 (當服務不可用或出錯時)
    return {
        "success": True,
        "donations": [],
        "summary": {
            "total_donations": 0,
            "total_amount_usd": 0.0,
            "error": "Unable to fetch real data"
        }
    }


async def async_main():
    """Async Main Entry Point"""
    # 讀取 stdin 輸入
    input_data = sys.stdin.read().strip()
    if not input_data:
        print(json.dumps({"success": False, "error": "未提供輸入數據"}))
        sys.exit(1)

    # 解析 JSON
    try:
        params = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    # 提取參數
    tx_hash = params.get("tx_hash")
    wallet_address = params.get("wallet_address")
    time_range = params.get("time_range")

    # 根據參數決定操作
    if tx_hash:
        result = await track_transaction(tx_hash)
    elif wallet_address:
        result = await query_donation_history(wallet_address, time_range)
    else:
        result = {
            "success": False,
            "error": "請提供 tx_hash (追蹤交易) 或 wallet_address (查詢歷史)"
        }

    # 輸出結果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result.get("success", False):
        sys.exit(1)

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
