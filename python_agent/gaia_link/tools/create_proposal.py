"""
CreateProposalTool - 創建人道救援提案

允許任何人創建提案，但必須指定白名單機構作為接收方。
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_proposal_service, get_whitelist_service


class CreateProposalTool(BaseTool):
    """
    創建人道救援提案工具

    任何人都可以創建提案，但必須指定一個白名單機構作為資金接收方。
    提案創建後進入 FUNDING 狀態，開始接受捐款。
    """

    name: str = "create_proposal"
    description: str = (
        "Create a humanitarian aid proposal. "
        "Must specify a whitelisted institution as the recipient. "
        "Returns proposal ID and details on success."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Proposal title (max 100 characters)",
            },
            "description": {
                "type": "string",
                "description": "Detailed proposal description",
            },
            "target_amount": {
                "type": "number",
                "description": "Target amount in USDC (minimum 100)",
            },
            "deadline_days": {
                "type": "integer",
                "description": "Days until funding deadline (7-90)",
            },
            "institution_address": {
                "type": "string",
                "description": "Address of whitelisted institution",
            },
            "creator_address": {
                "type": "string",
                "description": "Creator's wallet address",
            },
            "region": {
                "type": "string",
                "description": "Target region (optional)",
            },
        },
        "required": [
            "title",
            "description",
            "target_amount",
            "deadline_days",
            "institution_address",
            "creator_address",
        ],
    }

    async def execute(
        self,
        title: str,
        description: str,
        target_amount: float,
        deadline_days: int,
        institution_address: str,
        creator_address: str,
        region: Optional[str] = None,
    ) -> dict:
        """
        執行創建提案

        Args:
            title: 提案標題
            description: 提案描述
            target_amount: 目標金額 (USDC)
            deadline_days: 募資期限 (天數)
            institution_address: 白名單機構地址
            creator_address: 創建者地址
            region: 地區標籤 (可選)

        Returns:
            包含 success 和 proposal 或 error 的字典
        """
        # 驗證白名單
        whitelist = get_whitelist_service()
        if not await whitelist.is_whitelisted(institution_address):
            return {
                "success": False,
                "error": f"Institution {institution_address} is not whitelisted",
            }

        # 驗證期限
        if deadline_days < 7 or deadline_days > 90:
            return {
                "success": False,
                "error": "Deadline must be between 7-90 days",
            }

        # 驗證金額
        if target_amount < 100:
            return {
                "success": False,
                "error": "Target amount must be at least 100 USDC",
            }

        try:
            service = get_proposal_service()
            proposal = await service.create_proposal(
                title=title,
                description=description,
                target_amount=target_amount,
                deadline_days=deadline_days,
                institution_address=institution_address,
                creator_address=creator_address,
                region=region,
            )

            return {
                "success": True,
                "proposal": {
                    "id": proposal.proposal_id,
                    "address": proposal.address,
                    "title": proposal.title,
                    "description": proposal.description,
                    "target_amount": proposal.target_amount,
                    "deadline": proposal.deadline.isoformat(),
                    "institution": proposal.institution_name,
                    "institution_address": proposal.institution,
                    "status": proposal.status.name,
                    "region": proposal.region,
                },
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to create proposal: {e}"}
