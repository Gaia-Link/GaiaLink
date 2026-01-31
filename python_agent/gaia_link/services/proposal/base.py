"""
Proposal 服務抽象層

定義 ProposalService 和 WhitelistService 的抽象介面，
支援 Mock 和真實實作的切換。
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from .models import ProposalInfo, ProposalStatus, InstitutionInfo, ContributionInfo


class ProposalService(ABC):
    """
    提案服務抽象類

    定義提案系統的核心操作介面。
    實作類可以是 Mock (本地) 或 Blockchain (鏈上)。
    """

    @abstractmethod
    async def create_proposal(
        self,
        title: str,
        description: str,
        target_amount: float,
        deadline_days: int,
        institution_address: str,
        creator_address: str,
        region: Optional[str] = None,
    ) -> ProposalInfo:
        """
        創建提案

        Args:
            title: 提案標題
            description: 提案描述
            target_amount: 目標金額 (USDC)
            deadline_days: 募資期限 (天數)
            institution_address: 指定機構地址 (必須是白名單)
            creator_address: 創建者地址
            region: 地區標籤

        Returns:
            ProposalInfo: 創建的提案資訊

        Raises:
            ValueError: 機構不在白名單或參數無效
        """
        pass

    @abstractmethod
    async def contribute(
        self,
        proposal_id: str,
        amount: float,
        contributor_address: str,
    ) -> ContributionInfo:
        """
        捐款到提案

        Args:
            proposal_id: 提案 ID
            amount: 捐款金額
            contributor_address: 捐款者地址

        Returns:
            ContributionInfo: 捐款記錄

        Raises:
            ValueError: 提案不存在或狀態不允許捐款
        """
        pass

    @abstractmethod
    async def activate(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> ProposalInfo:
        """
        機構確認提案 (僅機構可調用)

        Args:
            proposal_id: 提案 ID
            institution_address: 機構地址 (必須與提案指定的機構匹配)

        Returns:
            ProposalInfo: 更新後的提案資訊

        Raises:
            ValueError: 非指定機構或狀態不允許
            PermissionError: 非授權機構
        """
        pass

    @abstractmethod
    async def reject(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> ProposalInfo:
        """
        機構拒絕提案 (僅機構可調用)

        Args:
            proposal_id: 提案 ID
            institution_address: 機構地址

        Returns:
            ProposalInfo: 更新後的提案資訊 (狀態變為 CANCELLED)

        Raises:
            ValueError: 非指定機構或狀態不允許
            PermissionError: 非授權機構
        """
        pass

    @abstractmethod
    async def check_and_update_status(
        self,
        proposal_id: str,
    ) -> ProposalInfo:
        """
        檢查並更新提案狀態

        自動處理:
        - 募資達標 → FUNDED
        - 募資截止未達標 → EXPIRED
        - 機構確認超時 (3天) → EXPIRED

        Args:
            proposal_id: 提案 ID

        Returns:
            ProposalInfo: 更新後的提案資訊
        """
        pass

    @abstractmethod
    async def withdraw(
        self,
        proposal_id: str,
        contributor_address: str,
    ) -> ContributionInfo:
        """
        退款 (僅當 EXPIRED 或 CANCELLED)

        Args:
            proposal_id: 提案 ID
            contributor_address: 捐款者地址

        Returns:
            ContributionInfo: 退款記錄

        Raises:
            ValueError: 狀態不允許退款或無捐款記錄
        """
        pass

    @abstractmethod
    async def get_proposal(self, proposal_id: str) -> Optional[ProposalInfo]:
        """獲取提案詳情"""
        pass

    @abstractmethod
    async def list_proposals(
        self,
        status: Optional[ProposalStatus] = None,
        institution: Optional[str] = None,
        region: Optional[str] = None,
        creator: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ProposalInfo]:
        """列出提案 (支援多種篩選條件)"""
        pass

    @abstractmethod
    async def get_contributions(
        self,
        proposal_id: str,
        contributor: Optional[str] = None,
    ) -> List[ContributionInfo]:
        """獲取提案的捐款記錄"""
        pass


class WhitelistService(ABC):
    """
    白名單服務抽象類

    管理經驗證的人道救援機構白名單。
    """

    @abstractmethod
    async def is_whitelisted(self, address: str) -> bool:
        """檢查地址是否在白名單"""
        pass

    @abstractmethod
    async def get_institution(self, address: str) -> Optional[InstitutionInfo]:
        """獲取機構資訊"""
        pass

    @abstractmethod
    async def list_institutions(
        self,
        region: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[InstitutionInfo]:
        """列出白名單機構"""
        pass

    @abstractmethod
    async def add_institution(
        self,
        address: str,
        name: str,
        region: str,
        website: Optional[str] = None,
        description: Optional[str] = None,
    ) -> InstitutionInfo:
        """
        添加機構到白名單 (管理員操作)

        Raises:
            ValueError: 地址已存在
            PermissionError: 非管理員
        """
        pass

    @abstractmethod
    async def update_institution(
        self,
        address: str,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
        region: Optional[str] = None,
    ) -> InstitutionInfo:
        """更新機構資訊"""
        pass
