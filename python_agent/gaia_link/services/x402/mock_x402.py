"""
Mock X402 支付服務

用於測試的模擬 HTTP 402 支付實現。
不需要真正的區塊鏈交互或私鑰簽署。
"""

import base64
import json
import hashlib
import secrets
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from .base import X402Service
from .models import (
    PaymentRequirements,
    PaymentRequest,
    PaymentHeader,
    VerifyResult,
    SettleResult,
    PaymentReceipt,
    X402Config,
)


class MockX402Service(X402Service):
    """
    Mock X402 支付服務

    模擬 HTTP 402 支付流程，用於測試。
    - 不需要真正的私鑰
    - 不需要區塊鏈交互
    - 支援驗證 mock 生成的表頭
    """

    def __init__(self, config: Optional[X402Config] = None):
        """
        初始化 Mock 服務

        Args:
            config: 可選的配置，默認使用標準配置
        """
        self._config = config or X402Config()
        # 用於追蹤已生成的支付表頭（模擬驗證）
        self._valid_headers: dict[str, dict] = {}

    def get_config(self) -> X402Config:
        """獲取當前配置"""
        return self._config

    def build_payment_requirements(
        self,
        request: Optional[PaymentRequest] = None,
    ) -> PaymentRequirements:
        """
        構建支付要求

        基於配置和請求構建完整的支付規格。
        """
        # 計算金額
        if request is not None:
            amount_atomic = request.get_amount_atomic(self._config.asset_decimals)
            resource = request.resource or self._config.resource
            network = request.network
            timeout = request.timeout_seconds
            memo = request.memo
        else:
            amount_atomic = self._config.max_amount_atomic
            resource = self._config.resource
            network = self._config.default_network
            timeout = self._config.max_timeout_seconds
            memo = None

        # 構建描述
        description = self._config.resource or "SpoonOS agent service"
        extra = {}
        if memo:
            extra["memo"] = memo

        return PaymentRequirements(
            scheme="exact",
            network=network,
            max_amount_required=str(amount_atomic),
            resource=resource,
            description=description,
            mime_type="application/json",
            pay_to=self._config.pay_to,
            max_timeout_seconds=timeout,
            asset=self._config.asset,
            extra=extra,
        )

    def build_payment_header(
        self,
        requirements: PaymentRequirements,
        max_value: Optional[int] = None,
    ) -> PaymentHeader:
        """
        構建支付表頭

        Mock 實現：生成模擬的 X-PAYMENT 表頭。
        """
        amount_atomic = int(requirements.max_amount_required)

        # 檢查最大金額限制
        if max_value is not None and amount_atomic > max_value:
            raise ValueError(
                f"Payment amount {amount_atomic} exceeds max_value {max_value}"
            )

        # 生成模擬的支付者地址
        if self._config.private_key:
            # 從私鑰派生模擬地址
            key_hash = hashlib.sha256(self._config.private_key.encode()).hexdigest()
            payer = "0x" + key_hash[:40]
        else:
            payer = "0x" + secrets.token_hex(20)

        # 生成模擬的支付表頭
        header_data = {
            "version": "1",
            "scheme": requirements.scheme,
            "network": requirements.network,
            "from": payer,
            "to": requirements.pay_to,
            "value": str(amount_atomic),
            "resource": requirements.resource,
            "nonce": secrets.token_hex(16),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signature": "mock_signature_" + secrets.token_hex(32),
        }

        header_value = base64.b64encode(json.dumps(header_data).encode()).decode()

        # 記錄有效表頭（用於驗證）
        self._valid_headers[header_value] = header_data

        return PaymentHeader(
            header_value=header_value,
            payer=payer,
            amount_atomic=amount_atomic,
            created_at=datetime.now(timezone.utc),
        )

    async def verify_payment(
        self,
        header_value: str,
        requirements: Optional[PaymentRequirements] = None,
    ) -> VerifyResult:
        """
        驗證支付表頭

        Mock 實現：檢查表頭是否由本服務生成。
        """
        # 檢查是否是已知的有效表頭
        if header_value in self._valid_headers:
            header_data = self._valid_headers[header_value]
            return VerifyResult(
                is_valid=True,
                payer=header_data.get("from"),
            )

        # 嘗試解碼未知表頭
        try:
            decoded = base64.b64decode(header_value)
            header_data = json.loads(decoded)

            # 基本格式檢查
            if all(
                k in header_data for k in ["version", "scheme", "from", "to", "value"]
            ):
                return VerifyResult(
                    is_valid=True,
                    payer=header_data.get("from"),
                )
        except Exception:
            pass

        return VerifyResult(
            is_valid=False,
            invalid_reason="Invalid or unknown payment header",
        )

    async def settle_payment(
        self,
        header_value: str,
        requirements: Optional[PaymentRequirements] = None,
    ) -> SettleResult:
        """
        結算支付

        Mock 實現：模擬成功的結算。
        """
        # 先驗證
        verify_result = await self.verify_payment(header_value, requirements)

        if not verify_result.is_valid:
            return SettleResult(
                success=False,
                error_reason=verify_result.invalid_reason or "Verification failed",
            )

        # 生成模擬交易哈希
        tx_hash = "0x" + secrets.token_hex(32)

        # 獲取網路資訊
        network = self._config.default_network
        if header_value in self._valid_headers:
            network = self._valid_headers[header_value].get(
                "network", self._config.default_network
            )

        return SettleResult(
            success=True,
            transaction=tx_hash,
            network=network,
            payer=verify_result.payer,
        )

    async def verify_and_settle(
        self,
        header_value: str,
        requirements: Optional[PaymentRequirements] = None,
        settle: bool = True,
    ) -> tuple[VerifyResult, Optional[SettleResult]]:
        """
        驗證並結算支付

        組合操作：先驗證，成功後結算。
        """
        verify_result = await self.verify_payment(header_value, requirements)

        if not verify_result.is_valid or not settle:
            return verify_result, None

        settle_result = await self.settle_payment(header_value, requirements)
        return verify_result, settle_result

    def decode_payment_response(
        self,
        response_header: str,
    ) -> PaymentReceipt:
        """
        解碼支付響應

        解析 X-PAYMENT-RESPONSE 表頭。
        """
        try:
            decoded = base64.b64decode(response_header)
            data = json.loads(decoded)

            return PaymentReceipt(
                success=data.get("success", False),
                transaction=data.get("transaction"),
                network=data.get("network"),
                payer=data.get("payer"),
                error_reason=data.get("error_reason"),
                raw=data,
            )
        except Exception as e:
            return PaymentReceipt(
                success=False,
                error_reason=f"Failed to decode response: {str(e)}",
                raw={},
            )
