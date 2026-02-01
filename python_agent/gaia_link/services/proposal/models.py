"""
Proposal 系統數據模型

定義提案系統的核心數據結構，符合 IMPLEMENTATION_PLAN_V2.md 規範。
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


class ProposalStatus(IntEnum):
    """
    提案狀態

    狀態機流程:
    FUNDING → FUNDED → ACTIVATED
                    ↘ EXPIRED
                    ↘ CANCELLED
    """
    FUNDING = 0      # 募資中
    FUNDED = 1       # 達標，等待機構確認
    ACTIVATED = 2    # 已激活，資金已轉移
    EXPIRED = 3      # 過期 (未達標 或 機構超時未確認)
    CANCELLED = 4    # 取消 (機構拒絕)


@dataclass
class ProposalInfo:
    """
    提案資訊

    包含提案的完整狀態資訊，用於查詢和顯示。
    """
    proposal_id: str
    address: str                    # 合約地址
    creator: str                    # 創建者地址
    institution: str                # 機構地址 (whitelisted)
    institution_name: str           # 機構名稱
    title: str
    description: str
    target_amount: float            # 目標金額 (USDC)
    total_raised: float             # 已募集金額
    deadline: datetime              # 募資截止時間
    status: ProposalStatus
    funded_at: Optional[datetime] = None   # 達標時間 (None if not funded)
    activation_deadline: Optional[datetime] = None  # 機構確認截止 (funded_at + 3 days)
    contributors_count: int = 0
    region: Optional[str] = None
    location: Optional[dict] = None  # {lat: float, lng: float}

    @property
    def progress_percent(self) -> float:
        """募資進度百分比"""
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, (self.total_raised / self.target_amount) * 100)

    @property
    def is_funded(self) -> bool:
        """是否已達標"""
        return self.total_raised >= self.target_amount

    @property
    def remaining_amount(self) -> float:
        """剩餘募資金額"""
        return max(0.0, self.target_amount - self.total_raised)


@dataclass
class ContributionInfo:
    """
    捐款記錄

    追蹤每筆捐款的詳細資訊，用於退款和審計。
    """
    contributor: str
    amount: float
    timestamp: datetime
    proposal_id: str
    tx_hash: Optional[str] = None   # 交易哈希


@dataclass
class InstitutionInfo:
    """
    白名單機構資訊

    儲存經驗證的人道救援機構資訊。
    """
    address: str
    name: str
    region: str
    is_active: bool = True
    total_received: float = 0.0
    proposals_count: int = 0
    website: Optional[str] = None
    description: Optional[str] = None
