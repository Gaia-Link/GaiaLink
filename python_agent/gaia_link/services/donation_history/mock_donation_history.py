"""
Mock Donation History 服務

提供 Demo 數據的捐款歷史查詢服務。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from gaia_link.services.donation_history.base import DonationHistoryService
from gaia_link.services.donation_history.models import (
    DonationRecord,
    DonationHistoryResult,
    DonationStatus,
    VaultType,
)


class MockDonationHistoryService(DonationHistoryService):
    """
    Mock 捐款歷史服務

    提供預設的 Demo 數據，用於開發和測試。
    """

    def __init__(self):
        """初始化 Mock 數據"""
        self._donations: Dict[str, List[DonationRecord]] = {}
        self._tx_index: Dict[str, DonationRecord] = {}
        self._initialize_demo_data()

    def _initialize_demo_data(self):
        """初始化 Demo 數據"""
        now = datetime.now()

        # Demo 錢包地址列表
        demo_wallets = [
            "0xTestWallet123",
            "0xDemoWallet",
            "0x1234567890123456789012345678901234567890",
        ]

        # 為每個 Demo 錢包創建捐款記錄
        demo_records = [
            # 最近 7 天內的捐款
            DonationRecord(
                tx_hash="0xabc123def456789012345678901234567890abcdef1234567890abcdef12345678",
                amount=100.0,
                token="USDC",
                recipient="Red Cross Turkey",
                recipient_address="0xRedCross111111111111111111111111111111111",
                timestamp=now - timedelta(days=2),
                status=DonationStatus.CONFIRMED,
                vault_type=VaultType.DIRECT,
            ),
            DonationRecord(
                tx_hash="0xdef456abc789012345678901234567890abcdef5678901234567890abcdef6789",
                amount=50.0,
                token="ETH",
                recipient="Gaza Relief Fund",
                recipient_address="0xGazaFund222222222222222222222222222222222",
                timestamp=now - timedelta(days=5),
                status=DonationStatus.CONFIRMED,
                vault_type=VaultType.NO_LOSS,
            ),
            # 7-30 天內的捐款
            DonationRecord(
                tx_hash="0x789ghi012345678901234567890abcdef123456789012345678901234567890ab",
                amount=200.0,
                token="USDT",
                recipient="Ukraine Humanitarian Aid",
                recipient_address="0xUkraineAid333333333333333333333333333333",
                timestamp=now - timedelta(days=15),
                status=DonationStatus.CONFIRMED,
                vault_type=VaultType.DIRECT,
            ),
            DonationRecord(
                tx_hash="0x012jkl345678901234567890abcdef6789012345678901234567890abcdef0123",
                amount=75.0,
                token="DAI",
                recipient="Syria Emergency Response",
                recipient_address="0xSyriaHelp444444444444444444444444444444",
                timestamp=now - timedelta(days=20),
                status=DonationStatus.CONFIRMED,
                vault_type=VaultType.DIRECT,
            ),
            # 30-90 天內的捐款
            DonationRecord(
                tx_hash="0x345mno678901234567890abcdef12345678901234567890abcdef345678901234",
                amount=150.0,
                token="USDC",
                recipient="Morocco Earthquake Relief",
                recipient_address="0xMorocco555555555555555555555555555555555",
                timestamp=now - timedelta(days=45),
                status=DonationStatus.CONFIRMED,
                vault_type=VaultType.NO_LOSS,
            ),
            # Pending 狀態的捐款
            DonationRecord(
                tx_hash="0x678pqr901234567890abcdef678901234567890abcdef678901234567890abcde",
                amount=25.0,
                token="USDC",
                recipient="Global Crisis Fund",
                recipient_address="0xGlobalFund666666666666666666666666666666",
                timestamp=now - timedelta(hours=2),
                status=DonationStatus.PENDING,
                vault_type=VaultType.DIRECT,
            ),
        ]

        # 為每個 Demo 錢包添加相同的記錄
        for wallet in demo_wallets:
            self._donations[wallet.lower()] = demo_records.copy()

        # 建立交易索引
        for record in demo_records:
            self._tx_index[record.tx_hash.lower()] = record

    def _parse_time_range(self, time_range: str) -> timedelta:
        """
        解析時間範圍字符串

        Args:
            time_range: 時間範圍 (7d, 30d, 90d, 365d, all)

        Returns:
            timedelta: 時間範圍
        """
        time_map = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
            "365d": timedelta(days=365),
            "all": timedelta(days=36500),  # ~100 years
        }
        return time_map.get(time_range, timedelta(days=30))

    def _calculate_usd_amount(self, amount: float, token: str) -> float:
        """
        計算 USD 金額

        Args:
            amount: 代幣數量
            token: 代幣類型

        Returns:
            float: USD 金額
        """
        # 簡化的價格映射 (實際應該從 Oracle 獲取)
        token_prices = {
            "USDC": 1.0,
            "USDT": 1.0,
            "DAI": 1.0,
            "ETH": 2500.0,
        }
        return amount * token_prices.get(token.upper(), 1.0)

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
        wallet_key = wallet_address.lower()
        all_donations = self._donations.get(wallet_key, [])

        # 解析時間範圍
        time_delta = self._parse_time_range(time_range)
        cutoff_time = datetime.now() - time_delta

        # 過濾時間範圍內的捐款
        filtered_donations = [
            d for d in all_donations
            if d.timestamp >= cutoff_time
        ]

        # 按時間排序 (最新的在前)
        filtered_donations.sort(key=lambda x: x.timestamp, reverse=True)

        # 限制數量
        limited_donations = filtered_donations[:limit]

        # 計算總金額 (USD)
        total_usd = sum(
            self._calculate_usd_amount(d.amount, d.token)
            for d in limited_donations
        )

        return DonationHistoryResult(
            donations=limited_donations,
            total_amount_usd=round(total_usd, 2),
            total_count=len(limited_donations),
            time_range=time_range,
        )

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
        return self._tx_index.get(tx_hash.lower())
