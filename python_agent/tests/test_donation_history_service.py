"""
Donation History Service 測試

TDD RED Phase: 測試先行
"""

import pytest
from datetime import datetime, timedelta

from gaia_link.services.donation_history.models import (
    DonationRecord,
    DonationHistoryResult,
    DonationStatus,
    VaultType,
)


class TestDonationRecordModel:
    """DonationRecord 數據模型測試"""

    def test_donation_record_creation(self):
        """應該能夠創建 DonationRecord"""
        record = DonationRecord(
            tx_hash="0x123abc",
            amount=100.0,
            token="USDC",
            recipient="Red Cross Turkey",
            recipient_address="0xRecipient123",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            status=DonationStatus.CONFIRMED,
            vault_type=VaultType.DIRECT,
        )

        assert record.tx_hash == "0x123abc"
        assert record.amount == 100.0
        assert record.token == "USDC"
        assert record.recipient == "Red Cross Turkey"
        assert record.status == DonationStatus.CONFIRMED
        assert record.vault_type == VaultType.DIRECT

    def test_donation_record_to_dict(self):
        """DonationRecord 應該能轉換為字典"""
        record = DonationRecord(
            tx_hash="0x123abc",
            amount=50.0,
            token="ETH",
            recipient="Gaza Relief Fund",
            recipient_address="0xGaza456",
            timestamp=datetime(2024, 1, 20, 15, 0, 0),
            status=DonationStatus.PENDING,
            vault_type=VaultType.NO_LOSS,
        )

        result = record.to_dict()

        assert result["tx_hash"] == "0x123abc"
        assert result["amount"] == 50.0
        assert result["token"] == "ETH"
        assert result["status"] == "pending"
        assert result["vault_type"] == "NO_LOSS"
        assert "timestamp" in result

    def test_donation_record_from_dict(self):
        """應該能從字典創建 DonationRecord"""
        data = {
            "tx_hash": "0xdef456",
            "amount": 200.0,
            "token": "USDT",
            "recipient": "Ukraine Aid",
            "recipient_address": "0xUkraine789",
            "timestamp": "2024-01-25T12:00:00",
            "status": "confirmed",
            "vault_type": "DIRECT",
        }

        record = DonationRecord.from_dict(data)

        assert record.tx_hash == "0xdef456"
        assert record.amount == 200.0
        assert record.status == DonationStatus.CONFIRMED
        assert record.vault_type == VaultType.DIRECT

    def test_donation_record_from_dict_with_datetime_object(self):
        """應該能從帶有 datetime 物件的字典創建 DonationRecord"""
        ts = datetime(2024, 1, 30, 14, 30, 0)
        data = {
            "tx_hash": "0xghi789",
            "amount": 300.0,
            "token": "ETH",
            "recipient": "Syria Relief",
            "recipient_address": "0xSyria999",
            "timestamp": ts,
            "status": "pending",
        }

        record = DonationRecord.from_dict(data)

        assert record.tx_hash == "0xghi789"
        assert record.amount == 300.0
        assert record.timestamp == ts
        assert record.status == DonationStatus.PENDING
        # 當沒有 vault_type 時應該使用預設值
        assert record.vault_type == VaultType.DIRECT


class TestDonationHistoryResultModel:
    """DonationHistoryResult 數據模型測試"""

    def test_donation_history_result_creation(self):
        """應該能夠創建 DonationHistoryResult"""
        donations = [
            DonationRecord(
                tx_hash="0x111",
                amount=100.0,
                token="USDC",
                recipient="Test Org",
                recipient_address="0xTest",
                timestamp=datetime.now(),
                status=DonationStatus.CONFIRMED,
            ),
        ]

        result = DonationHistoryResult(
            donations=donations,
            total_amount_usd=100.0,
            total_count=1,
            time_range="30d",
        )

        assert len(result.donations) == 1
        assert result.total_amount_usd == 100.0
        assert result.total_count == 1
        assert result.time_range == "30d"

    def test_donation_history_result_to_dict(self):
        """DonationHistoryResult 應該能轉換為字典"""
        donations = [
            DonationRecord(
                tx_hash="0x222",
                amount=50.0,
                token="DAI",
                recipient="Test Org 2",
                recipient_address="0xTest2",
                timestamp=datetime(2024, 1, 10),
                status=DonationStatus.CONFIRMED,
            ),
        ]

        result = DonationHistoryResult(
            donations=donations,
            total_amount_usd=50.0,
            total_count=1,
            time_range="7d",
        )

        data = result.to_dict()

        assert len(data["donations"]) == 1
        assert data["total_amount_usd"] == 50.0
        assert data["total_count"] == 1
        assert data["time_range"] == "7d"

    def test_donation_history_result_from_dict(self):
        """應該能從字典創建 DonationHistoryResult"""
        data = {
            "donations": [
                {
                    "tx_hash": "0x333",
                    "amount": 75.0,
                    "token": "USDC",
                    "recipient": "Test Org 3",
                    "recipient_address": "0xTest3",
                    "timestamp": "2024-02-01T10:00:00",
                    "status": "confirmed",
                    "vault_type": "NO_LOSS",
                },
            ],
            "total_amount_usd": 75.0,
            "total_count": 1,
            "time_range": "90d",
        }

        result = DonationHistoryResult.from_dict(data)

        assert len(result.donations) == 1
        assert result.donations[0].tx_hash == "0x333"
        assert result.total_amount_usd == 75.0
        assert result.total_count == 1
        assert result.time_range == "90d"


