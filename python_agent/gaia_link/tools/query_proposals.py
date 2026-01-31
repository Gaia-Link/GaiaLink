"""
QueryProposalsTool - 查詢提案

支援多種篩選條件查詢提案列表。
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_proposal_service
from gaia_link.services.proposal.models import ProposalStatus


class QueryProposalsTool(BaseTool):
    """
    查詢提案工具

    支援按狀態、機構、地區等條件篩選提案。
    返回提案列表及進度資訊。
    """

    name: str = "query_proposals"
    description: str = (
        "Query humanitarian aid proposals with optional filters. "
        "Returns proposal list with funding progress."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["FUNDING", "FUNDED", "ACTIVATED", "EXPIRED", "CANCELLED"],
                "description": "Filter by proposal status",
            },
            "institution": {
                "type": "string",
                "description": "Filter by institution address",
            },
            "region": {
                "type": "string",
                "description": "Filter by region",
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "description": "Maximum number of results (1-100)",
            },
        },
    }

    async def execute(
        self,
        status: Optional[str] = None,
        institution: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20,
    ) -> dict:
        """
        執行查詢

        Args:
            status: 按狀態篩選
            institution: 按機構地址篩選
            region: 按地區篩選
            limit: 最大結果數 (默認 20)

        Returns:
            包含 proposals 列表和 total_count 的字典
        """
        service = get_proposal_service()

        # 轉換狀態字串為枚舉
        status_enum = None
        if status:
            try:
                status_enum = ProposalStatus[status]
            except KeyError:
                return {
                    "success": False,
                    "error": f"Invalid status: {status}. Must be one of: FUNDING, FUNDED, ACTIVATED, EXPIRED, CANCELLED",
                }

        # 限制 limit 範圍
        limit = max(1, min(100, limit))

        try:
            proposals = await service.list_proposals(
                status=status_enum,
                institution=institution,
                region=region,
                limit=limit,
            )

            return {
                "proposals": [
                    {
                        "id": p.proposal_id,
                        "title": p.title,
                        "description": p.description[:100] + "..." if len(p.description) > 100 else p.description,
                        "institution": p.institution_name,
                        "institution_address": p.institution,
                        "target_amount": p.target_amount,
                        "total_raised": p.total_raised,
                        "progress_percent": p.progress_percent,
                        "status": p.status.name,
                        "deadline": p.deadline.isoformat(),
                        "region": p.region,
                        "contributors_count": p.contributors_count,
                    }
                    for p in proposals
                ],
                "total_count": len(proposals),
            }
        except Exception as e:
            return {"success": False, "error": f"Query failed: {e}"}
