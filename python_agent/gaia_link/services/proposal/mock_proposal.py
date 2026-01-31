"""
MockProposalService - 提案服務的 Mock 實作

提供本地記憶體存儲的提案服務，用於測試和開發。
實作完整的狀態機邏輯：FUNDING → FUNDED → ACTIVATED/EXPIRED/CANCELLED
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from .base import ProposalService, WhitelistService
from .models import ProposalInfo, ProposalStatus, ContributionInfo


# 3 天激活窗口 (機構確認期限)
ACTIVATION_WINDOW_DAYS = 3


class MockProposalService(ProposalService):
    """
    MockProposalService - 提案服務的 Mock 實作

    使用記憶體存儲，適用於測試和開發環境。
    實作完整的提案生命週期管理。
    """

    def __init__(self, whitelist_service: WhitelistService):
        """
        初始化 MockProposalService

        Args:
            whitelist_service: 白名單服務實例
        """
        self._whitelist_service = whitelist_service
        self._proposals: Dict[str, ProposalInfo] = {}
        self._contributions: Dict[str, List[ContributionInfo]] = {}  # proposal_id -> contributions
        self._contributor_index: Dict[str, Dict[str, ContributionInfo]] = {}  # proposal_id -> {contributor -> contribution}

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return f"prop-{uuid.uuid4().hex[:8]}"

    def _generate_address(self) -> str:
        """生成模擬合約地址"""
        return f"0x{uuid.uuid4().hex[:40]}"

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
        """創建提案"""
        # 驗證參數
        if target_amount <= 0:
            raise ValueError("Target amount must be positive")

        if deadline_days <= 0:
            raise ValueError("Deadline days must be positive")

        # 驗證機構白名單
        if not await self._whitelist_service.is_whitelisted(institution_address):
            raise ValueError(f"Institution not in whitelist: {institution_address}")

        # 獲取機構資訊
        institution = await self._whitelist_service.get_institution(institution_address)
        institution_name = institution.name if institution else "Unknown"

        # 創建提案
        proposal_id = self._generate_id()
        address = self._generate_address()

        proposal = ProposalInfo(
            proposal_id=proposal_id,
            address=address,
            creator=creator_address,
            institution=institution_address,
            institution_name=institution_name,
            title=title,
            description=description,
            target_amount=target_amount,
            total_raised=0.0,
            deadline=datetime.now() + timedelta(days=deadline_days),
            status=ProposalStatus.FUNDING,
            funded_at=None,
            activation_deadline=None,
            contributors_count=0,
            region=region,
        )

        self._proposals[proposal_id] = proposal
        self._contributions[proposal_id] = []
        self._contributor_index[proposal_id] = {}

        # 更新機構統計
        if hasattr(self._whitelist_service, '_increment_proposals_count'):
            self._whitelist_service._increment_proposals_count(institution_address)

        return proposal

    async def contribute(
        self,
        proposal_id: str,
        amount: float,
        contributor_address: str,
    ) -> ContributionInfo:
        """捐款到提案"""
        # 驗證提案存在
        if proposal_id not in self._proposals:
            raise ValueError(f"Proposal not found: {proposal_id}")

        proposal = self._proposals[proposal_id]

        # 驗證狀態
        if proposal.status != ProposalStatus.FUNDING:
            raise ValueError(f"Proposal status does not allow contributions: {proposal.status.name}")

        # 驗證金額
        if amount <= 0:
            raise ValueError("Contribution amount must be positive")

        # 創建捐款記錄
        contribution = ContributionInfo(
            contributor=contributor_address,
            amount=amount,
            timestamp=datetime.now(),
            proposal_id=proposal_id,
            tx_hash=f"0x{uuid.uuid4().hex}",
        )

        # 更新捐款記錄
        self._contributions[proposal_id].append(contribution)

        # 更新捐款者索引 (用於退款)
        if contributor_address not in self._contributor_index[proposal_id]:
            self._contributor_index[proposal_id][contributor_address] = contribution
        else:
            # 累加金額
            old = self._contributor_index[proposal_id][contributor_address]
            self._contributor_index[proposal_id][contributor_address] = ContributionInfo(
                contributor=contributor_address,
                amount=old.amount + amount,
                timestamp=contribution.timestamp,
                proposal_id=proposal_id,
                tx_hash=contribution.tx_hash,
            )

        # 更新提案
        new_total = proposal.total_raised + amount
        unique_contributors = len(self._contributor_index[proposal_id])

        # 檢查是否達標
        funded_at = proposal.funded_at
        activation_deadline = proposal.activation_deadline
        new_status = proposal.status

        if new_total >= proposal.target_amount and proposal.status == ProposalStatus.FUNDING:
            new_status = ProposalStatus.FUNDED
            funded_at = datetime.now()
            activation_deadline = funded_at + timedelta(days=ACTIVATION_WINDOW_DAYS)

        # 創建更新後的提案
        self._proposals[proposal_id] = ProposalInfo(
            proposal_id=proposal.proposal_id,
            address=proposal.address,
            creator=proposal.creator,
            institution=proposal.institution,
            institution_name=proposal.institution_name,
            title=proposal.title,
            description=proposal.description,
            target_amount=proposal.target_amount,
            total_raised=new_total,
            deadline=proposal.deadline,
            status=new_status,
            funded_at=funded_at,
            activation_deadline=activation_deadline,
            contributors_count=unique_contributors,
            region=proposal.region,
        )

        return contribution

    async def activate(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> ProposalInfo:
        """機構確認提案"""
        # 驗證提案存在
        if proposal_id not in self._proposals:
            raise ValueError(f"Proposal not found: {proposal_id}")

        proposal = self._proposals[proposal_id]

        # 驗證狀態
        if proposal.status != ProposalStatus.FUNDED:
            raise ValueError(f"Proposal must be FUNDED to activate, current status: {proposal.status.name}")

        # 驗證機構
        if proposal.institution != institution_address:
            raise PermissionError(f"Only designated institution can activate this proposal")

        # 激活提案
        self._proposals[proposal_id] = ProposalInfo(
            proposal_id=proposal.proposal_id,
            address=proposal.address,
            creator=proposal.creator,
            institution=proposal.institution,
            institution_name=proposal.institution_name,
            title=proposal.title,
            description=proposal.description,
            target_amount=proposal.target_amount,
            total_raised=proposal.total_raised,
            deadline=proposal.deadline,
            status=ProposalStatus.ACTIVATED,
            funded_at=proposal.funded_at,
            activation_deadline=proposal.activation_deadline,
            contributors_count=proposal.contributors_count,
            region=proposal.region,
        )

        # 更新機構統計
        if hasattr(self._whitelist_service, '_add_received_amount'):
            self._whitelist_service._add_received_amount(institution_address, proposal.total_raised)

        return self._proposals[proposal_id]

    async def reject(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> ProposalInfo:
        """機構拒絕提案"""
        # 驗證提案存在
        if proposal_id not in self._proposals:
            raise ValueError(f"Proposal not found: {proposal_id}")

        proposal = self._proposals[proposal_id]

        # 驗證狀態
        if proposal.status != ProposalStatus.FUNDED:
            raise ValueError(f"Proposal must be FUNDED to reject, current status: {proposal.status.name}")

        # 驗證機構
        if proposal.institution != institution_address:
            raise PermissionError(f"Only designated institution can reject this proposal")

        # 取消提案
        self._proposals[proposal_id] = ProposalInfo(
            proposal_id=proposal.proposal_id,
            address=proposal.address,
            creator=proposal.creator,
            institution=proposal.institution,
            institution_name=proposal.institution_name,
            title=proposal.title,
            description=proposal.description,
            target_amount=proposal.target_amount,
            total_raised=proposal.total_raised,
            deadline=proposal.deadline,
            status=ProposalStatus.CANCELLED,
            funded_at=proposal.funded_at,
            activation_deadline=proposal.activation_deadline,
            contributors_count=proposal.contributors_count,
            region=proposal.region,
        )

        return self._proposals[proposal_id]

    async def check_and_update_status(
        self,
        proposal_id: str,
    ) -> ProposalInfo:
        """檢查並更新提案狀態"""
        if proposal_id not in self._proposals:
            raise ValueError(f"Proposal not found: {proposal_id}")

        proposal = self._proposals[proposal_id]
        now = datetime.now()
        new_status = proposal.status

        # 檢查募資截止 (FUNDING → EXPIRED)
        if proposal.status == ProposalStatus.FUNDING:
            if now > proposal.deadline:
                new_status = ProposalStatus.EXPIRED

        # 檢查激活截止 (FUNDED → EXPIRED)
        elif proposal.status == ProposalStatus.FUNDED:
            if proposal.activation_deadline and now > proposal.activation_deadline:
                new_status = ProposalStatus.EXPIRED

        # 更新狀態
        if new_status != proposal.status:
            self._proposals[proposal_id] = ProposalInfo(
                proposal_id=proposal.proposal_id,
                address=proposal.address,
                creator=proposal.creator,
                institution=proposal.institution,
                institution_name=proposal.institution_name,
                title=proposal.title,
                description=proposal.description,
                target_amount=proposal.target_amount,
                total_raised=proposal.total_raised,
                deadline=proposal.deadline,
                status=new_status,
                funded_at=proposal.funded_at,
                activation_deadline=proposal.activation_deadline,
                contributors_count=proposal.contributors_count,
                region=proposal.region,
            )

        return self._proposals[proposal_id]

    async def withdraw(
        self,
        proposal_id: str,
        contributor_address: str,
    ) -> ContributionInfo:
        """退款"""
        # 驗證提案存在
        if proposal_id not in self._proposals:
            raise ValueError(f"Proposal not found: {proposal_id}")

        proposal = self._proposals[proposal_id]

        # 驗證狀態 (只有 EXPIRED 或 CANCELLED 可以退款)
        if proposal.status not in (ProposalStatus.EXPIRED, ProposalStatus.CANCELLED):
            raise ValueError(f"Cannot withdraw from proposal with status: {proposal.status.name}")

        # 驗證捐款記錄
        if proposal_id not in self._contributor_index:
            raise ValueError(f"No contributions found for proposal: {proposal_id}")

        if contributor_address not in self._contributor_index[proposal_id]:
            raise ValueError(f"No contribution found for contributor: {contributor_address}")

        # 獲取並移除捐款記錄
        contribution = self._contributor_index[proposal_id].pop(contributor_address)

        # 更新提案總額
        new_total = proposal.total_raised - contribution.amount
        new_count = len(self._contributor_index[proposal_id])

        self._proposals[proposal_id] = ProposalInfo(
            proposal_id=proposal.proposal_id,
            address=proposal.address,
            creator=proposal.creator,
            institution=proposal.institution,
            institution_name=proposal.institution_name,
            title=proposal.title,
            description=proposal.description,
            target_amount=proposal.target_amount,
            total_raised=new_total,
            deadline=proposal.deadline,
            status=proposal.status,
            funded_at=proposal.funded_at,
            activation_deadline=proposal.activation_deadline,
            contributors_count=new_count,
            region=proposal.region,
        )

        return contribution

    async def get_proposal(self, proposal_id: str) -> Optional[ProposalInfo]:
        """獲取提案詳情"""
        return self._proposals.get(proposal_id)

    async def list_proposals(
        self,
        status: Optional[ProposalStatus] = None,
        institution: Optional[str] = None,
        region: Optional[str] = None,
        creator: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ProposalInfo]:
        """列出提案"""
        proposals = list(self._proposals.values())

        # 篩選
        if status is not None:
            proposals = [p for p in proposals if p.status == status]

        if institution:
            proposals = [p for p in proposals if p.institution == institution]

        if region:
            proposals = [p for p in proposals if p.region == region]

        if creator:
            proposals = [p for p in proposals if p.creator == creator]

        # 按創建時間排序 (新的在前)
        proposals.sort(key=lambda p: p.deadline, reverse=True)

        # 分頁
        return proposals[offset:offset + limit]

    async def get_contributions(
        self,
        proposal_id: str,
        contributor: Optional[str] = None,
    ) -> List[ContributionInfo]:
        """獲取提案的捐款記錄"""
        if proposal_id not in self._contributions:
            return []

        contributions = self._contributions[proposal_id]

        if contributor:
            contributions = [c for c in contributions if c.contributor == contributor]

        return contributions
