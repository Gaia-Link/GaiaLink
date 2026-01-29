"""
SepoliaBlockchainService - Sepolia 測試網區塊鏈服務

連接以太坊 Sepolia 測試網執行真實交易
"""

import os
from typing import Optional

from gaia_link.services.base import BlockchainService, TransactionResult

# 嘗試導入 web3，如果未安裝則提供友好提示
try:
    from web3 import Web3
    from web3.exceptions import Web3Exception
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    Web3Exception = Exception


# Sepolia 測試網配置
SEPOLIA_CHAIN_ID = 11155111
SEPOLIA_EXPLORER_URL = "https://sepolia.etherscan.io"

# 代幣合約地址 (Sepolia 測試網)
SEPOLIA_TOKEN_CONTRACTS = {
    "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",  # Circle 官方測試 USDC
    "USDT": "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06",  # Sepolia USDT
    "DAI": "0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6",   # Sepolia DAI
}

# ERC20 轉帳 ABI (只需要 transfer 函數)
ERC20_TRANSFER_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class SepoliaBlockchainService(BlockchainService):
    """
    Sepolia 測試網區塊鏈服務

    需要配置：
    - SEPOLIA_RPC_URL: Sepolia RPC 端點 (如 Alchemy, Infura)
    - WALLET_PRIVATE_KEY: 發送者錢包私鑰 (僅測試用)

    注意：此服務用於測試目的，不要在生產環境使用私鑰直接存儲
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
    ):
        """
        初始化 Sepolia 服務

        Args:
            rpc_url: Sepolia RPC URL (默認從環境變數讀取)
            private_key: 錢包私鑰 (默認從環境變數讀取)
        """
        if not WEB3_AVAILABLE:
            raise ImportError(
                "web3 package is not installed. "
                "Install it with: pip install web3"
            )

        self._rpc_url = rpc_url or os.getenv("SEPOLIA_RPC_URL")
        self._private_key = private_key or os.getenv("WALLET_PRIVATE_KEY")

        if not self._rpc_url:
            raise ValueError(
                "SEPOLIA_RPC_URL is required. "
                "Set it via environment variable or constructor parameter."
            )

        # 初始化 Web3 連接
        self._web3 = Web3(Web3.HTTPProvider(self._rpc_url))

        # 驗證連接
        if not self._web3.is_connected():
            raise ConnectionError(f"Failed to connect to Sepolia RPC: {self._rpc_url}")

        # 設置發送者帳戶 (如果提供了私鑰)
        self._account = None
        if self._private_key:
            self._account = self._web3.eth.account.from_key(self._private_key)

    @property
    def network_name(self) -> str:
        return "sepolia"

    @property
    def chain_id(self) -> int:
        return SEPOLIA_CHAIN_ID

    @property
    def is_connected(self) -> bool:
        """檢查是否已連接到網絡"""
        return self._web3.is_connected()

    @property
    def sender_address(self) -> Optional[str]:
        """獲取發送者地址"""
        return self._account.address if self._account else None

    async def send_transaction(
        self,
        amount: float,
        token: str,
        recipient_address: str,
        sender_address: Optional[str] = None,
    ) -> TransactionResult:
        """
        發送真實交易到 Sepolia 測試網

        Args:
            amount: 轉帳金額
            token: 代幣類型 (ETH 或 ERC20)
            recipient_address: 接收者地址
            sender_address: 發送者地址 (忽略，使用配置的帳戶)

        Returns:
            TransactionResult: 交易結果
        """
        # 檢查帳戶配置
        if not self._account:
            return TransactionResult(
                success=False,
                status="failed",
                error="No wallet configured. Set WALLET_PRIVATE_KEY environment variable.",
            )

        # 驗證地址
        if not self.is_valid_address(recipient_address):
            return TransactionResult(
                success=False,
                status="failed",
                error=f"Invalid recipient address: {recipient_address}",
            )

        try:
            if token == "ETH":
                return await self._send_eth_transaction(amount, recipient_address)
            else:
                return await self._send_erc20_transaction(amount, token, recipient_address)
        except Web3Exception as e:
            return TransactionResult(
                success=False,
                status="failed",
                error=f"Web3 error: {str(e)}",
            )
        except Exception as e:
            return TransactionResult(
                success=False,
                status="failed",
                error=f"Transaction failed: {str(e)}",
            )

    async def _send_eth_transaction(
        self,
        amount: float,
        recipient_address: str,
    ) -> TransactionResult:
        """發送 ETH 交易"""
        # 轉換金額為 Wei
        amount_wei = self._web3.to_wei(amount, "ether")

        # 獲取 nonce
        nonce = self._web3.eth.get_transaction_count(self._account.address)

        # 估算 gas
        gas_price = self._web3.eth.gas_price
        gas_limit = 21000  # ETH 轉帳標準 gas

        # 構建交易
        transaction = {
            "nonce": nonce,
            "to": recipient_address,
            "value": amount_wei,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": SEPOLIA_CHAIN_ID,
        }

        # 簽名交易
        signed_txn = self._web3.eth.account.sign_transaction(
            transaction, self._private_key
        )

        # 發送交易
        tx_hash = self._web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_id = tx_hash.hex()

        # 計算 gas 費用
        gas_fee = self._web3.from_wei(gas_price * gas_limit, "ether")

        return TransactionResult(
            success=True,
            transaction_id=tx_id,
            status="pending",  # 交易已提交但未確認
            gas_fee=float(gas_fee),
            gas_fee_usd=float(gas_fee) * 2500,  # 估算 USD
            explorer_url=self.get_explorer_url(tx_id),
        )

    async def _send_erc20_transaction(
        self,
        amount: float,
        token: str,
        recipient_address: str,
    ) -> TransactionResult:
        """發送 ERC20 代幣交易"""
        # 檢查代幣是否支援
        if token not in SEPOLIA_TOKEN_CONTRACTS:
            return TransactionResult(
                success=False,
                status="failed",
                error=f"Token {token} not supported on Sepolia. Supported: {list(SEPOLIA_TOKEN_CONTRACTS.keys())}",
            )

        contract_address = SEPOLIA_TOKEN_CONTRACTS[token]

        # 創建合約實例
        contract = self._web3.eth.contract(
            address=contract_address,
            abi=ERC20_TRANSFER_ABI,
        )

        # 獲取代幣小數位數 (大多數穩定幣是 6 或 18)
        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            decimals = 6  # 默認使用 6 (USDC/USDT 標準)

        # 轉換金額
        amount_with_decimals = int(amount * (10 ** decimals))

        # 獲取 nonce
        nonce = self._web3.eth.get_transaction_count(self._account.address)

        # 估算 gas
        gas_price = self._web3.eth.gas_price

        try:
            gas_limit = contract.functions.transfer(
                recipient_address,
                amount_with_decimals,
            ).estimate_gas({"from": self._account.address})
        except Exception:
            gas_limit = 100000  # ERC20 轉帳默認 gas

        # 構建交易
        transaction = contract.functions.transfer(
            recipient_address,
            amount_with_decimals,
        ).build_transaction({
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": SEPOLIA_CHAIN_ID,
        })

        # 簽名交易
        signed_txn = self._web3.eth.account.sign_transaction(
            transaction, self._private_key
        )

        # 發送交易
        tx_hash = self._web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_id = tx_hash.hex()

        # 計算 gas 費用
        gas_fee = self._web3.from_wei(gas_price * gas_limit, "ether")

        return TransactionResult(
            success=True,
            transaction_id=tx_id,
            status="pending",
            gas_fee=float(gas_fee),
            gas_fee_usd=float(gas_fee) * 2500,
            explorer_url=self.get_explorer_url(tx_id),
        )

    def get_explorer_url(self, transaction_id: str) -> str:
        """獲取 Sepolia Etherscan URL"""
        return f"{SEPOLIA_EXPLORER_URL}/tx/{transaction_id}"

    async def get_balance(
        self,
        address: str,
        token: str = "ETH",
    ) -> float:
        """
        查詢地址餘額

        Args:
            address: 錢包地址
            token: 代幣類型

        Returns:
            float: 餘額
        """
        if not self.is_valid_address(address):
            return 0.0

        try:
            if token == "ETH":
                balance_wei = self._web3.eth.get_balance(address)
                return float(self._web3.from_wei(balance_wei, "ether"))
            else:
                if token not in SEPOLIA_TOKEN_CONTRACTS:
                    return 0.0

                contract = self._web3.eth.contract(
                    address=SEPOLIA_TOKEN_CONTRACTS[token],
                    abi=ERC20_TRANSFER_ABI,
                )

                try:
                    decimals = contract.functions.decimals().call()
                except Exception:
                    decimals = 6

                balance = contract.functions.balanceOf(address).call()
                return balance / (10 ** decimals)
        except Exception:
            return 0.0

    async def estimate_gas(
        self,
        amount: float,
        token: str,
        recipient_address: str,
    ) -> float:
        """
        估算 Gas 費用

        Returns:
            float: 估算的 Gas 費用 (ETH)
        """
        try:
            gas_price = self._web3.eth.gas_price

            if token == "ETH":
                gas_limit = 21000
            else:
                gas_limit = 100000  # ERC20 轉帳估算

            gas_fee_wei = gas_price * gas_limit
            return float(self._web3.from_wei(gas_fee_wei, "ether"))
        except Exception:
            return 0.003  # 默認估算

    async def wait_for_confirmation(
        self,
        transaction_id: str,
        timeout: int = 120,
    ) -> TransactionResult:
        """
        等待交易確認

        Args:
            transaction_id: 交易 ID
            timeout: 超時時間（秒）

        Returns:
            TransactionResult: 確認後的交易結果
        """
        try:
            receipt = self._web3.eth.wait_for_transaction_receipt(
                transaction_id,
                timeout=timeout,
            )

            success = receipt["status"] == 1
            gas_used = receipt["gasUsed"]
            gas_price = receipt["effectiveGasPrice"]
            gas_fee = self._web3.from_wei(gas_used * gas_price, "ether")

            return TransactionResult(
                success=success,
                transaction_id=transaction_id,
                status="confirmed" if success else "failed",
                gas_fee=float(gas_fee),
                gas_fee_usd=float(gas_fee) * 2500,
                explorer_url=self.get_explorer_url(transaction_id),
                error=None if success else "Transaction reverted",
            )
        except Exception as e:
            return TransactionResult(
                success=False,
                transaction_id=transaction_id,
                status="timeout",
                error=f"Confirmation timeout: {str(e)}",
            )
