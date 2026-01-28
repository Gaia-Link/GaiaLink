"""
execute_donation 工具 - 執行捐款交易

基於 SpoonOS BaseTool 實現，模擬區塊鏈捐款交易
"""

import hashlib
import secrets
import time
from typing import Optional

from spoon_ai.tools.base import BaseTool

# 支援的代幣列表
SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "DAI"]

# 代幣對美元的模擬匯率
TOKEN_USD_RATES = {
    "USDC": 1.0,
    "USDT": 1.0,
    "ETH": 2500.0,
    "DAI": 1.0
}

# 模擬的 Gas 費用範圍 (ETH)
GAS_FEE_RANGE = (0.001, 0.005)


class ExecuteDonationTool(BaseTool):
    """
    執行人道救援捐款交易

    模擬區塊鏈上的代幣轉帳，支援 USDC、USDT、ETH、DAI 等代幣。
    計算 Gas 費用並產生交易 ID。
    """

    name: str = "execute_donation"
    description: str = (
        "Execute a humanitarian donation transaction on blockchain. "
        "Supports USDC, USDT, ETH, DAI tokens. "
        "Calculates gas fees and returns transaction details including "
        "transaction ID, status, and blockchain explorer URL."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Donation amount (must be positive)"
            },
            "token": {
                "type": "string",
                "enum": ["USDC", "USDT", "ETH", "DAI"],
                "description": "Token type for donation"
            },
            "recipient_address": {
                "type": "string",
                "description": "Recipient wallet address"
            }
        },
        "required": ["amount", "token", "recipient_address"]
    }

    async def execute(self, amount: float, token: str, recipient_address: str) -> dict:
        """
        執行捐款交易

        Args:
            amount: 捐款金額
            token: 代幣類型 (USDC, USDT, ETH, DAI)
            recipient_address: 接收者錢包地址

        Returns:
            交易結果字典，包含 success, transaction_id, status, details, explorer_url, error
        """
        # 驗證金額
        if amount <= 0:
            return self._build_error_response("Donation amount must be positive")

        # 驗證代幣
        if token not in SUPPORTED_TOKENS:
            return self._build_error_response(
                f"Unsupported token: {token}. Supported tokens: {', '.join(SUPPORTED_TOKENS)}"
            )

        # 驗證地址格式
        if not self._is_valid_address(recipient_address):
            return self._build_error_response(
                f"Invalid recipient address format: {recipient_address}"
            )

        # 模擬交易執行
        return self._execute_mock_transaction(amount, token, recipient_address)

    def _is_valid_address(self, address: str) -> bool:
        """驗證以太坊地址格式"""
        if not address:
            return False

        # 簡單的以太坊地址驗證（0x 開頭，40 個十六進位字符）
        if address.startswith("0x") and len(address) == 42:
            try:
                int(address[2:], 16)
                return True
            except ValueError:
                return False

        return False

    def _execute_mock_transaction(
        self,
        amount: float,
        token: str,
        recipient_address: str
    ) -> dict:
        """執行模擬交易"""
        # 生成交易 ID
        tx_id = self._generate_transaction_id(amount, token, recipient_address)

        # 計算 Gas 費用（使用固定值以確保 Demo 穩定）
        gas_fee = (GAS_FEE_RANGE[0] + GAS_FEE_RANGE[1]) / 2

        # 計算總成本（美元）
        token_rate = TOKEN_USD_RATES.get(token, 1.0)
        eth_rate = TOKEN_USD_RATES["ETH"]
        amount_usd = amount * token_rate
        gas_usd = gas_fee * eth_rate
        total_cost_usd = amount_usd + gas_usd

        # 構建成功回應
        return {
            "success": True,
            "transaction_id": tx_id,
            "status": "confirmed",
            "details": {
                "amount_sent": amount,
                "token": token,
                "gas_fee": round(gas_fee, 6),
                "total_cost_usd": round(total_cost_usd, 2)
            },
            "explorer_url": f"https://etherscan.io/tx/{tx_id}",
            "error": None
        }

    def _generate_transaction_id(
        self,
        amount: float,
        token: str,
        recipient_address: str
    ) -> str:
        """生成模擬交易 ID"""
        # 使用加密安全的隨機數生成唯一 ID
        random_bytes = secrets.token_hex(16)
        data = f"{amount}{token}{recipient_address}{time.time()}{random_bytes}"
        hash_bytes = hashlib.sha256(data.encode()).hexdigest()
        return f"0x{hash_bytes}"

    def _build_error_response(self, error_message: str) -> dict:
        """構建錯誤回應"""
        return {
            "success": False,
            "transaction_id": None,
            "status": "failed",
            "details": None,
            "explorer_url": None,
            "error": error_message
        }
