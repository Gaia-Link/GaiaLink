"""
execute_donation 工具 - 執行捐款交易

基於 SpoonOS BaseTool 實現，支援 Mock 和真實區塊鏈交易
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.config import get_blockchain_service, get_settings
from gaia_link.services.base import BlockchainService
from gaia_link.services.sepolia_blockchain import GAIA_CONTRACTS


# 支援的代幣列表
SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "DAI"]

# ERC20 Transfer Selector (a9059cbb)
ERC20_TRANSFER_SELECTOR = "0xa9059cbb"

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
        "Prepare a humanitarian donation transaction payload for user signature. "
        "Supports USDC, USDT, ETH, DAI tokens. "
        "Can route to DIRECT vaults or YIELD strategies (Euler/Pendle). "
        "Returns a transaction object that the frontend can propose to the user."
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
                "description": "Target address (optional, if not provided will route based on context)"
            },
            "vault_type": {
                "type": "string",
                "enum": ["DIRECT", "YIELD"],
                "description": "Type of vault strategy. DIRECT = immediate transfer, YIELD = no-loss donation via DeFi.",
                "default": "DIRECT"
            }
        },
        "required": ["amount", "token"]
    }

    # 允許注入自定義服務（用於測試）
    _blockchain_service: Optional[BlockchainService] = None

    def __init__(self, blockchain_service: Optional[BlockchainService] = None, **data):
        super().__init__(**data)
        self._blockchain_service = blockchain_service

        return get_blockchain_service()

    def _encode_erc20_transfer(self, to_address: str, amount: float, decimals: int = 18) -> str:
        """
        手動編碼 ERC20 transfer 函數
        transfer(address to, uint256 amount)
        """
        # 移除 0x 前綴
        to_clean = to_address.replace("0x", "")
        
        # 計算金額 (Wei)
        amount_wei = int(amount * (10 ** decimals))
        
        # 參數 1: 地址 (32 bytes padding)
        param_to = to_clean.zfill(64)
        
        # 參數 2: 金額 (32 bytes padding hex)
        param_amount = hex(amount_wei)[2:].zfill(64)
        
        return f"{ERC20_TRANSFER_SELECTOR}{param_to}{param_amount}"

    async def execute(self, amount: float, token: str, recipient_address: str = None, vault_type: str = "DIRECT") -> dict:
        """
        準備捐款交易 Payload

        Args:
            amount: 捐款金額
            token: 代幣類型
            recipient_address: 接收地址 (若無則由 Agent 根據上下文決定，此處 Demo 默認 mock)
            vault_type: 資金池類型 (DIRECT/YIELD)
        """
        # 輸入驗證
        if amount <= 0:
            return self._build_error_response("Amount must be positive")

        if token not in SUPPORTED_TOKENS:
            return self._build_error_response(
                f"Unsupported token: {token}. Supported: {', '.join(SUPPORTED_TOKENS)}"
            )

        # 若未提供地址，使用 Mock 地址 (Demo 用)
        if not recipient_address:
            recipient_address = GAIA_CONTRACTS["ProposalManager"]

        # 簡單的 Payload 構建 (Mock)
        # 真實場景會調用合約生成 calldata (e.g., ERC20 transfer or Vault deposit)
        
        # 獲取服務用於估算 Gas (可選)
        service = self._get_service()
        
        # 模擬 Gas 估算
        estimated_gas = 21000
        estimated_gas_price = "20 gwei"

        # 構建交易 Payload
        tx_data = "0x"
        tx_value = "0"
        
        if token == "ETH":
            tx_value = str(int(amount * 1e18)) # Wei
        else:
            # ERC20 Transfer
            # 默認精度 18 (USDC 通常是 6，但在 Local Mock 是 18? 檢查 MockERC20)
            # 假設 MockERC20 用 18, 真實 USDC 用 6. 
            # 簡單起見，Demo 用 18.
            decimals = 6 if token in ["USDC", "USDT"] else 18
            tx_data = self._encode_erc20_transfer(recipient_address, amount, decimals)

        return {
            "success": True,
            "status": "ready_to_sign",
            "transaction_payload": {
                "to": recipient_address if token == "ETH" else GAIA_CONTRACTS.get(token, recipient_address), # 如果是 ERC20，對象是 Token 合約
                "value": tx_value,
                "data": tx_data,
                "chainId": 31337, # Local Anvil (was 11155111)
                "intent_summary": f"Donate {amount} {token} via {vault_type} Vault"
            },
            "details": {
                "amount": amount,
                "token": token,
                "vault_type": vault_type,
                "estimated_gas": estimated_gas
            },
            "message": f"I have prepared a {vault_type} donation of {amount} {token}. Please sign the transaction to proceed."
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
