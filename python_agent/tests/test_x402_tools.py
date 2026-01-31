"""
X402 支付工具測試

測試 X402PaymentTool 的功能。
"""

import pytest
from decimal import Decimal

from gaia_link.services.x402 import (
    reset_x402_service,
    set_x402_service,
    X402Config,
)
from gaia_link.services.x402.mock_x402 import MockX402Service


@pytest.fixture(autouse=True)
def reset_global_services():
    """每個測試前重置全局服務"""
    reset_x402_service()
    yield
    reset_x402_service()


@pytest.fixture
def x402_service():
    """創建 X402 服務"""
    config = X402Config(
        private_key="0x" + "a" * 64,
        pay_to="0xReceiver",
        resource="https://example.com/api",
    )
    service = MockX402Service(config=config)
    set_x402_service(service)
    return service


class TestX402PaymentTool:
    """X402PaymentTool 測試"""

    @pytest.mark.asyncio
    async def test_build_payment_header_success(self, x402_service):
        """成功構建支付表頭"""
        from gaia_link.tools.x402_payment import X402PaymentTool

        tool = X402PaymentTool()
        result = await tool.execute(
            resource="https://example.com/api",
            amount_usdc=0.01,
        )

        assert result["success"] is True
        assert "payment_header" in result
        assert result["payment_header"] != ""
        assert "amount_atomic" in result
        assert result["amount_atomic"] == 10000

    @pytest.mark.asyncio
    async def test_build_payment_header_with_memo(self, x402_service):
        """應支援添加備註"""
        from gaia_link.tools.x402_payment import X402PaymentTool

        tool = X402PaymentTool()
        result = await tool.execute(
            resource="https://example.com/api",
            amount_usdc=0.05,
            memo="Donation for crisis relief",
        )

        assert result["success"] is True
        assert "requirements" in result

    @pytest.mark.asyncio
    async def test_build_payment_header_amount_atomic(self, x402_service):
        """應支援原子單位金額"""
        from gaia_link.tools.x402_payment import X402PaymentTool

        tool = X402PaymentTool()
        result = await tool.execute(
            resource="https://example.com/api",
            amount_atomic=25000,  # 0.025 USDC
        )

        assert result["success"] is True
        assert result["amount_atomic"] == 25000

    @pytest.mark.asyncio
    async def test_build_payment_header_with_max_value(self, x402_service):
        """應遵守最大金額限制"""
        from gaia_link.tools.x402_payment import X402PaymentTool

        tool = X402PaymentTool()
        result = await tool.execute(
            resource="https://example.com/api",
            amount_usdc=0.05,
            max_value=10000,  # 低於請求金額
        )

        assert result["success"] is False
        assert "error" in result
        assert "exceed" in result["error"].lower() or "max" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_missing_resource(self, x402_service):
        """缺少資源 URL 應失敗"""
        from gaia_link.tools.x402_payment import X402PaymentTool

        tool = X402PaymentTool()
        result = await tool.execute(
            resource="",  # 空字串
            amount_usdc=0.01,
        )

        assert result["success"] is False
        assert "error" in result


class TestX402VerifyPaymentTool:
    """X402VerifyPaymentTool 測試"""

    @pytest.mark.asyncio
    async def test_verify_valid_payment(self, x402_service):
        """驗證有效的支付表頭"""
        from gaia_link.tools.x402_payment import X402PaymentTool, X402VerifyPaymentTool

        # 先構建支付表頭
        payment_tool = X402PaymentTool()
        payment_result = await payment_tool.execute(
            resource="https://example.com/api",
            amount_usdc=0.01,
        )
        payment_header = payment_result["payment_header"]

        # 驗證
        verify_tool = X402VerifyPaymentTool()
        result = await verify_tool.execute(payment_header=payment_header)

        assert result["success"] is True
        assert result["is_valid"] is True
        assert "payer" in result

    @pytest.mark.asyncio
    async def test_verify_invalid_payment(self, x402_service):
        """驗證無效的支付表頭"""
        from gaia_link.tools.x402_payment import X402VerifyPaymentTool

        verify_tool = X402VerifyPaymentTool()
        result = await verify_tool.execute(payment_header="invalid-header")

        assert result["success"] is True  # 工具執行成功
        assert result["is_valid"] is False  # 但驗證失敗
        assert "invalid_reason" in result


class TestX402SettlePaymentTool:
    """X402SettlePaymentTool 測試"""

    @pytest.mark.asyncio
    async def test_settle_valid_payment(self, x402_service):
        """結算有效的支付"""
        from gaia_link.tools.x402_payment import X402PaymentTool, X402SettlePaymentTool

        # 先構建支付表頭
        payment_tool = X402PaymentTool()
        payment_result = await payment_tool.execute(
            resource="https://example.com/api",
            amount_usdc=0.01,
        )
        payment_header = payment_result["payment_header"]

        # 結算
        settle_tool = X402SettlePaymentTool()
        result = await settle_tool.execute(payment_header=payment_header)

        assert result["success"] is True
        assert result["settled"] is True
        assert "transaction" in result
        assert result["transaction"].startswith("0x")

    @pytest.mark.asyncio
    async def test_settle_invalid_payment(self, x402_service):
        """結算無效的支付應失敗"""
        from gaia_link.tools.x402_payment import X402SettlePaymentTool

        settle_tool = X402SettlePaymentTool()
        result = await settle_tool.execute(payment_header="invalid-header")

        assert result["success"] is True  # 工具執行成功
        assert result["settled"] is False  # 但結算失敗
        assert "error_reason" in result


class TestX402DecodeReceiptTool:
    """X402DecodeReceiptTool 測試"""

    @pytest.mark.asyncio
    async def test_decode_valid_receipt(self, x402_service):
        """解碼有效的支付收據"""
        import base64
        import json

        from gaia_link.tools.x402_payment import X402DecodeReceiptTool

        receipt_data = {
            "success": True,
            "transaction": "0xabc123",
            "network": "base-sepolia",
            "payer": "0xPayer",
        }
        receipt_header = base64.b64encode(json.dumps(receipt_data).encode()).decode()

        decode_tool = X402DecodeReceiptTool()
        result = await decode_tool.execute(response_header=receipt_header)

        assert result["success"] is True
        assert result["receipt"]["success"] is True
        assert result["receipt"]["transaction"] == "0xabc123"

    @pytest.mark.asyncio
    async def test_decode_invalid_receipt(self, x402_service):
        """解碼無效的支付收據"""
        from gaia_link.tools.x402_payment import X402DecodeReceiptTool

        decode_tool = X402DecodeReceiptTool()
        result = await decode_tool.execute(response_header="invalid-base64")

        assert result["success"] is True  # 工具執行成功
        assert result["receipt"]["success"] is False  # 但收據解析失敗
