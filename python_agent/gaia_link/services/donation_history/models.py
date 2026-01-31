"""
Donation History 數據模型

定義捐款記錄和查詢結果的數據類型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class DonationStatus(str, Enum):
    """捐款狀態"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class VaultType(str, Enum):
    """資金池類型"""
    DIRECT = "DIRECT"
    NO_LOSS = "NO_LOSS"


@dataclass
class DonationRecord:
    """
    單筆捐款記錄

    Attributes:
        tx_hash: 交易哈希
        amount: 捐款金額
        token: 代幣類型 (USDC, USDT, ETH, DAI)
        recipient: 接收者名稱 (機構或危機名稱)
        recipient_address: 接收者錢包地址
        timestamp: 交易時間
        status: 交易狀態 (pending, confirmed, failed)
        vault_type: 資金池類型 (DIRECT, NO_LOSS)
    """
    tx_hash: str
    amount: float
    token: str
    recipient: str
    recipient_address: str
    timestamp: datetime
    status: DonationStatus
    vault_type: VaultType = VaultType.DIRECT

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "tx_hash": self.tx_hash,
            "amount": self.amount,
            "token": self.token,
            "recipient": self.recipient,
            "recipient_address": self.recipient_address,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "vault_type": self.vault_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonationRecord":
        """從字典創建實例"""
        return cls(
            tx_hash=data["tx_hash"],
            amount=data["amount"],
            token=data["token"],
            recipient=data["recipient"],
            recipient_address=data["recipient_address"],
            timestamp=datetime.fromisoformat(data["timestamp"])
                if isinstance(data["timestamp"], str)
                else data["timestamp"],
            status=DonationStatus(data["status"]),
            vault_type=VaultType(data.get("vault_type", "DIRECT")),
        )


@dataclass
class DonationHistoryResult:
    """
    捐款歷史查詢結果

    Attributes:
        donations: 捐款記錄列表
        total_amount_usd: 總捐款金額 (USD)
        total_count: 總捐款筆數
        time_range: 查詢時間範圍描述
    """
    donations: List[DonationRecord]
    total_amount_usd: float
    total_count: int
    time_range: str

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "donations": [d.to_dict() for d in self.donations],
            "total_amount_usd": self.total_amount_usd,
            "total_count": self.total_count,
            "time_range": self.time_range,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonationHistoryResult":
        """從字典創建實例"""
        return cls(
            donations=[DonationRecord.from_dict(d) for d in data["donations"]],
            total_amount_usd=data["total_amount_usd"],
            total_count=data["total_count"],
            time_range=data["time_range"],
        )
