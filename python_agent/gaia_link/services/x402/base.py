"""
X402 支付服務抽象層

定義 X402Service 的抽象介面，
支援 Mock 和真實實作 (spoon-core) 的切換。
"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import (
    PaymentRequirements,
    PaymentRequest,
    PaymentHeader,
    VerifyResult,
    SettleResult,
    PaymentReceipt,
    X402Config,
)


class X402Service(ABC):
    """
    X402 支付服務抽象類

    定義 HTTP 402 支付流程的核心操作介面。
    實作類可以是:
    - MockX402Service: 本地測試用
    - GaiaX402Service: 封裝 spoon-core X402PaymentService
    """

    @abstractmethod
    def get_config(self) -> X402Config:
        """獲取當前配置"""
        pass

    @abstractmethod
    def build_payment_requirements(
        self,
        request: Optional[PaymentRequest] = None,
    ) -> PaymentRequirements:
        """
        構建支付要求

        基於配置和請求構建完整的支付規格。

        Args:
            request: 可選的支付請求參數

        Returns:
            PaymentRequirements: 支付要求
        """
        pass

    @abstractmethod
    def build_payment_header(
        self,
        requirements: PaymentRequirements,
        max_value: Optional[int] = None,
    ) -> PaymentHeader:
        """
        構建支付表頭

        簽署並生成 X-PAYMENT 表頭。

        Args:
            requirements: 支付要求
            max_value: 最大允許金額 (安全上限)

        Returns:
            PaymentHeader: 簽署後的支付表頭

        Raises:
            ValueError: 金額超過上限
            RuntimeError: 簽署失敗
        """
        pass

    @abstractmethod
    async def verify_payment(
        self,
        header_value: str,
        requirements: Optional[PaymentRequirements] = None,
    ) -> VerifyResult:
        """
        驗證支付表頭

        Args:
            header_value: X-PAYMENT 表頭值
            requirements: 可選的支付要求 (用於驗證)

        Returns:
            VerifyResult: 驗證結果
        """
        pass

    @abstractmethod
    async def settle_payment(
        self,
        header_value: str,
        requirements: Optional[PaymentRequirements] = None,
    ) -> SettleResult:
        """
        結算支付

        Args:
            header_value: X-PAYMENT 表頭值
            requirements: 可選的支付要求

        Returns:
            SettleResult: 結算結果
        """
        pass

    @abstractmethod
    async def verify_and_settle(
        self,
        header_value: str,
        requirements: Optional[PaymentRequirements] = None,
        settle: bool = True,
    ) -> tuple[VerifyResult, Optional[SettleResult]]:
        """
        驗證並結算支付

        組合操作：先驗證，成功後結算。

        Args:
            header_value: X-PAYMENT 表頭值
            requirements: 可選的支付要求
            settle: 是否執行結算 (False 則只驗證)

        Returns:
            (VerifyResult, SettleResult | None): 驗證結果和結算結果
        """
        pass

    @abstractmethod
    def decode_payment_response(
        self,
        response_header: str,
    ) -> PaymentReceipt:
        """
        解碼支付響應

        解析 X-PAYMENT-RESPONSE 表頭。

        Args:
            response_header: Base64 編碼的響應表頭

        Returns:
            PaymentReceipt: 支付收據
        """
        pass
