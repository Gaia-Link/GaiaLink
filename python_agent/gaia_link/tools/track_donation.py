"""
TrackDonationTool - 追蹤捐款工具

用於查詢用戶的捐款歷史記錄。
"""

from typing import Optional, List
from datetime import datetime
import logging

from spoon_ai.tools.base import BaseTool
from gaia_link.services.blockchain.gaia_proposal import get_gaia_proposal_service

logger = logging.getLogger(__name__)

class TrackDonationTool(BaseTool):
    """
    追蹤用戶的捐款歷史與投資組合
    
    當用戶詢問 "List my donations", "My history", "Show detailed donations" 時使用此工具。
    """
    
    name: str = "track_donation"
    description: str = (
        "Retrieve the user's donation history and portfolio status from the blockchain (Gaia Protocol). "
        "Returns a list of proposals the user has contributed to (both Direct and No-Loss)."
    )
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "wallet_address": {
                "type": "string",
                "description": "User's wallet address (optional, will use connected wallet if not provided)"
            },
            "time_range": {
                "type": "string",
                "enum": ["7d", "30d", "90d", "1y", "all"],
                "description": "Time range filter",
                "default": "all"
            }
        },
        "required": []
    }

    async def execute(self, wallet_address: Optional[str] = None, time_range: str = "all") -> dict:
        """執行查詢"""
        service = get_gaia_proposal_service()
        
        # Determine address to query
        if not wallet_address:
            # Try to get from service context if possible, or fail gracefully
            # In SpoonOS, the valid connected wallet is often passed in context or assumed known by frontend
            # Here we might need to rely on the Agent passing it if known, or use the service's default sender if local
            # Ideally the Agent retrieves it from user context.
            # If still None, we can try to use the configured "sender" in blockchain service as fallback for demo
             if service._provider.sender_address:
                 wallet_address = service._provider.sender_address
             else:
                 return {
                     "success": False,
                     "error": "Wallet address is required to list donations. Please connect your wallet."
                 }

        logger.info(f"Tracking donations for {wallet_address}")
        
        try:
            # 1. Get Portfolio
            contributions = await service.get_user_portfolio(wallet_address)
            
            if not contributions:
                return {
                    "success": True,
                    "donations": [],
                    "message": "You haven't made any donations yet.",
                    "summary": {"total_count": 0, "total_amount": 0}
                }

            donations_list = []
            
            # 2. Enrich details
            for contribution in contributions:
                try:
                    proposal = await service.get_proposal(contribution.proposal_id)
                    title = proposal.title if proposal else f"Proposal #{contribution.proposal_id}"
                    
                    donations_list.append({
                        "proposal_id": contribution.proposal_id,
                        "proposal_title": title,
                        "amount": contribution.amount,
                        "token": "USDC",
                        "status": "active" if contribution.amount > 0 else "withdrawn", # simplified
                        "type": "No-Loss" if contribution.is_no_loss else "Direct",
                        "timestamp": contribution.contributed_at.isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch proposal details: {e}")
                    donations_list.append({
                         "proposal_id": contribution.proposal_id,
                         "amount": contribution.amount,
                         "error": "Details unavailable"
                    })

            total_amount = sum(d.get("amount", 0) for d in donations_list)

            return {
                "success": True,
                "donations": donations_list,
                "summary": {
                    "total_count": len(donations_list),
                    "total_amount": total_amount,
                    "currency": "USDC"
                },
                "message": f"Found {len(donations_list)} active donations totaling {total_amount} USDC."
            }

        except Exception as e:
            logger.error(f"TrackDonation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
