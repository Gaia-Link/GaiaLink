"""
ActivateProposalTool - 機構確認並激活提案

僅指定機構可以激活已達標 (FUNDED) 的提案，激活後資金轉移給機構。
"""

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_proposal_service
from gaia_link.services.proposal.models import ProposalStatus


class ActivateProposalTool(BaseTool):
    """
    機構激活提案工具

    僅指定機構可以激活已達標 (FUNDED) 的提案。
    激活後，募集的資金將轉移給機構，狀態變為 ACTIVATED。
    機構必須在 3 天內確認，否則提案將自動過期。
    """

    name: str = "activate_proposal"
    description: str = (
        "Institution confirms and activates a funded proposal. "
        "Only the designated institution can activate. "
        "Funds are transferred to the institution upon activation."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "proposal_id": {
                "type": "string",
                "description": "Proposal ID to activate",
            },
            "institution_address": {
                "type": "string",
                "description": "Institution's wallet address (must match proposal)",
            },
        },
        "required": ["proposal_id", "institution_address"],
    }

    async def execute(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> dict:
        """
        執行激活

        Args:
            proposal_id: 提案 ID
            institution_address: 機構地址 (必須與提案指定的機構匹配)

        Returns:
            包含 success 和 activation 或 error 的字典
        """
        service = get_proposal_service()

        # 檢查提案存在
        proposal = await service.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        # 檢查提案狀態
        if proposal.status != ProposalStatus.FUNDED:
            return {
                "success": False,
                "error": f"Proposal must be FUNDED to activate, current: {proposal.status.name}",
            }

        # 檢查機構權限
        if proposal.institution != institution_address:
            return {
                "success": False,
                "error": "Only the designated institution can activate this proposal",
            }

        try:
            result = await service.activate(
                proposal_id=proposal_id,
                institution_address=institution_address,
            )

            return {
                "success": True,
                "activation": {
                    "proposal_id": result.proposal_id,
                    "status": result.status.name,
                    "funds_transferred": result.total_raised,
                    "institution": result.institution_name,
                },
                "message": f"Funds ({result.total_raised:.2f} USDC) transferred to {result.institution_name}",
            }
        except PermissionError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Activation failed: {e}"}
