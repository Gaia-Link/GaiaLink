"""
MCP Donation History 工具測試

TDD RED Phase: 測試先行
"""

import pytest
from unittest.mock import MagicMock


class TestMCPDonationHistoryToolRegistration:
    """MCP Donation History 工具註冊測試"""

    def test_get_donation_history_tool_registered(self):
        """get_donation_history 工具應該被註冊"""
        from gaia_link.mcp_server import mcp

        tool_names = list(mcp._tool_manager._tools.keys())
        assert "get_donation_history" in tool_names

    def test_get_transaction_status_tool_registered(self):
        """get_transaction_status 工具應該被註冊"""
        from gaia_link.mcp_server import mcp

        tool_names = list(mcp._tool_manager._tools.keys())
        assert "get_transaction_status" in tool_names


class TestGetDonationHistoryTool:
    """get_donation_history 工具功能測試"""

    @pytest.mark.asyncio
    async def test_returns_success_true(self):
        """get_donation_history 應該返回 success: true"""
        from gaia_link.mcp_server import get_donation_history

        mock_ctx = MagicMock()

        result = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="30d",
            limit=10,
            ctx=mock_ctx,
        )

        assert isinstance(result, dict)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_returns_donations_list(self):
        """get_donation_history 應該返回捐款列表"""
        from gaia_link.mcp_server import get_donation_history

        mock_ctx = MagicMock()

        result = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="30d",
            limit=10,
            ctx=mock_ctx,
        )

        assert "donations" in result
        assert isinstance(result["donations"], list)

    @pytest.mark.asyncio
    async def test_returns_total_stats(self):
        """get_donation_history 應該返回統計數據"""
        from gaia_link.mcp_server import get_donation_history

        mock_ctx = MagicMock()

        result = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="30d",
            limit=10,
            ctx=mock_ctx,
        )

        assert "total_amount_usd" in result
        assert "total_count" in result
        assert "time_range" in result

    @pytest.mark.asyncio
    async def test_masks_wallet_address(self):
        """get_donation_history 應該部分遮蔽錢包地址"""
        from gaia_link.mcp_server import get_donation_history

        mock_ctx = MagicMock()

        result = await get_donation_history.fn(
            wallet_address="0x1234567890123456789012345678901234567890",
            time_range="30d",
            limit=10,
            ctx=mock_ctx,
        )

        # 返回結果中的錢包地址應該被部分遮蔽
        assert "wallet_address" in result
        wallet = result["wallet_address"]
        # 應該顯示開頭和結尾，中間遮蔽
        assert "..." in wallet or "****" in wallet or len(wallet) < 42

    @pytest.mark.asyncio
    async def test_default_parameters(self):
        """get_donation_history 應該有預設參數"""
        from gaia_link.mcp_server import get_donation_history

        mock_ctx = MagicMock()

        # 只提供必要參數
        result = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            ctx=mock_ctx,
        )

        assert result["success"] is True
        # 預設 time_range 應該是 30d
        assert result["time_range"] == "30d"

    @pytest.mark.asyncio
    async def test_invalid_time_range_handled(self):
        """無效的 time_range 應該被妥善處理"""
        from gaia_link.mcp_server import get_donation_history

        mock_ctx = MagicMock()

        # 使用無效的 time_range
        result = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="invalid",
            limit=10,
            ctx=mock_ctx,
        )

        # 應該返回錯誤或使用預設值
        assert isinstance(result, dict)
        # 如果返回錯誤
        if not result.get("success", True):
            assert "error" in result
        # 如果使用預設值
        else:
            assert result["success"] is True


class TestGetTransactionStatusTool:
    """get_transaction_status 工具功能測試"""

    @pytest.mark.asyncio
    async def test_returns_transaction_details(self):
        """get_transaction_status 應該返回交易詳情"""
        from gaia_link.mcp_server import (
            get_donation_history,
            get_transaction_status,
        )

        mock_ctx = MagicMock()

        # 先取得一筆交易
        history = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=1,
            ctx=mock_ctx,
        )

        if history.get("donations"):
            tx_hash = history["donations"][0]["tx_hash"]

            result = await get_transaction_status.fn(
                tx_hash=tx_hash,
                ctx=mock_ctx,
            )

            assert isinstance(result, dict)
            assert "success" in result

    @pytest.mark.asyncio
    async def test_returns_not_found_for_nonexistent(self):
        """不存在的交易應該返回 found: false"""
        from gaia_link.mcp_server import get_transaction_status

        mock_ctx = MagicMock()

        result = await get_transaction_status.fn(
            tx_hash="0xNonExistentTx999",
            ctx=mock_ctx,
        )

        assert isinstance(result, dict)
        assert result.get("found") is False or result.get("success") is False

    @pytest.mark.asyncio
    async def test_includes_explorer_url(self):
        """get_transaction_status 應該包含 explorer_url"""
        from gaia_link.mcp_server import (
            get_donation_history,
            get_transaction_status,
        )

        mock_ctx = MagicMock()

        # 先取得一筆交易
        history = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=1,
            ctx=mock_ctx,
        )

        if history.get("donations"):
            tx_hash = history["donations"][0]["tx_hash"]

            result = await get_transaction_status.fn(
                tx_hash=tx_hash,
                ctx=mock_ctx,
            )

            # 如果找到交易，應該包含 explorer_url
            if result.get("found", result.get("success")):
                assert "explorer_url" in result
                assert "etherscan" in result["explorer_url"].lower() or \
                       "sepolia" in result["explorer_url"].lower()

    @pytest.mark.asyncio
    async def test_returns_full_transaction_info(self):
        """get_transaction_status 應該返回完整交易資訊"""
        from gaia_link.mcp_server import (
            get_donation_history,
            get_transaction_status,
        )

        mock_ctx = MagicMock()

        # 先取得一筆交易
        history = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=1,
            ctx=mock_ctx,
        )

        if history.get("donations"):
            tx_hash = history["donations"][0]["tx_hash"]

            result = await get_transaction_status.fn(
                tx_hash=tx_hash,
                ctx=mock_ctx,
            )

            if result.get("found", result.get("success")):
                # 應該包含必要欄位
                assert "tx_hash" in result
                assert "amount" in result
                assert "token" in result
                assert "status" in result


class TestMCPDonationHistoryIntegration:
    """MCP Donation History 整合測試"""

    @pytest.mark.asyncio
    async def test_workflow_get_history_then_check_status(self):
        """完整流程: 先取歷史，再查詢單筆狀態"""
        from gaia_link.mcp_server import (
            get_donation_history,
            get_transaction_status,
        )

        mock_ctx = MagicMock()

        # Step 1: 取得捐款歷史
        history = await get_donation_history.fn(
            wallet_address="0xTestWallet123",
            time_range="all",
            limit=5,
            ctx=mock_ctx,
        )

        assert history["success"] is True

        # Step 2: 對每筆交易查詢狀態
        for donation in history.get("donations", [])[:2]:
            tx_hash = donation["tx_hash"]

            status = await get_transaction_status.fn(
                tx_hash=tx_hash,
                ctx=mock_ctx,
            )

            # 應該能找到這筆交易
            assert status.get("found", status.get("success")) is True
            assert status["tx_hash"] == tx_hash
