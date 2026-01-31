"""
ContributeProposalTool - 捐款到提案

允許任何人向處於 FUNDING 狀態的提案捐款。
"""

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_proposal_service
from gaia_link.services.proposal.models import ProposalStatus


class ContributeProposalTool(BaseTool):
    """
    捐款到提案工具

    向處於 FUNDING 狀態的提案捐款。
    當捐款使提案達到目標金額時，狀態自動變為 FUNDED。
    """

    name: str = "contribute_proposal"
    description: str = (
        "Contribute funds to a humanitarian aid proposal. "
        "Only proposals in FUNDING status can receive contributions."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "proposal_id": {
                "type": "string",
                "description": "Proposal ID to contribute to",
            },
            "amount": {
                "type": "number",
                "description": "Amount to contribute in USDC (minimum 1)",
            },
            "contributor_address": {
                "type": "string",
                "description": "Contributor's wallet address",
            },
        },
        "required": ["proposal_id", "amount", "contributor_address"],
    }

    async def execute(
        self,
        proposal_id: str,
        amount: float,
        contributor_address: str,
    ) -> dict:
        """
        執行捐款

        Args:
            proposal_id: 提案 ID
            amount: 捐款金額 (USDC)
            contributor_address: 捐款者地址

        Returns:
            包含 success 和 contribution 或 error 的字典
        """
        service = get_proposal_service()

        # 檢查提案存在
        proposal = await service.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        # 檢查提案狀態
        if proposal.status != ProposalStatus.FUNDING:
            return {
                "success": False,
                "error": f"Proposal is {proposal.status.name}, not accepting contributions",
            }

        # 驗證金額
        if amount < 1:
            return {
                "success": False,
                "error": "Contribution amount must be at least 1 USDC",
            }

        try:
            contribution = await service.contribute(
                proposal_id=proposal_id,
                amount=amount,
                contributor_address=contributor_address,
            )

            # 獲取更新後的提案資訊
            updated_proposal = await service.get_proposal(proposal_id)

            return {
                "success": True,
                "contribution": {
                    "contributor": contribution.contributor,
                    "amount": contribution.amount,
                    "timestamp": contribution.timestamp.isoformat(),
                    "tx_hash": contribution.tx_hash,
                },
                "proposal_progress": {
                    "total_raised": updated_proposal.total_raised,
                    "target_amount": updated_proposal.target_amount,
                    "percentage": updated_proposal.progress_percent,
                    "status": updated_proposal.status.name,
                    "contributors_count": updated_proposal.contributors_count,
                },
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Contribution failed: {e}"}
