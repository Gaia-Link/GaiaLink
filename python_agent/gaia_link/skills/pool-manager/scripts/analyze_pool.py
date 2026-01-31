#!/usr/bin/env python3
"""
分析資金池狀態和收益

此腳本作為 pool-manager 技能的一部分，
用於分析資金池的當前狀態和收益情況。

輸入 (stdin JSON):
    {"pool_id": "vault_001"} 或 {"action": "list"}

輸出 (stdout JSON):
    {"pool_status": {...}, "yield_info": {...}, ...}

Phase 4 重構: 使用 Service 層替代硬編碼數據
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# 添加項目路徑以支援直接執行腳本
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_script_dir, "..", "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 嘗試導入 Service 層
try:
    from gaia_link.services.pool import (
        get_pool_service,
        PoolInfo,
        VaultType,
    )
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False


async def get_pool_status_async(pool_id: str) -> dict:
    """
    獲取指定池子的狀態 (異步版本)

    Args:
        pool_id: 池子 ID

    Returns:
        池子狀態字典
    """
    if not HAS_SERVICE:
        return get_pool_status_fallback(pool_id)

    try:
        service = get_pool_service()
        pool = await service.get_pool(pool_id)

        if not pool:
            return {
                "success": False,
                "error": f"Pool not found: {pool_id}"
            }

        # 獲取建議
        recommendation = await service.get_pool_recommendation(pool)

        return {
            "success": True,
            "pool_status": {
                **pool.to_dict(),
            },
            "yield_info": {
                "earned_usd": pool.yield_earned,
                "apy_estimate": 4.5 if pool.vault_type == VaultType.YIELD else 0,
                "protocol": "Euler" if pool.vault_type == VaultType.YIELD else None,
            },
            "recommendation": recommendation.to_dict(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching pool: {str(e)}"
        }


async def list_all_pools_async() -> dict:
    """
    列出所有池子 (異步版本)

    Returns:
        所有池子的列表
    """
    if not HAS_SERVICE:
        return list_all_pools_fallback()

    try:
        service = get_pool_service()
        result = await service.list_pools(active_only=True)

        pools_list = []
        for pool in result.pools:
            pools_list.append({
                "vault_id": pool.vault_id,
                "name": pool.name,
                "vault_type": pool.vault_type.value,
                "current_amount": pool.current_amount,
                "progress_percent": pool.progress_percent,
            })

        return {
            "success": True,
            "pools": pools_list,
            "summary": {
                "total_pools": result.total_pools,
                "total_value_usd": result.total_value,
                "total_yield_earned_usd": result.total_yield,
                "timestamp": datetime.now().isoformat(),
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing pools: {str(e)}"
        }


# =============================================================================
# Fallback 實現 (當 Service 層不可用時)
# =============================================================================


# Mock 資金池數據 (fallback)
MOCK_POOLS = {
    "vault_001": {
        "vault_id": "vault_001",
        "name": "Turkey Earthquake Relief",
        "vault_type": "yield",
        "creator_type": "organization",
        "beneficiary_org_id": "org_redcross",
        "target_amount": 100000.0,
        "current_amount": 65000.0,
        "yield_earned": 1250.0,
        "region": "Turkey",
        "is_active": True,
        "created_at": "2024-01-15",
    },
    "vault_002": {
        "vault_id": "vault_002",
        "name": "Philippines Typhoon Aid",
        "vault_type": "direct",
        "creator_type": "community",
        "beneficiary_org_id": "org_unicef",
        "target_amount": 50000.0,
        "current_amount": 32000.0,
        "yield_earned": 0.0,
        "region": "Philippines",
        "is_active": True,
        "created_at": "2024-02-01",
    },
    "vault_003": {
        "vault_id": "vault_003",
        "name": "Gaza Humanitarian Fund",
        "vault_type": "yield",
        "creator_type": "organization",
        "beneficiary_org_id": "org_who",
        "target_amount": 200000.0,
        "current_amount": 180000.0,
        "yield_earned": 4500.0,
        "region": "Gaza",
        "is_active": True,
        "created_at": "2024-01-01",
    },
}


def get_pool_recommendation_fallback(pool: dict) -> dict:
    """
    根據池子狀態生成建議 (fallback 版本)

    Args:
        pool: 池子數據

    Returns:
        建議字典
    """
    recommendations = []
    priority = "NORMAL"

    progress = pool["current_amount"] / pool["target_amount"] if pool["target_amount"] > 0 else 0

    if progress >= 0.9:
        recommendations.append("Pool is nearly at target. Consider opening a new pool.")
        priority = "LOW"
    elif progress < 0.3:
        recommendations.append("Pool needs more funding. Consider promoting on social media.")
        priority = "HIGH"

    if pool["vault_type"] == "yield" and pool["yield_earned"] > 0:
        recommendations.append(f"Yield earned: ${pool['yield_earned']}. Consider distributing to beneficiary.")

    return {
        "priority": priority,
        "items": recommendations,
    }


def get_pool_status_fallback(pool_id: str) -> dict:
    """
    獲取指定池子的狀態 (fallback 版本)

    Args:
        pool_id: 池子 ID

    Returns:
        池子狀態字典
    """
    pool = MOCK_POOLS.get(pool_id)
    if not pool:
        return {
            "success": False,
            "error": f"Pool not found: {pool_id}"
        }

    # 計算進度
    progress = pool["current_amount"] / pool["target_amount"] if pool["target_amount"] > 0 else 0

    return {
        "success": True,
        "pool_status": {
            **pool,
            "progress_percent": round(progress * 100, 1),
            "remaining_amount": pool["target_amount"] - pool["current_amount"],
        },
        "yield_info": {
            "earned_usd": pool["yield_earned"],
            "apy_estimate": 4.5 if pool["vault_type"] == "yield" else 0,
            "protocol": "Euler" if pool["vault_type"] == "yield" else None,
        },
        "recommendation": get_pool_recommendation_fallback(pool),
    }


def list_all_pools_fallback() -> dict:
    """
    列出所有池子 (fallback 版本)

    Returns:
        所有池子的列表
    """
    pools_list = []
    total_value = 0
    total_yield = 0

    for pool_id, pool in MOCK_POOLS.items():
        if pool["is_active"]:
            pools_list.append({
                "vault_id": pool["vault_id"],
                "name": pool["name"],
                "vault_type": pool["vault_type"],
                "current_amount": pool["current_amount"],
                "progress_percent": round(pool["current_amount"] / pool["target_amount"] * 100, 1),
            })
            total_value += pool["current_amount"]
            total_yield += pool["yield_earned"]

    return {
        "success": True,
        "pools": pools_list,
        "summary": {
            "total_pools": len(pools_list),
            "total_value_usd": total_value,
            "total_yield_earned_usd": total_yield,
            "timestamp": datetime.now().isoformat(),
        }
    }


# =============================================================================
# 主入口
# =============================================================================


def main():
    """主入口點"""
    # 讀取 stdin 輸入
    input_data = sys.stdin.read().strip()
    if not input_data:
        # 默認列出所有池子
        if HAS_SERVICE:
            result = asyncio.run(list_all_pools_async())
        else:
            result = list_all_pools_fallback()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 解析 JSON
    try:
        params = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    # 處理請求
    action = params.get("action", "query")
    pool_id = params.get("pool_id")

    if action == "list" or not pool_id:
        if HAS_SERVICE:
            result = asyncio.run(list_all_pools_async())
        else:
            result = list_all_pools_fallback()
    else:
        if HAS_SERVICE:
            result = asyncio.run(get_pool_status_async(pool_id))
        else:
            result = get_pool_status_fallback(pool_id)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
