"""
execute_donation 工具 - 執行捐款交易

基於 SpoonOS BaseTool 實現，支援 Mock 和真實區塊鏈交易
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.config import get_blockchain_service, get_settings
from gaia_link.services.base import BlockchainService


# 支援的代幣列表
SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "DAI"]

# 代幣對美元的參考匯率
TOKEN_USD_RATES = {
    "USDC": 1.0,
    "USDT": 1.0,
    "ETH": 2500.0,
    "DAI": 1.0,
}


class ExecuteDonationTool(BaseTool):
    """
    執行人道救援捐款交易

    支援兩種模式：
    - Mock 模式：用於測試和 Demo，不連接真實區塊鏈
    - Sepolia 模式：連接以太坊 Sepolia 測試網執行真實交易

    模式透過環境變數 BLOCKCHAIN_NETWORK 控制：
    - mock (默認): 使用 MockBlockchainService
    - sepolia: 使用 SepoliaBlockchainService
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

    # 允許注入自定義服務（用於測試）
    _blockchain_service: Optional[BlockchainService] = None

    def __init__(self, blockchain_service: Optional[BlockchainService] = None, **data):
        """
        初始化工具

        Args:
            blockchain_service: 可選的區塊鏈服務實例（用於依賴注入）
        """
        super().__init__(**data)
        self._blockchain_service = blockchain_service

    def _get_service(self) -> BlockchainService:
        """獲取區塊鏈服務實例"""
        if self._blockchain_service is not None:
            return self._blockchain_service
        return get_blockchain_service()

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
        # 獲取服務
        service = self._get_service()
        settings = get_settings()

        # 執行交易
        result = await service.send_transaction(
            amount=amount,
            token=token,
            recipient_address=recipient_address,
        )

        # 如果交易失敗，返回錯誤
        if not result.success:
            return self._build_error_response(result.error or "Transaction failed")

        # 計算總成本（美元）
        token_rate = TOKEN_USD_RATES.get(token, 1.0)
        amount_usd = amount * token_rate
        total_cost_usd = amount_usd + result.gas_fee_usd

        # 構建成功回應
        return {
            "success": True,
            "transaction_id": result.transaction_id,
            "status": result.status,
            "details": {
                "amount_sent": amount,
                "token": token,
                "gas_fee": result.gas_fee,
                "total_cost_usd": round(total_cost_usd, 2),
                "network": service.network_name,
            },
            "explorer_url": result.explorer_url,
            "error": None,
        }

    def _build_error_response(self, error_message: str) -> dict:
        """構建錯誤回應"""
        return {
            "success": False,
            "transaction_id": None,
            "status": "failed",
            "details": None,
            "explorer_url": None,
            "error": error_message,
        }

    def get_supported_tokens(self) -> list[str]:
        """獲取支援的代幣列表"""
        return SUPPORTED_TOKENS.copy()

    def get_token_rate(self, token: str) -> float:
        """獲取代幣對美元匯率"""
        return TOKEN_USD_RATES.get(token, 1.0)
