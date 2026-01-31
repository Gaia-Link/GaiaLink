"""
execute_donation 工具單元測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest

from gaia_link.tools.execute_donation import (
    ExecuteDonationTool,
    encode_erc20_transfer,
    SEPOLIA_TOKEN_CONTRACTS,
    ERC20_TRANSFER_SELECTOR,
)


class TestERC20Encoding:
    """測試 ERC20 calldata 編碼"""

    def test_encode_erc20_transfer_format(self):
        """calldata 應以 0xa9059cbb 開頭 (transfer selector)"""
        calldata = encode_erc20_transfer(
            recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=6
        )
        assert calldata.startswith(ERC20_TRANSFER_SELECTOR)

    def test_encode_erc20_transfer_length(self):
        """calldata 應為 138 字元 (0x + 8 selector + 64 address + 64 amount)"""
        calldata = encode_erc20_transfer(
            recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=6
        )
        assert len(calldata) == 138

    def test_encode_erc20_transfer_amount_usdc(self):
        """100 USDC (6 decimals) = 100000000 = 0x5F5E100"""
        calldata = encode_erc20_transfer(
            recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=6
        )
        # Amount should be in the last 64 chars
        amount_hex = calldata[-64:]
        # 100 * 10^6 = 100000000 = 0x5F5E100
        assert "5f5e100" in amount_hex.lower()

    def test_encode_erc20_transfer_amount_dai(self):
        """100 DAI (18 decimals) 應正確編碼"""
        calldata = encode_erc20_transfer(
            recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=18
        )
        # 100 * 10^18 = 100000000000000000000 = 0x56BC75E2D63100000
        amount_hex = calldata[-64:]
        assert "56bc75e2d63100000" in amount_hex.lower()

    def test_encode_erc20_transfer_address_padding(self):
        """地址應左補零到 64 字元"""
        calldata = encode_erc20_transfer(
            recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=6
        )
        # Address is chars 10-74 (after 0xa9059cbb)
        address_part = calldata[10:74]
        # Should be padded with leading zeros
        assert address_part.startswith("000000000000000000000000")
        # And contain the actual address
        assert "742d35cc6634c0532925a3b844bc9e7595f5be91" in address_part.lower()

    def test_encode_erc20_transfer_without_0x_prefix(self):
        """地址不含 0x 前綴也應正常工作"""
        calldata1 = encode_erc20_transfer(
            recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=6
        )
        calldata2 = encode_erc20_transfer(
            recipient="742d35Cc6634C0532925a3b844Bc9e7595f5bE91",
            amount=100.0,
            decimals=6
        )
        assert calldata1 == calldata2


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
        assert set(tool.parameters["required"]) == {"amount", "token"}

    def test_tool_supports_multiple_tokens(self, tool):
        """工具應支援多種代幣"""
        token_enum = tool.parameters["properties"]["token"]["enum"]
        assert "USDC" in token_enum
        assert "USDT" in token_enum
        assert "ETH" in token_enum
        assert "DAI" in token_enum

    @pytest.mark.asyncio
    async def test_execute_successful_donation(self, tool):
        """成功的捐款應返回正確的結構 (ready_to_sign)"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is True
        assert result["status"] == "ready_to_sign"
        assert "transaction_payload" in result
        assert "details" in result
        assert "message" in result

        # Verify transaction payload structure
        payload = result["transaction_payload"]
        assert payload["chainId"] == 11155111  # Sepolia
        assert "to" in payload
        assert "value" in payload
        assert "data" in payload

    @pytest.mark.asyncio
    async def test_execute_returns_erc20_calldata(self, tool):
        """USDC 捐款應返回 ERC20 transfer calldata"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is True
        payload = result["transaction_payload"]

        # ERC20 transfer: to should be the token contract
        assert payload["to"] == SEPOLIA_TOKEN_CONTRACTS["USDC"]
        assert payload["value"] == "0"
        assert payload["data"].startswith(ERC20_TRANSFER_SELECTOR)

    @pytest.mark.asyncio
    async def test_execute_eth_donation(self, tool):
        """ETH 捐款應返回原生轉帳 (無 calldata)"""
        result = await tool.execute(
            amount=0.1,
            token="ETH",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is True
        payload = result["transaction_payload"]

        # ETH transfer: to should be the recipient, data should be 0x
        assert payload["to"] == "0x1234567890abcdef1234567890abcdef12345678"
        assert payload["data"] == "0x"
        # Value should be in Wei (0.1 ETH = 100000000000000000 Wei)
        assert int(payload["value"]) == 100000000000000000

    @pytest.mark.asyncio
    async def test_execute_returns_gas_estimate(self, tool):
        """應返回 Gas 估算"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is True
        assert result["details"]["estimated_gas"] > 0

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
    async def test_execute_returns_intent_summary(self, tool):
        """應返回交易意圖摘要"""
        result = await tool.execute(
            amount=100.0,
            token="USDC",
            recipient_address="0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result["success"] is True
        assert "intent_summary" in result["transaction_payload"]
        assert "100" in result["transaction_payload"]["intent_summary"]
        assert "USDC" in result["transaction_payload"]["intent_summary"]

    @pytest.mark.asyncio
    async def test_execute_different_tokens(self, tool):
        """應支援不同代幣類型"""
        tokens = ["USDC", "USDT", "DAI"]
        address = "0x1234567890abcdef1234567890abcdef12345678"

        for token in tokens:
            result = await tool.execute(
                amount=10.0,
                token=token,
                recipient_address=address
            )

            assert result["success"] is True
            assert result["details"]["token"] == token
            # ERC20 tokens should have calldata
            assert result["transaction_payload"]["data"].startswith(ERC20_TRANSFER_SELECTOR)

    def test_tool_to_param_format(self, tool):
        """to_param 應返回正確的函數調用格式"""
        param = tool.to_param()

        assert param["type"] == "function"
        assert param["function"]["name"] == "execute_donation"