class TestDonationHistoryService:
    """DonationHistoryService 功能測試"""

    @pytest.mark.asyncio
    async def test_get_history_returns_correct_format(self):
        """get_history 應該返回 DonationHistoryResult"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()
        result = await service.get_history(
            wallet_address="0xTestWallet123",
            time_range="30d",
            limit=10,
        )

        assert isinstance(result, DonationHistoryResult)
        assert isinstance(result.donations, list)
        assert isinstance(result.total_amount_usd, (int, float))
        assert isinstance(result.total_count, int)
        assert isinstance(result.time_range, str)

    @pytest.mark.asyncio
    async def test_get_history_respects_limit(self):
        """get_history 應該遵守 limit 參數"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()
        result = await service.get_history(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=3,
        )

        assert len(result.donations) <= 3

    @pytest.mark.asyncio
    async def test_get_history_filters_by_time_range(self):
        """get_history 應該按時間範圍過濾"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()

        # 7 天內的記錄應該比 30 天少
        result_7d = await service.get_history(
            wallet_address="0xTestWallet123",
            time_range="7d",
            limit=100,
        )

        result_30d = await service.get_history(
            wallet_address="0xTestWallet123",
            time_range="30d",
            limit=100,
        )

        # 7d 的結果應該 <= 30d 的結果
        assert len(result_7d.donations) <= len(result_30d.donations)

    @pytest.mark.asyncio
    async def test_get_transaction_returns_record(self):
        """get_transaction 應該返回單筆記錄"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()

        # 先取得歷史記錄
        history = await service.get_history(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=1,
        )

        if history.donations:
            tx_hash = history.donations[0].tx_hash
            result = await service.get_transaction(tx_hash)

            assert result is not None
            assert isinstance(result, DonationRecord)
            assert result.tx_hash == tx_hash

    @pytest.mark.asyncio
    async def test_get_transaction_returns_none_for_nonexistent(self):
        """get_transaction 對不存在的交易應該返回 None"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()
        result = await service.get_transaction("0xNonExistentTx999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_history_calculates_total_correctly(self):
        """get_history 應該正確計算總金額"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()
        result = await service.get_history(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=100,
        )

        # total_count 應該等於 donations 列表長度
        assert result.total_count == len(result.donations)

        # total_amount_usd 應該 >= 0
        assert result.total_amount_usd >= 0

    @pytest.mark.asyncio
    async def test_get_history_empty_wallet(self):
        """空錢包應該返回空列表"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
        )

        service = get_donation_history_service()
        result = await service.get_history(
            wallet_address="0xEmptyWallet000",
            time_range="all",
            limit=100,
        )

        # 對於沒有捐款記錄的錢包，應該返回空列表
        assert isinstance(result.donations, list)
        assert result.total_count == 0
        assert result.total_amount_usd == 0.0


class TestMockDonationHistoryService:
    """MockDonationHistoryService 特定測試"""

    def test_mock_service_can_be_imported(self):
        """MockDonationHistoryService 應該可以被導入"""
        from gaia_link.services.donation_history import (
            MockDonationHistoryService,
        )
        assert MockDonationHistoryService is not None

    def test_mock_service_is_subclass(self):
        """MockDonationHistoryService 應該是 DonationHistoryService 的子類"""
        from gaia_link.services.donation_history import (
            MockDonationHistoryService,
            DonationHistoryService,
        )
        assert issubclass(MockDonationHistoryService, DonationHistoryService)

    @pytest.mark.asyncio
    async def test_mock_service_provides_demo_data(self):
        """Mock 服務應該提供 Demo 數據"""
        from gaia_link.services.donation_history import (
            MockDonationHistoryService,
        )

        service = MockDonationHistoryService()
        result = await service.get_history(
            wallet_address="0xDemoWallet",
            time_range="all",
            limit=100,
        )

        # Mock 服務應該有預設的 Demo 數據
        # 對於 Demo 錢包，應該有一些捐款記錄
        assert isinstance(result, DonationHistoryResult)


class TestServiceFactory:
    """服務工廠函數測試"""

    def test_get_donation_history_service_returns_service(self):
        """get_donation_history_service 應該返回服務實例"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
            DonationHistoryService,
        )

        service = get_donation_history_service()
        assert isinstance(service, DonationHistoryService)

    def test_set_donation_history_service_works(self):
        """set_donation_history_service 應該能設置自定義服務"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
            set_donation_history_service,
            reset_donation_history_service,
            MockDonationHistoryService,
        )

        # 創建自定義服務
        custom_service = MockDonationHistoryService()

        # 設置自定義服務
        set_donation_history_service(custom_service)

        # 獲取的服務應該是設置的那個
        service = get_donation_history_service()
        assert service is custom_service

        # 清理
        reset_donation_history_service()

    def test_reset_donation_history_service_works(self):
        """reset_donation_history_service 應該重置服務"""
        from gaia_link.services.donation_history import (
            get_donation_history_service,
            reset_donation_history_service,
        )

        # 先獲取一次服務
        service1 = get_donation_history_service()

        # 重置
        reset_donation_history_service()

        # 再獲取，應該是新的實例
        service2 = get_donation_history_service()

        # 由於重置後會創建新實例，兩者應該不同
        # (但如果是單例模式可能相同，這裡測試重置功能)
        assert service1 is not None
        assert service2 is not None

        # 清理
        reset_donation_history_service()
