"""
Pool 數據模型

定義資金池記錄和查詢結果的數據類型。
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class VaultType(str, Enum):
    """資金池類型"""
    DIRECT = "direct"
    YIELD = "yield"


class CreatorType(str, Enum):
    """創建者類型"""
    ORGANIZATION = "organization"
    COMMUNITY = "community"


class RecommendationPriority(str, Enum):
    """建議優先級"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


@dataclass
class PoolInfo:
    """
    資金池信息

    Attributes:
        vault_id: 資金池 ID
        name: 資金池名稱
        vault_type: 資金池類型 (direct, yield)
        creator_type: 創建者類型 (organization, community)
        beneficiary_org_id: 受益機構 ID
        target_amount: 目標金額
        current_amount: 當前金額
        yield_earned: 已賺取收益
        region: 區域
        is_active: 是否啟用
        created_at: 創建時間
    """
    vault_id: str
    name: str
    vault_type: VaultType
    creator_type: CreatorType
    beneficiary_org_id: str
    target_amount: float
    current_amount: float
    yield_earned: float
    region: str
    is_active: bool
    created_at: str

    @property
    def progress_percent(self) -> float:
        """計算進度百分比"""
        if self.target_amount <= 0:
            return 0.0
        return round((self.current_amount / self.target_amount) * 100, 1)

    @property
    def remaining_amount(self) -> float:
        """計算剩餘金額"""
        return self.target_amount - self.current_amount

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "vault_id": self.vault_id,
            "name": self.name,
            "vault_type": self.vault_type.value,
            "creator_type": self.creator_type.value,
            "beneficiary_org_id": self.beneficiary_org_id,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "yield_earned": self.yield_earned,
            "region": self.region,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "progress_percent": self.progress_percent,
            "remaining_amount": self.remaining_amount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PoolInfo":
        """從字典創建實例"""
        return cls(
            vault_id=data["vault_id"],
            name=data["name"],
            vault_type=VaultType(data["vault_type"]),
            creator_type=CreatorType(data["creator_type"]),
            beneficiary_org_id=data["beneficiary_org_id"],
            target_amount=data["target_amount"],
            current_amount=data["current_amount"],
            yield_earned=data["yield_earned"],
            region=data["region"],
            is_active=data["is_active"],
            created_at=data["created_at"],
        )


@dataclass
class PoolListResult:
    """
    資金池列表查詢結果

    Attributes:
        pools: 資金池列表
        total_value: 總價值
        total_yield: 總收益
    """
    pools: List[PoolInfo]
    total_value: float
    total_yield: float

    @property
    def total_pools(self) -> int:
        """資金池數量"""
        return len(self.pools)

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "pools": [p.to_dict() for p in self.pools],
            "total_value": self.total_value,
            "total_yield": self.total_yield,
            "total_pools": self.total_pools,
        }


@dataclass
class PoolRecommendation:
    """
    資金池建議

    Attributes:
        priority: 優先級 (LOW, NORMAL, HIGH)
        items: 建議項目列表
    """
    priority: RecommendationPriority
    items: List[str]

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "priority": self.priority.value,
            "items": self.items,
        }


@dataclass
class YieldInfo:
    """
    收益信息

    Attributes:
        earned_usd: 已賺取收益 (USD)
        apy_estimate: 預估年化收益率
        protocol: 使用的 DeFi 協議
    """
    earned_usd: float
    apy_estimate: float
    protocol: Optional[str]

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "earned_usd": self.earned_usd,
            "apy_estimate": self.apy_estimate,
            "protocol": self.protocol,
        }
