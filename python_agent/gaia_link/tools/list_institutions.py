"""
ListInstitutionsTool - 列出白名單機構

列出所有經驗證的人道救援機構。
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_whitelist_service


class ListInstitutionsTool(BaseTool):
    """
    列出白名單機構工具

    列出所有經驗證的人道救援機構，支援按地區篩選。
    只有白名單機構可以作為提案的資金接收方。
    """

    name: str = "list_institutions"
    description: str = (
        "List whitelisted humanitarian institutions. "
        "Only these institutions can receive funds from proposals."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "Filter by region (e.g., 'Asia', 'Europe', 'Global')",
            },
            "active_only": {
                "type": "boolean",
                "default": True,
                "description": "Only show active institutions",
            },
        },
    }

    async def execute(
        self,
        region: Optional[str] = None,
        active_only: bool = True,
    ) -> dict:
        """
        執行查詢

        Args:
            region: 按地區篩選 (可選)
            active_only: 只顯示活躍機構 (默認 True)

        Returns:
            包含 institutions 列表和 total_count 的字典
        """
        service = get_whitelist_service()

        try:
            institutions = await service.list_institutions(
                region=region,
                active_only=active_only,
            )

            return {
                "institutions": [
                    {
                        "address": i.address,
                        "name": i.name,
                        "region": i.region,
                        "is_active": i.is_active,
                        "total_received": i.total_received,
                        "proposals_count": i.proposals_count,
                        "website": i.website,
                        "description": i.description,
                    }
                    for i in institutions
                ],
                "total_count": len(institutions),
            }
        except Exception as e:
            return {"success": False, "error": f"Query failed: {e}"}
