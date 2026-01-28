"""
execute_donation 工具單元測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest

from gaia_link.tools.execute_donation import ExecuteDonationTool


class TestExecuteDonationTool:
    """execute_donation 工具測試"""

    @pytest.fixture
    def tool(self):
        """建立工具實例"""
        return ExecuteDonationTool()

    def test_tool_has_correct_name(self, tool):
        """工具應有正確的名稱"""
        assert tool.name == "execute_donation"

    def test_tool_has_description(self, tool):
        """工具應有描述"""
        assert len(tool.description) > 0
        assert "donation" in tool.description.lower()

    def test_tool_has_required_parameters(self, tool):
        """工具應有必要的參數定義"""
        props = tool.parameters["properties"]
        assert "amount" in props
        assert "token" in props
        assert "recipient_address" in props
        assert set(tool.parameters["required"]) == {"amount", "token", "recipient_address"}

    def test_tool_supports_multiple_tokens(self, tool):
        """工具應支援多種代幣"""
        token_enum = tool.parameters["properties"]["token"]["enum"]
        assert "USDC" in token_enum
        assert "USDT" in token_enum
        assert "ETH" in token_enum
        assert "DAI" in token_enum

    @pytest.mark.asyncio
    async def test_execute_successful_donation(self, tool):
        """成功的捐款應返回正確的結構"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert "success" in result
        assert "transaction_id" in result
        assert "status" in result
        assert "details" in result

        if result["success"]:
            assert result["transaction_id"] is not None
            assert result["status"] == "confirmed"
            assert result["details"]["amount_sent"] == 100.0
            assert result["details"]["token"] == "USDC"
            assert "gas_fee" in result["details"]
            assert "total_cost_usd" in result["details"]
            assert "explorer_url" in result

    @pytest.mark.asyncio
    async def test_execute_returns_transaction_details(self, tool):
        """應返回完整的交易詳情"""
        result = await tool.execute(
            amount=50.0,
            token="ETH",
            recipient_address="0xabcdef1234567890abcdef1234567890abcdef12"
        )

        if result["success"]:
            details = result["details"]
            assert details["amount_sent"] == 50.0
            assert details["token"] == "ETH"
            assert details["gas_fee"] >= 0
            assert details["total_cost_usd"] > 0

    @pytest.mark.asyncio
    async def test_execute_calculates_gas_fee(self, tool):
        """應計算 Gas 費用"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        if result["success"]:
            assert result["details"]["gas_fee"] > 0
            # 總成本應大於等於捐款金額（因為有 Gas 費）
            assert result["details"]["total_cost_usd"] >= result["details"]["amount_sent"]

    @pytest.mark.asyncio
    async def test_execute_invalid_amount_raises_error(self, tool):
        """無效金額應拋出錯誤或返回失敗"""
        result = await tool.execute(
            amount=-100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        # 負數金額應該失敗
        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_execute_zero_amount_raises_error(self, tool):
        """零金額應拋出錯誤或返回失敗"""
        result = await tool.execute(
            amount=0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_execute_invalid_token_raises_error(self, tool):
        """無效代幣應拋出錯誤或返回失敗"""
        result = await tool.execute(
            amount=100.0,
            token="INVALID_TOKEN",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_execute_invalid_address_raises_error(self, tool):
        """無效地址應拋出錯誤或返回失敗"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="invalid_address"
        )

        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_execute_returns_explorer_url(self, tool):
        """成功交易應返回區塊鏈瀏覽器連結"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        if result["success"]:
            assert result["explorer_url"] is not None
            assert "etherscan" in result["explorer_url"].lower() or "http" in result["explorer_url"]

    @pytest.mark.asyncio
    async def test_execute_different_tokens(self, tool):
        """應支援不同代幣類型"""
        tokens = ["USDC", "USDT", "ETH", "DAI"]
        address = "0x1234567890abcdef1234567890abcdef12345678"

        for token in tokens:
            result = await tool.execute(
                amount=10.0,
                token=token,
                recipient_address=address
            )

            if result["success"]:
                assert result["details"]["token"] == token

    def test_tool_to_param_format(self, tool):
        """to_param 應返回正確的函數調用格式"""
        param = tool.to_param()

        assert param["type"] == "function"
        assert param["function"]["name"] == "execute_donation"
