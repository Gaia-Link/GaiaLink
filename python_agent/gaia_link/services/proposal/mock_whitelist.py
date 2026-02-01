"""
MockWhitelistService - 白名單服務的 Mock 實作

提供本地記憶體存儲的白名單服務，用於測試和開發。
包含預設的人道救援機構列表。
"""

from typing import Optional, List, Dict

from .base import WhitelistService
from .models import InstitutionInfo


# 預設白名單機構
DEFAULT_INSTITUTIONS = [
    InstitutionInfo(
        address="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",  # Anvil Account 0 (Owner/Red Cross Admin)
        name="International Red Cross",
        region="Global",
        is_active=True,
        total_received=0.0,
        proposals_count=0,
        website="https://www.icrc.org",
        description="International Committee of the Red Cross",
    ),
    InstitutionInfo(
        address="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",  # Anvil Account 1 (UNICEF Admin)
        name="UNICEF",
        region="Global",
        is_active=True,
        total_received=0.0,
        proposals_count=0,
        website="https://www.unicef.org",
        description="United Nations Children's Fund",
    ),
    InstitutionInfo(
        address="0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",  # Anvil Account 2 (MSF)
        name="Doctors Without Borders (MSF)",
        region="Global",
        is_active=True,
        total_received=0.0,
        proposals_count=0,
        website="https://www.msf.org",
        description="Medecins Sans Frontieres",
    ),
    InstitutionInfo(
        address="0x90F79bf6EB2c4f870365E785982E1f101E93b906",  # Anvil Account 3 (Taiwan Red Cross)
        name="Taiwan Red Cross",
        region="Asia",
        is_active=True,
        total_received=0.0,
        proposals_count=0,
        website="https://www.redcross.org.tw",
        description="Taiwan Red Cross Society",
    ),
    InstitutionInfo(
        address="0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",  # Anvil Account 4 (WFP)
        name="World Food Programme",
        region="Global",
        is_active=True,
        total_received=0.0,
        proposals_count=0,
        website="https://www.wfp.org",
        description="United Nations World Food Programme",
    ),
]


class MockWhitelistService(WhitelistService):
    """
    MockWhitelistService - 白名單服務的 Mock 實作

    使用記憶體存儲，適用於測試和開發環境。
    """

    def __init__(self, include_defaults: bool = True):
        """
        初始化 MockWhitelistService

        Args:
            include_defaults: 是否包含預設機構列表
        """
        self._institutions: Dict[str, InstitutionInfo] = {}

        if include_defaults:
            for inst in DEFAULT_INSTITUTIONS:
                self._institutions[inst.address] = InstitutionInfo(
                    address=inst.address,
                    name=inst.name,
                    region=inst.region,
                    is_active=inst.is_active,
                    total_received=inst.total_received,
                    proposals_count=inst.proposals_count,
                    website=inst.website,
                    description=inst.description,
                )

    async def is_whitelisted(self, address: str) -> bool:
        """檢查地址是否在白名單"""
        inst = self._institutions.get(address)
        return inst is not None and inst.is_active

    async def get_institution(self, address: str) -> Optional[InstitutionInfo]:
        """獲取機構資訊"""
        return self._institutions.get(address)

    async def list_institutions(
        self,
        region: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[InstitutionInfo]:
        """列出白名單機構"""
        institutions = list(self._institutions.values())

        # 篩選
        if active_only:
            institutions = [i for i in institutions if i.is_active]

        if region:
            institutions = [i for i in institutions if i.region == region]

        # 分頁
        return institutions[offset:offset + limit]

    async def add_institution(
        self,
        address: str,
        name: str,
        region: str,
        website: Optional[str] = None,
        description: Optional[str] = None,
    ) -> InstitutionInfo:
        """添加機構到白名單"""
        if address in self._institutions:
            raise ValueError(f"Institution already exists: {address}")

        institution = InstitutionInfo(
            address=address,
            name=name,
            region=region,
            is_active=True,
            total_received=0.0,
            proposals_count=0,
            website=website,
            description=description,
        )

        self._institutions[address] = institution
        return institution

    async def update_institution(
        self,
        address: str,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        region: Optional[str] = None,
    ) -> InstitutionInfo:
        """更新機構資訊"""
        if address not in self._institutions:
            raise ValueError(f"Institution not found: {address}")

        inst = self._institutions[address]

        # 創建更新後的實例 (保持 immutability)
        updated = InstitutionInfo(
            address=inst.address,
            name=name if name is not None else inst.name,
            region=region if region is not None else inst.region,
            is_active=is_active if is_active is not None else inst.is_active,
            total_received=inst.total_received,
            proposals_count=inst.proposals_count,
            website=inst.website,
            description=inst.description,
        )

        self._institutions[address] = updated
        return updated

    # === 內部輔助方法 (用於 ProposalService) ===

    def _increment_proposals_count(self, address: str) -> None:
        """增加機構的提案數量 (內部用)"""
        if address in self._institutions:
            inst = self._institutions[address]
            self._institutions[address] = InstitutionInfo(
                address=inst.address,
                name=inst.name,
                region=inst.region,
                is_active=inst.is_active,
                total_received=inst.total_received,
                proposals_count=inst.proposals_count + 1,
                website=inst.website,
                description=inst.description,
            )

    def _add_received_amount(self, address: str, amount: float) -> None:
        """增加機構接收的金額 (內部用)"""
        if address in self._institutions:
            inst = self._institutions[address]
            self._institutions[address] = InstitutionInfo(
                address=inst.address,
                name=inst.name,
                region=inst.region,
                is_active=inst.is_active,
                total_received=inst.total_received + amount,
                proposals_count=inst.proposals_count,
                website=inst.website,
                description=inst.description,
            )
