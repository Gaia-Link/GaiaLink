"""
WithdrawContributionTool - 退款工具

允許捐款者從已過期 (EXPIRED) 或已取消 (CANCELLED) 的提案中提取捐款。
"""

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_proposal_service
from gaia_link.services.proposal.models import ProposalStatus


class WithdrawContributionTool(BaseTool):
    """
    退款工具

    允許捐款者從以下狀態的提案中提取捐款：
    - EXPIRED: 募資截止未達標，或機構超時未確認
    - CANCELLED: 機構拒絕了提案

    已激活 (ACTIVATED) 的提案不允許退款，因為資金已轉移給機構。
    """

    name: str = "withdraw_contribution"
    description: str = (
        "Withdraw contribution from an expired or cancelled proposal. "
        "Only available when proposal status is EXPIRED or CANCELLED."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "proposal_id": {
                "type": "string",
                "description": "Proposal ID to withdraw from",
            },
            "contributor_address": {
                "type": "string",
                "description": "Contributor's wallet address",
            },
        },
        "required": ["proposal_id", "contributor_address"],
    }

    async def execute(
        self,
        proposal_id: str,
        contributor_address: str,
    ) -> dict:
        """
        執行退款

        Args:
            proposal_id: 提案 ID
            contributor_address: 捐款者地址

        Returns:
            包含 success 和 withdrawal 或 error 的字典
        """
        service = get_proposal_service()

        # 檢查提案存在
        proposal = await service.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        # 檢查提案狀態
        if proposal.status not in (ProposalStatus.EXPIRED, ProposalStatus.CANCELLED):
            return {
                "success": False,
                "error": (
                    f"Withdrawal only allowed for EXPIRED or CANCELLED proposals, "
                    f"current: {proposal.status.name}"
                ),
            }

        try:
            contribution = await service.withdraw(
                proposal_id=proposal_id,
                contributor_address=contributor_address,
            )

            return {
                "success": True,
                "withdrawal": {
                    "contributor": contribution.contributor,
                    "amount": contribution.amount,
                    "proposal_id": contribution.proposal_id,
                },
                "message": f"Successfully refunded {contribution.amount:.2f} USDC",
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Withdrawal failed: {e}"}
