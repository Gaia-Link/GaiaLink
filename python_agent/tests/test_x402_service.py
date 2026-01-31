"""
X402 支付服務測試

測試 Mock 實作的 HTTP 402 支付流程。
"""

import pytest
from decimal import Decimal
from datetime import datetime

from gaia_link.services.x402.models import (
    PaymentStatus,
    PaymentRequirements,
    PaymentRequest,
    PaymentHeader,
    VerifyResult,
    SettleResult,
    PaymentReceipt,
    X402Config,
)
from gaia_link.services.x402.base import X402Service


class TestX402Models:
    """X402 數據模型測試"""

    def test_payment_request_amount_atomic_from_usdc(self):
        """PaymentRequest 應正確計算原子單位"""
        request = PaymentRequest(
            resource="https://example.com/api",
            amount_usdc=Decimal("0.01"),
        )
        assert request.get_amount_atomic(decimals=6) == 10000

    def test_payment_request_amount_atomic_priority(self):
        """原子單位應優先於 USDC 金額"""
        request = PaymentRequest(
            resource="https://example.com/api",
            amount_usdc=Decimal("0.01"),
            amount_atomic=50000,  # 優先使用
        )
        assert request.get_amount_atomic(decimals=6) == 50000

    def test_payment_request_default_network(self):
        """默認網路應為 base-sepolia"""
        request = PaymentRequest(resource="https://example.com/api")
        assert request.network == "base-sepolia"

    def test_x402_config_max_amount_atomic(self):
        """X402Config 應正確計算最大原子單位"""
        config = X402Config(
            max_amount_usdc=Decimal("0.10"),
            asset_decimals=6,
        )
        assert config.max_amount_atomic == 100000

    def test_payment_status_enum(self):
        """PaymentStatus 枚舉值應正確"""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.VERIFIED.value == "verified"
        assert PaymentStatus.SETTLED.value == "settled"
        assert PaymentStatus.FAILED.value == "failed"


class TestMockX402ServiceBasic:
    """MockX402Service 基本功能測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        return MockX402Service()

    def test_service_is_x402_service(self, x402_service):
        """服務應該是 X402Service 的實例"""
        assert isinstance(x402_service, X402Service)

    def test_get_config(self, x402_service):
        """應返回有效配置"""
        config = x402_service.get_config()
        assert isinstance(config, X402Config)
        assert config.default_network == "base-sepolia"
        assert config.asset_decimals == 6

    def test_get_config_with_custom_values(self):
        """應支援自定義配置"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        custom_config = X402Config(
            default_network="ethereum-mainnet",
            max_amount_usdc=Decimal("1.00"),
        )
        service = MockX402Service(config=custom_config)
        config = service.get_config()
        assert config.default_network == "ethereum-mainnet"
        assert config.max_amount_usdc == Decimal("1.00")


class TestMockX402ServicePaymentRequirements:
    """MockX402Service 支付要求測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        return MockX402Service()

    def test_build_payment_requirements_basic(self, x402_service):
        """應構建基本支付要求"""
        requirements = x402_service.build_payment_requirements()

        assert isinstance(requirements, PaymentRequirements)
        assert requirements.scheme == "exact"
        assert requirements.network == "base-sepolia"

    def test_build_payment_requirements_with_request(self, x402_service):
        """應根據請求構建支付要求"""
        request = PaymentRequest(
            resource="https://example.com/api",
            amount_usdc=Decimal("0.05"),
            memo="Test payment",
        )
        requirements = x402_service.build_payment_requirements(request=request)

        assert requirements.resource == "https://example.com/api"
        assert requirements.max_amount_required == "50000"  # 0.05 * 10^6
        assert "Test payment" in requirements.description or requirements.extra.get(
            "memo"
        ) == "Test payment"

    def test_build_payment_requirements_amount_atomic(self, x402_service):
        """應正確處理原子單位金額"""
        request = PaymentRequest(
            resource="https://example.com/api",
            amount_atomic=25000,  # 0.025 USDC
        )
        requirements = x402_service.build_payment_requirements(request=request)

        assert requirements.max_amount_required == "25000"


class TestMockX402ServicePaymentHeader:
    """MockX402Service 支付表頭測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        config = X402Config(
            private_key="0x" + "a" * 64,  # 測試用私鑰
            pay_to="0xReceiver",
        )
        return MockX402Service(config=config)

    def test_build_payment_header_basic(self, x402_service):
        """應構建有效的支付表頭"""
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.01"),
            )
        )
        header = x402_service.build_payment_header(requirements)

        assert isinstance(header, PaymentHeader)
        assert header.header_value != ""
        assert header.amount_atomic == 10000

    def test_build_payment_header_with_max_value(self, x402_service):
        """應遵守最大金額限制"""
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.05"),
            )
        )

        # 設置較低的 max_value
        with pytest.raises(ValueError) as exc_info:
            x402_service.build_payment_header(requirements, max_value=10000)

        assert "exceed" in str(exc_info.value).lower() or "max" in str(
            exc_info.value
        ).lower()

    def test_build_payment_header_sets_payer(self, x402_service):
        """應設置支付者地址"""
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.01"),
            )
        )
        header = x402_service.build_payment_header(requirements)

        assert header.payer != ""


