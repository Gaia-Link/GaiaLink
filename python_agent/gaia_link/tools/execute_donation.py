"""
execute_donation 工具 - 執行捐款交易

基於 SpoonOS BaseTool 實現，支援 Mock 和真實區塊鏈交易
"""

import re
from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.config import get_blockchain_service, get_settings
from gaia_link.services.base import BlockchainService
from gaia_link.services.base import BlockchainService
from gaia_link.services.sepolia_blockchain import GAIA_CONTRACTS


# 支援的代幣列表
SUPPORTED_TOKENS = ["USDC", "USDT", "ETH", "DAI"]

# ERC20 Transfer Selector (a9059cbb)
ERC20_TRANSFER_SELECTOR = "0xa9059cbb"
# GaiaProposalManager.depositToProposal(uint256,uint256,bool) selector
GAIA_DEPOSIT_SELECTOR = "0xd1836538" 
# ERC20 approve(address,uint256) selector
ERC20_APPROVE_SELECTOR = "0x095ea7b3"

# 代幣對美元的參考匯率
TOKEN_USD_RATES = {
    "USDC": 1.0,
    "USDT": 1.0,
    "ETH": 2500.0,
    "DAI": 1.0,
}

# Sepolia 測試網代幣合約地址
import os
# Sepolia 測試網代幣合約地址
# Token Contract Addresses (Default to Sepolia, but should be configurable)
SEPOLIA_TOKEN_CONTRACTS = {
    "USDC": os.getenv("USDC_TOKEN_ADDRESS", "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"),
    "USDT": "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06", # Placeholder if not set env
    "DAI": "0x68194a729C2450ad26072b3D33ADaCbcef39D574",
}

# 代幣小數位數
TOKEN_DECIMALS = {
    "USDC": 18,
    "USDT": 6,
    "DAI": 18,
    "ETH": 18,
}


def encode_erc20_transfer(recipient: str, amount: float, decimals: int = 6) -> str:
    """
    編碼 ERC20 transfer(address,uint256) calldata

    Args:
        recipient: 接收地址 (含或不含 0x 前綴)
        amount: 轉帳金額 (人類可讀格式，如 100.0)
        decimals: 代幣小數位數 (USDC = 6, DAI = 18)

    Returns:
        完整的 calldata hex string (含 0x 前綴)
    """
    # 清理地址格式
    clean_recipient = recipient.lower().replace("0x", "")

    # 將金額轉為最小單位 (USDC: 100 -> 100000000)
    amount_wei = int(amount * (10 ** decimals))

    # 編碼參數 (每個參數 32 bytes = 64 hex chars)
    # address: 左補零到 32 bytes
    address_padded = clean_recipient.zfill(64)
    # uint256: 左補零到 32 bytes
    amount_hex = hex(amount_wei)[2:].zfill(64)

    return f"{ERC20_TRANSFER_SELECTOR}{address_padded}{amount_hex}"


def encode_erc20_approve(spender: str, amount: float, decimals: int = 6) -> str:
    """
    編碼 ERC20 approve(address,uint256) calldata
    """
    clean_spender = spender.lower().replace("0x", "")
    amount_wei = int(amount * (10 ** decimals))
    address_padded = clean_spender.zfill(64)
    amount_hex = hex(amount_wei)[2:].zfill(64)
    return f"{ERC20_APPROVE_SELECTOR}{address_padded}{amount_hex}"


