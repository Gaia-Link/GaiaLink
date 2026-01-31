"""
X402 支付服務數據模型

HTTP 402 Payment Required 支付流程的核心數據結構。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class PaymentStatus(Enum):
    """支付狀態"""

    PENDING = "pending"  # 等待支付
    VERIFIED = "verified"  # 已驗證
    SETTLED = "settled"  # 已結算
    FAILED = "failed"  # 失敗
    EXPIRED = "expired"  # 已過期


@dataclass
class PaymentRequirements:
    """
    支付要求

    伺服器返回的 402 響應中包含的支付規格。
    """

    scheme: str = "exact"  # 支付方案
    network: str = "base-sepolia"  # 區塊鏈網路
    max_amount_required: str = "0"  # 原子單位金額
    resource: str = ""  # 受保護資源 URL
    description: str = ""  # 支付說明
    mime_type: str = "application/json"  # 響應類型
    pay_to: str = ""  # 收款地址
    max_timeout_seconds: int = 120  # 支付有效期
    asset: str = ""  # 代幣合約地址
    extra: Dict[str, Any] = field(default_factory=dict)  # 額外數據


@dataclass
class PaymentRequest:
    """
    支付請求

    用戶發起的支付參數。
    """

    resource: str  # 受保護資源 URL
    amount_usdc: Optional[Decimal] = None  # USD 金額
    amount_atomic: Optional[int] = None  # 原子單位 (優先)
    memo: Optional[str] = None  # 支付備註
    payer: Optional[str] = None  # 支付者地址
    network: str = "base-sepolia"  # 網路
    timeout_seconds: int = 120  # 有效期

    def get_amount_atomic(self, decimals: int = 6) -> int:
        """獲取原子單位金額"""
        if self.amount_atomic is not None:
            return self.amount_atomic
        if self.amount_usdc is not None:
            scale = Decimal(10) ** decimals
            return int(self.amount_usdc * scale)
        return 0


@dataclass
class PaymentHeader:
    """
    支付表頭

    簽署後的 X-PAYMENT 表頭內容。
    """

    header_value: str  # Base64 編碼的表頭
    payer: str  # 支付者地址
    amount_atomic: int  # 支付金額
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerifyResult:
    """
    驗證結果

    支付表頭驗證的結果。
    """

    is_valid: bool  # 是否有效
    invalid_reason: Optional[str] = None  # 無效原因
    payer: Optional[str] = None  # 支付者地址


@dataclass
class SettleResult:
    """
    結算結果

    支付結算的結果。
    """

    success: bool  # 是否成功
    error_reason: Optional[str] = None  # 錯誤原因
    transaction: Optional[str] = None  # 交易哈希
    network: Optional[str] = None  # 網路
    payer: Optional[str] = None  # 支付者地址


@dataclass
class PaymentReceipt:
    """
    支付收據

    完成支付後的收據。
    """

    success: bool  # 結算成功
    transaction: Optional[str] = None  # 交易哈希
    network: Optional[str] = None  # 網路
    payer: Optional[str] = None  # 支付者地址
    error_reason: Optional[str] = None  # 錯誤訊息
    raw: Dict[str, Any] = field(default_factory=dict)  # 原始數據


@dataclass
class X402Config:
    """
    X402 配置

    服務初始化配置。
    """

    # 基礎配置
    facilitator_url: str = "https://x402.org/facilitator"
    default_network: str = "base-sepolia"
    asset: str = "0xa063B8d5ada3bE64A24Df594F96aB75F0fb78160"  # USDC on Base Sepolia
    asset_decimals: int = 6
    max_amount_usdc: Decimal = Decimal("0.10")
    max_timeout_seconds: int = 120

    # 收款配置
    pay_to: str = ""  # 收款地址
    resource: str = ""  # 受保護資源

    # 客戶端配置 (用於簽署)
    private_key: Optional[str] = None  # 私鑰 (0x 前綴)
    use_turnkey: bool = False  # 使用 Turnkey 簽署

    @property
    def max_amount_atomic(self) -> int:
        """最大金額 (原子單位)"""
        scale = Decimal(10) ** self.asset_decimals
        return int(self.max_amount_usdc * scale)