class TestMockX402ServiceVerification:
    """MockX402Service 驗證測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        return MockX402Service(
            config=X402Config(
                private_key="0x" + "a" * 64,
                pay_to="0xReceiver",
            )
        )

    @pytest.mark.asyncio
    async def test_verify_payment_valid(self, x402_service):
        """應驗證有效的支付表頭"""
        # 構建支付
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.01"),
            )
        )
        header = x402_service.build_payment_header(requirements)

        # 驗證
        result = await x402_service.verify_payment(header.header_value, requirements)

        assert isinstance(result, VerifyResult)
        assert result.is_valid is True
        assert result.payer is not None

    @pytest.mark.asyncio
    async def test_verify_payment_invalid_header(self, x402_service):
        """應拒絕無效的支付表頭"""
        result = await x402_service.verify_payment("invalid-header-value")

        assert result.is_valid is False
        assert result.invalid_reason is not None


class TestMockX402ServiceSettlement:
    """MockX402Service 結算測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        return MockX402Service(
            config=X402Config(
                private_key="0x" + "a" * 64,
                pay_to="0xReceiver",
            )
        )

    @pytest.mark.asyncio
    async def test_settle_payment_success(self, x402_service):
        """應成功結算有效支付"""
        # 構建支付
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.01"),
            )
        )
        header = x402_service.build_payment_header(requirements)

        # 結算
        result = await x402_service.settle_payment(header.header_value, requirements)

        assert isinstance(result, SettleResult)
        assert result.success is True
        assert result.transaction is not None
        assert result.network == "base-sepolia"

    @pytest.mark.asyncio
    async def test_settle_payment_invalid_header(self, x402_service):
        """應拒絕結算無效支付"""
        result = await x402_service.settle_payment("invalid-header-value")

        assert result.success is False
        assert result.error_reason is not None


class TestMockX402ServiceVerifyAndSettle:
    """MockX402Service 驗證並結算測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        return MockX402Service(
            config=X402Config(
                private_key="0x" + "a" * 64,
                pay_to="0xReceiver",
            )
        )

    @pytest.mark.asyncio
    async def test_verify_and_settle_full_flow(self, x402_service):
        """應完成完整的驗證和結算流程"""
        # 構建支付
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.01"),
            )
        )
        header = x402_service.build_payment_header(requirements)

        # 驗證並結算
        verify_result, settle_result = await x402_service.verify_and_settle(
            header.header_value, requirements
        )

        assert verify_result.is_valid is True
        assert settle_result is not None
        assert settle_result.success is True

    @pytest.mark.asyncio
    async def test_verify_and_settle_verify_only(self, x402_service):
        """應支援僅驗證模式"""
        # 構建支付
        requirements = x402_service.build_payment_requirements(
            PaymentRequest(
                resource="https://example.com/api",
                amount_usdc=Decimal("0.01"),
            )
        )
        header = x402_service.build_payment_header(requirements)

        # 僅驗證
        verify_result, settle_result = await x402_service.verify_and_settle(
            header.header_value, requirements, settle=False
        )

        assert verify_result.is_valid is True
        assert settle_result is None


class TestMockX402ServicePaymentReceipt:
    """MockX402Service 支付收據測試"""

    @pytest.fixture
    def x402_service(self):
        """創建 X402 服務實例"""
        from gaia_link.services.x402.mock_x402 import MockX402Service

        return MockX402Service()

    def test_decode_payment_response_valid(self, x402_service):
        """應解碼有效的支付響應"""
        import base64
        import json

        response_data = {
            "success": True,
            "transaction": "0xabc123",
            "network": "base-sepolia",
            "payer": "0xPayer",
        }
        response_header = base64.b64encode(
            json.dumps(response_data).encode()
        ).decode()

        receipt = x402_service.decode_payment_response(response_header)

        assert isinstance(receipt, PaymentReceipt)
        assert receipt.success is True
        assert receipt.transaction == "0xabc123"
        assert receipt.network == "base-sepolia"

    def test_decode_payment_response_invalid(self, x402_service):
        """應處理無效的支付響應"""
        receipt = x402_service.decode_payment_response("invalid-base64")

        assert receipt.success is False
        assert receipt.error_reason is not None


class TestX402ServiceFactory:
    """X402 服務工廠函數測試"""

    def test_get_x402_service_returns_mock_by_default(self):
        """默認應返回 Mock 服務"""
        from gaia_link.services.x402 import get_x402_service, reset_x402_service

        reset_x402_service()  # 清除快取
        service = get_x402_service()

        assert isinstance(service, X402Service)
        # 檢查是 MockX402Service
        assert service.__class__.__name__ == "MockX402Service"

    def test_set_x402_service(self):
        """應能設置自定義服務"""
        from gaia_link.services.x402 import (
            get_x402_service,
            set_x402_service,
            reset_x402_service,
        )
        from gaia_link.services.x402.mock_x402 import MockX402Service

        reset_x402_service()
        custom_service = MockX402Service(
            config=X402Config(default_network="custom-network")
        )
        set_x402_service(custom_service)

        service = get_x402_service()
        assert service.get_config().default_network == "custom-network"

        reset_x402_service()  # 清理

    def test_reset_x402_service(self):
        """應能重置服務實例"""
        from gaia_link.services.x402 import (
            get_x402_service,
            set_x402_service,
            reset_x402_service,
        )
        from gaia_link.services.x402.mock_x402 import MockX402Service

        # 設置自定義服務
        custom_service = MockX402Service(
            config=X402Config(default_network="custom-network")
        )
        set_x402_service(custom_service)

        # 重置
        reset_x402_service()

        # 應返回新的默認服務
        service = get_x402_service()
        assert service.get_config().default_network == "base-sepolia"

        reset_x402_service()  # 清理