def encode_gaia_deposit(proposal_id: int, amount: float, is_no_loss: bool = False, decimals: int = 18) -> str:
    """
    編碼 GaiaProposalManager.depositToProposal(uint256,uint256,bool) calldata

    Args:
        proposal_id: 提案 ID
        amount: 捐款金額
        is_no_loss: 是否為 No-Loss 捐款
        decimals: 代幣小數位數 (Gaia 預設 USDC 為 18 in contract context, but let's check)
    """
    # 將金額轉為最小單位
    amount_wei = int(amount * (10 ** decimals))

    # 編碼參數
    pid_hex = hex(proposal_id)[2:].zfill(64)
    amount_hex = hex(amount_wei)[2:].zfill(64)
    bool_hex = "1".zfill(64) if is_no_loss else "0".zfill(64)

    return f"{GAIA_DEPOSIT_SELECTOR}{pid_hex}{amount_hex}{bool_hex}"


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
            "proposal_id": {
                "type": "string",
                "description": "Proposal ID to donate to (numeric string, e.g., '0')"
            },
            "proposal_name": {
                "type": "string",
                "description": "Name of the proposal to donate to (if ID is unknown)"
            },
            "vault_type": {
                "type": "string",
                "enum": ["DIRECT", "YIELD"],
                "description": "Type of vault strategy. DIRECT = immediate transfer, YIELD = no-loss donation via DeFi.",
                "default": "DIRECT"
            },
            "action": {
                "type": "string",
                "enum": ["APPROVE", "DEPOSIT"],
                "description": "Action to perform. APPROVE = authorize manager to spend USDC, DEPOSIT = execute donation.",
                "default": "DEPOSIT"
            }
        },
        "required": ["amount", "token"]
    }

    # 允許注入自定義服務（用於測試）
    _blockchain_service: Optional[BlockchainService] = None

    def __init__(self, blockchain_service: Optional[BlockchainService] = None, **data):
        super().__init__(**data)
        self._blockchain_service = blockchain_service

    def _get_service(self) -> BlockchainService:
        if self._blockchain_service is not None:
            return self._blockchain_service
        return get_blockchain_service()

    async def execute(self, amount: float, token: str, recipient_address: str = None, vault_type: str = "DIRECT", proposal_id: str = None, proposal_name: str = None, action: str = "DEPOSIT") -> dict:
        """
        準備捐款交易 Payload
        """
        # 輸入驗證
        if amount <= 0:
            return self._build_error_response("Amount must be positive")

        if token not in SUPPORTED_TOKENS:
            return self._build_error_response(
                f"Unsupported token: {token}. Supported: {', '.join(SUPPORTED_TOKENS)}"
            )

        # 若未提供地址，使用 GaiaProposalManager 地址
        if not recipient_address:
            from gaia_link.services.blockchain.config import get_blockchain_config
            recipient_address = get_blockchain_config().addresses.proposal_manager
        else:
            # 驗證地址格式 (基本驗證)
            if not self._is_valid_eth_address(recipient_address):
                return self._build_error_response(
                    f"Invalid Ethereum address: {recipient_address}"
                )

        # 獲取代幣小數位數
        decimals = TOKEN_DECIMALS.get(token, 6)

        from gaia_link.services.blockchain.config import get_blockchain_config
        blockchain_config = get_blockchain_config()

        # 自動解析提案名稱為 ID
        if not proposal_id and proposal_name:
            from gaia_link.services.proposal import get_proposal_service
            service = get_proposal_service()
            proposals = await service.list_proposals(title_query=proposal_name)
            if proposals:
                # 優先完全符合
                exact_match = next((p for p in proposals if p.title.lower() == proposal_name.lower()), None)
                proposal_id = exact_match.proposal_id if exact_match else proposals[0].proposal_id

        if action == "APPROVE":
            # Generate Approval Payload
            spender = blockchain_config.addresses.proposal_manager
            calldata = encode_erc20_approve(spender, amount, decimals)
            tx_to = blockchain_config.addresses.usdc_token or SEPOLIA_TOKEN_CONTRACTS["USDC"]
            tx_value = "0"
            estimated_gas = 50000
            chain_id = blockchain_config.chain_id
            
            return {
                "success": True,
                "status": "ready_to_sign",
                "action": "APPROVE",
                "transaction_payload": {
                    "to": tx_to,
                    "value": tx_value,
                    "data": calldata,
                    "chainId": chain_id,
                    "gas": str(estimated_gas),
                    "intent_summary": f"Approve Gaia Manager to spend {amount} {token}"
                },
                "message": f"I've prepared an approval transaction for {amount} {token}. This is required before you can donate."
            }

        # 根據代幣類型構建交易
        if proposal_id:
            # Gaia Proposal Deposit
            pid = int(proposal_id)
            is_no_loss = (vault_type == "YIELD")
            
            # Gaia contract expects 18 decimals for USDC usually in SetupDemo context
            # Let's use 18 as default for contract interaction unless specified
            calldata = encode_gaia_deposit(pid, amount, is_no_loss, decimals=18)
            
            from gaia_link.services.blockchain.config import get_blockchain_config
            blockchain_config = get_blockchain_config()
            tx_to = blockchain_config.addresses.proposal_manager
            tx_value = "0"
            estimated_gas = 150000
            chain_id = blockchain_config.chain_id
        elif token == "ETH":
            # ETH 原生轉帳
            calldata = "0x"
            tx_to = recipient_address
            # ETH value 以 Wei 為單位 (amount * 10^18)
            tx_value = str(int(amount * (10 ** 18)))
            estimated_gas = 21000
            
            from gaia_link.services.blockchain.config import get_blockchain_config
            chain_id = get_blockchain_config().chain_id
        else:
            # ERC20 transfer
            calldata = encode_erc20_transfer(recipient_address, amount, decimals)
            # Send to token contract
            # If we are on Foundry/Local, make sure we use the configured USDC address
            from gaia_link.services.blockchain.config import get_blockchain_config
            blockchain_config = get_blockchain_config()
            
            if token == "USDC":
                 tx_to = blockchain_config.addresses.usdc_token or SEPOLIA_TOKEN_CONTRACTS["USDC"]
            else:
                 tx_to = SEPOLIA_TOKEN_CONTRACTS.get(token, SEPOLIA_TOKEN_CONTRACTS["USDC"])
            
            tx_value = "0"
            estimated_gas = 65000
            chain_id = blockchain_config.chain_id

            # CRITICAL: Prevent direct transfer to ProposalManager
            if recipient_address.lower() == blockchain_config.addresses.proposal_manager.lower():
                return self._build_error_response(
                    "Direct transfer to ProposalManager is prohibited. Please specify a proposal_id or proposal_name."
                )

        return {
            "success": True,
            "status": "ready_to_sign",
            "transaction_payload": {
                "to": tx_to,
                "value": tx_value,
                "data": calldata,
                "chainId": chain_id,
                "gas": str(estimated_gas),
                "intent_summary": f"Donate {amount} {token} via {vault_type} Vault"
            },
            "details": {
                "amount": amount,
                "token": token,
                "vault_type": vault_type,
                "proposal_id": proposal_id,
                "recipient": recipient_address if not proposal_id else tx_to,
                "token_contract": tx_to if token != "ETH" else None,
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
            "details": {},
            "explorer_url": None,
            "error": error_message,
        }

    def _is_valid_eth_address(self, address: str) -> bool:
        """
        驗證 Ethereum 地址格式

        Args:
            address: 要驗證的地址

        Returns:
            True 如果地址格式有效
        """
        if not address:
            return False
        # 以太坊地址: 0x + 40 hex characters
        pattern = r'^0x[a-fA-F0-9]{40}$'
        return bool(re.match(pattern, address))

    def get_supported_tokens(self) -> list[str]:
        """獲取支援的代幣列表"""
        return SUPPORTED_TOKENS.copy()

    def get_token_rate(self, token: str) -> float:
        """獲取代幣對美元匯率"""
        return TOKEN_USD_RATES.get(token, 1.0)
