"""
服務層單元測試

測試 BlockchainService 和 MockBlockchainService
"""

import pytest

from gaia_link.services.base import BlockchainService, TransactionResult
from gaia_link.services.mock_blockchain import (
    MockBlockchainService,
    SUPPORTED_TOKENS,
    TOKEN_USD_RATES,
    MOCK_GAS_FEE,
)


class TestTransactionResult:
    """TransactionResult 數據類測試"""

    def test_successful_result(self):
        """成功的交易結果"""
        result = TransactionResult(
            success=True,
            transaction_id="0x123",
            status="confirmed",
            gas_fee=0.003,
            gas_fee_usd=7.5,
            explorer_url="https://etherscan.io/tx/0x123",
        )
        assert result.success is True
        assert result.transaction_id == "0x123"
        assert result.status == "confirmed"
        assert result.error is None

    def test_failed_result(self):
        """失敗的交易結果"""
        result = TransactionResult(
            success=False,
            status="failed",
            error="Insufficient funds",
        )
        assert result.success is False
        assert result.transaction_id is None
        assert result.error == "Insufficient funds"

    def test_to_dict(self):
        """to_dict 應返回正確的字典格式"""
        result = TransactionResult(
            success=True,
            transaction_id="0xabc",
            status="confirmed",
            gas_fee=0.002,
            gas_fee_usd=5.0,
            explorer_url="https://etherscan.io/tx/0xabc",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["transaction_id"] == "0xabc"
        assert d["status"] == "confirmed"
        assert d["gas_fee"] == 0.002
        assert d["gas_fee_usd"] == 5.0
        assert d["explorer_url"] == "https://etherscan.io/tx/0xabc"
        assert d["error"] is None


class TestMockBlockchainService:
    """MockBlockchainService 測試"""

    @pytest.fixture
    def service(self):
        """建立服務實例"""
        return MockBlockchainService()

    def test_network_name(self, service):
        """應返回 mock 網絡名稱"""
        assert service.network_name == "mock"

    def test_chain_id(self, service):
        """Mock 網絡 chain_id 應為 0"""
        assert service.chain_id == 0

    def test_is_valid_address_valid(self, service):
        """應驗證有效的以太坊地址"""
        valid_address = "0x1234567890abcdef1234567890abcdef12345678"
        assert service.is_valid_address(valid_address) is True

    def test_is_valid_address_invalid_format(self, service):
        """應拒絕無效格式的地址"""
        assert service.is_valid_address("invalid") is False
        assert service.is_valid_address("0x123") is False
        assert service.is_valid_address("") is False
        assert service.is_valid_address(None) is False

    def test_is_valid_address_invalid_hex(self, service):
        """應拒絕包含非十六進位字符的地址"""
        invalid_address = "0x123456789GHIJKL1234567890abcdef12345678"
        assert service.is_valid_address(invalid_address) is False

    @pytest.mark.asyncio
    async def test_send_transaction_success(self, service):
        """成功的交易應返回正確結果"""
        result = await service.send_transaction(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678",
        )
        assert result.success is True
        assert result.transaction_id is not None
        assert result.transaction_id.startswith("0x")
        assert result.status == "confirmed"
        assert result.gas_fee == MOCK_GAS_FEE
        assert result.explorer_url is not None

    @pytest.mark.asyncio
    async def test_send_transaction_invalid_amount(self, service):
        """無效金額應返回失敗"""
        result = await service.send_transaction(
            amount=-100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678",
        )
        assert result.success is False
        assert "positive" in result.error.lower()

    @pytest.mark.asyncio
    async def test_send_transaction_zero_amount(self, service):
        """零金額應返回失敗"""
        result = await service.send_transaction(
            amount=0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678",
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_send_transaction_unsupported_token(self, service):
        """不支援的代幣應返回失敗"""
        result = await service.send_transaction(
            amount=100.0,
            token="INVALID",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678",
        )
        assert result.success is False
        assert "unsupported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_send_transaction_invalid_address(self, service):
        """無效地址應返回失敗"""
        result = await service.send_transaction(
            amount=100.0,
            token="USDC",
            recipient_address="invalid_address",
        )
        assert result.success is False
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_send_transaction_all_supported_tokens(self, service):
        """應支援所有列出的代幣"""
        address = "0x1234567890abcdef1234567890abcdef12345678"
        for token in SUPPORTED_TOKENS:
            result = await service.send_transaction(
                amount=10.0,
                token=token,
                recipient_address=address,
            )
            assert result.success is True, f"Token {token} should be supported"

    def test_get_explorer_url(self, service):
        """應返回正確的區塊鏈瀏覽器 URL"""
        tx_id = "0xabc123"
        url = service.get_explorer_url(tx_id)
        assert "etherscan.io" in url
        assert tx_id in url

    @pytest.mark.asyncio
    async def test_get_balance_valid_address(self, service):
        """應返回模擬餘額"""
        address = "0x1234567890abcdef1234567890abcdef12345678"
        balance = await service.get_balance(address, "ETH")
        assert balance > 0

    @pytest.mark.asyncio
    async def test_get_balance_invalid_address(self, service):
        """無效地址應返回 0 餘額"""
        balance = await service.get_balance("invalid", "ETH")
        assert balance == 0.0

    @pytest.mark.asyncio
    async def test_estimate_gas(self, service):
        """應返回固定的 Gas 費用估算"""
        gas = await service.estimate_gas(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678",
        )
        assert gas == MOCK_GAS_FEE

    def test_get_token_usd_rate(self, service):
        """應返回正確的代幣匯率"""
        assert service.get_token_usd_rate("USDC") == 1.0
        assert service.get_token_usd_rate("ETH") == 2500.0
        assert service.get_token_usd_rate("UNKNOWN") == 1.0

    def test_get_supported_tokens(self, service):
        """應返回支援的代幣列表副本"""
        tokens = service.get_supported_tokens()
        assert tokens == SUPPORTED_TOKENS
        # 確保返回的是副本，不是原始列表
        tokens.append("TEST")
        assert "TEST" not in service.get_supported_tokens()


class TestBlockchainServiceInterface:
    """BlockchainService 抽象介面測試"""

    def test_mock_service_implements_interface(self):
        """MockBlockchainService 應實現 BlockchainService 介面"""
        service = MockBlockchainService()
        assert isinstance(service, BlockchainService)

    def test_interface_has_required_methods(self):
        """BlockchainService 應定義必要的抽象方法"""
        # 檢查抽象方法
        abstract_methods = BlockchainService.__abstractmethods__
        assert "send_transaction" in abstract_methods
        assert "get_explorer_url" in abstract_methods
        assert "get_balance" in abstract_methods
        assert "estimate_gas" in abstract_methods

    def test_interface_has_required_properties(self):
        """BlockchainService 應定義必要的屬性"""
        abstract_methods = BlockchainService.__abstractmethods__
        assert "network_name" in abstract_methods
        assert "chain_id" in abstract_methods
