"""
MockBlockchainService - 模擬區塊鏈服務

用於測試和 Hackathon Demo，不連接真實區塊鏈
"""

import hashlib
import secrets
import time
from typing import Optional

from gaia_link.services.base import BlockchainService, TransactionResult


# 支援的代幣列表
SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "DAI"]

# 代幣對美元的模擬匯率
TOKEN_USD_RATES = {
    "USDC": 1.0,
    "USDT": 1.0,
    "ETH": 2500.0,
    "DAI": 1.0,
}

# 模擬的 Gas 費用 (ETH) - 使用固定值確保 Demo 穩定
MOCK_GAS_FEE = 0.003


class MockBlockchainService(BlockchainService):
    """
    模擬區塊鏈服務

    特點：
    - 不連接真實區塊鏈
    - 使用固定 Gas 費用
    - 生成模擬交易 ID
    - 適用於測試和 Demo
    """

    @property
    def network_name(self) -> str:
        return "mock"

    @property
    def chain_id(self) -> int:
        return 0  # Mock 網絡沒有真實 chain ID

    async def send_transaction(
        self,
        amount: float,
        token: str,
        recipient_address: str,
        sender_address: Optional[str] = None,
    ) -> TransactionResult:
        """
        模擬發送交易

        Args:
            amount: 轉帳金額
            token: 代幣類型
            recipient_address: 接收者地址
            sender_address: 發送者地址 (Mock 模式下忽略)

        Returns:
            TransactionResult: 模擬交易結果
        """
        # 驗證金額
        if amount <= 0:
            return TransactionResult(
                success=False,
                status="failed",
                error="Donation amount must be positive",
            )

        # 驗證代幣
        if token not in SUPPORTED_TOKENS:
            return TransactionResult(
                success=False,
                status="failed",
                error=f"Unsupported token: {token}. Supported: {', '.join(SUPPORTED_TOKENS)}",
            )

        # 驗證地址
        if not self.is_valid_address(recipient_address):
            return TransactionResult(
                success=False,
                status="failed",
                error=f"Invalid recipient address format: {recipient_address}",
            )

        # 生成交易 ID
        tx_id = self._generate_transaction_id(amount, token, recipient_address)

        # 計算費用
        gas_fee = MOCK_GAS_FEE
        gas_fee_usd = gas_fee * TOKEN_USD_RATES["ETH"]

        return TransactionResult(
            success=True,
            transaction_id=tx_id,
            status="confirmed",
            gas_fee=round(gas_fee, 6),
            gas_fee_usd=round(gas_fee_usd, 2),
            explorer_url=self.get_explorer_url(tx_id),
        )

    def get_explorer_url(self, transaction_id: str) -> str:
        """
        獲取模擬的區塊鏈瀏覽器 URL

        注意：此 URL 在 Mock 模式下不會指向真實交易
        """
        return f"https://etherscan.io/tx/{transaction_id}"

    async def get_balance(
        self,
        address: str,
        token: str = "ETH",
    ) -> float:
        """
        返回模擬餘額

        Mock 模式下總是返回足夠的餘額
        """
        if not self.is_valid_address(address):
            return 0.0

        # 模擬餘額
        mock_balances = {
            "ETH": 10.0,
            "USDC": 10000.0,
            "USDT": 10000.0,
            "DAI": 10000.0,
        }
        return mock_balances.get(token, 0.0)

    async def estimate_gas(
        self,
        amount: float,
        token: str,
        recipient_address: str,
    ) -> float:
        """
        返回固定的模擬 Gas 費用
        """
        return MOCK_GAS_FEE

    def _generate_transaction_id(
        self,
        amount: float,
        token: str,
        recipient_address: str,
    ) -> str:
        """
        生成模擬交易 ID

        使用 secrets 模組確保加密安全
        """
        random_bytes = secrets.token_hex(16)
        data = f"{amount}{token}{recipient_address}{time.time()}{random_bytes}"
        hash_bytes = hashlib.sha256(data.encode()).hexdigest()
        return f"0x{hash_bytes}"

    def get_token_usd_rate(self, token: str) -> float:
        """獲取代幣對美元匯率"""
        return TOKEN_USD_RATES.get(token, 1.0)

    def get_supported_tokens(self) -> list[str]:
        """獲取支援的代幣列表"""
        return SUPPORTED_TOKENS.copy()
