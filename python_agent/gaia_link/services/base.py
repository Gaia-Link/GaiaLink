"""
BlockchainService 抽象基類

定義區塊鏈服務的標準介面，支援多種實作：
- MockBlockchainService: 測試和 Demo 用
- SepoliaBlockchainService: Sepolia 測試網
- MainnetBlockchainService: 以太坊主網 (未來)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TransactionResult:
    """交易結果數據類"""
    success: bool
    transaction_id: Optional[str] = None
    status: str = "pending"
    gas_fee: float = 0.0
    gas_fee_usd: float = 0.0
    explorer_url: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "success": self.success,
            "transaction_id": self.transaction_id,
            "status": self.status,
            "gas_fee": self.gas_fee,
            "gas_fee_usd": self.gas_fee_usd,
            "explorer_url": self.explorer_url,
            "error": self.error,
        }


class BlockchainService(ABC):
    """
    區塊鏈服務抽象基類

    所有區塊鏈服務實作必須繼承此類並實現以下方法：
    - send_transaction: 發送交易
    - get_explorer_url: 獲取區塊鏈瀏覽器 URL
    - get_balance: 查詢餘額
    - estimate_gas: 估算 Gas 費用
    """

    @property
    @abstractmethod
    def network_name(self) -> str:
        """網絡名稱 (如 'mock', 'sepolia', 'mainnet')"""
        pass

    @property
    @abstractmethod
    def chain_id(self) -> int:
        """鏈 ID"""
        pass

    @abstractmethod
    async def send_transaction(
        self,
        amount: float,
        token: str,
        recipient_address: str,
        sender_address: Optional[str] = None,
    ) -> TransactionResult:
        """
        發送交易

        Args:
            amount: 轉帳金額
            token: 代幣類型 (USDC, USDT, ETH, DAI)
            recipient_address: 接收者地址
            sender_address: 發送者地址 (可選，某些實作可能需要)

        Returns:
            TransactionResult: 交易結果
        """
        pass

    @abstractmethod
    def get_explorer_url(self, transaction_id: str) -> str:
        """
        獲取區塊鏈瀏覽器 URL

        Args:
            transaction_id: 交易 ID

        Returns:
            str: 瀏覽器 URL
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def estimate_gas(
        self,
        amount: float,
        token: str,
        recipient_address: str,
    ) -> float:
        """
        估算 Gas 費用

        Args:
            amount: 轉帳金額
            token: 代幣類型
            recipient_address: 接收者地址

        Returns:
            float: 估算的 Gas 費用 (ETH)
        """
        pass

    def is_valid_address(self, address: str) -> bool:
        """
        驗證以太坊地址格式

        Args:
            address: 待驗證地址

        Returns:
            bool: 是否為有效地址
        """
        if not address:
            return False

        if not address.startswith("0x") or len(address) != 42:
            return False

        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
