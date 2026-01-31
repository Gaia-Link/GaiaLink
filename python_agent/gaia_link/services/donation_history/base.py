"""
Donation History 服務抽象基類

定義捐款歷史查詢服務的接口。
"""

from abc import ABC, abstractmethod
from typing import Optional

from gaia_link.services.donation_history.models import (
    DonationRecord,
    DonationHistoryResult,
)


class DonationHistoryService(ABC):
    """
    捐款歷史服務抽象基類

    定義查詢捐款歷史的標準接口，支援 Mock 和真實實作切換。
    """

    @abstractmethod
    async def get_history(
        self,
        wallet_address: str,
        time_range: str = "30d",
        limit: int = 50,
    ) -> DonationHistoryResult:
        """
        獲取用戶捐款歷史

        Args:
            wallet_address: 用戶錢包地址
            time_range: 時間範圍 (7d, 30d, 90d, 365d, all)
            limit: 返回最大筆數

        Returns:
            DonationHistoryResult: 捐款歷史結果
        """
        pass

    @abstractmethod
    async def get_transaction(
        self,
        tx_hash: str,
    ) -> Optional[DonationRecord]:
        """
        查詢單筆交易

        Args:
            tx_hash: 交易哈希

        Returns:
            DonationRecord: 捐款記錄，不存在則返回 None
        """
        pass
