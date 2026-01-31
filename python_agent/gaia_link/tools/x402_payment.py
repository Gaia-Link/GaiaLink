"""
X402 支付工具

HTTP 402 Payment Required 支付相關工具集合。
"""

from typing import Optional
from decimal import Decimal

from spoon_ai.tools.base import BaseTool

from gaia_link.services.x402 import get_x402_service, PaymentRequest


class X402PaymentTool(BaseTool):
    """
    X402 支付表頭構建工具

    為 HTTP 402 付費資源構建簽署的支付表頭。
    """

    name: str = "x402_payment"
    description: str = (
        "Build a signed X-PAYMENT header for HTTP 402 paywalled resources. "
        "Returns the payment header that can be used to access protected resources."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "resource": {
                "type": "string",
                "description": "URL of the protected resource",
            },
            "amount_usdc": {
                "type": "number",
                "description": "Payment amount in USDC (e.g., 0.01)",
            },
            "amount_atomic": {
                "type": "integer",
                "description": "Payment amount in atomic units (overrides amount_usdc)",
            },
            "memo": {
                "type": "string",
                "description": "Optional payment memo/note",
            },
            "max_value": {
                "type": "integer",
                "description": "Maximum allowed payment amount (safety limit)",
            },
        },
        "required": ["resource"],
    }

    async def execute(
        self,
        resource: str,
        amount_usdc: Optional[float] = None,
        amount_atomic: Optional[int] = None,
        memo: Optional[str] = None,
        max_value: Optional[int] = None,
    ) -> dict:
        """
        構建支付表頭

        Args:
            resource: 受保護資源 URL
            amount_usdc: 支付金額 (USDC)
            amount_atomic: 支付金額 (原子單位，優先)
            memo: 支付備註
            max_value: 最大允許金額 (安全上限)

        Returns:
            dict: 包含支付表頭和詳情
        """
        # 驗證輸入
        if not resource:
            return {
                "success": False,
                "error": "Resource URL is required",
            }

        try:
            service = get_x402_service()

            # 構建支付請求
            request = PaymentRequest(
                resource=resource,
                amount_usdc=Decimal(str(amount_usdc)) if amount_usdc else None,
                amount_atomic=amount_atomic,
                memo=memo,
            )

            # 構建支付要求
            requirements = service.build_payment_requirements(request)

            # 構建支付表頭
            header = service.build_payment_header(requirements, max_value=max_value)

            return {
                "success": True,
                "payment_header": header.header_value,
                "payer": header.payer,
                "amount_atomic": header.amount_atomic,
                "requirements": {
                    "scheme": requirements.scheme,
                    "network": requirements.network,
                    "resource": requirements.resource,
                    "pay_to": requirements.pay_to,
                },
            }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to build payment header: {str(e)}",
            }


class X402VerifyPaymentTool(BaseTool):
    """
    X402 支付驗證工具

    驗證 X-PAYMENT 表頭的有效性。
    """

    name: str = "x402_verify_payment"
    description: str = (
        "Verify an X-PAYMENT header for validity. "
        "Returns whether the payment is valid and the payer address."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "payment_header": {
                "type": "string",
                "description": "The X-PAYMENT header value to verify",
            },
        },
        "required": ["payment_header"],
    }

    async def execute(
        self,
        payment_header: str,
    ) -> dict:
        """
        驗證支付表頭

        Args:
            payment_header: X-PAYMENT 表頭值

        Returns:
            dict: 驗證結果
        """
        try:
            service = get_x402_service()
            result = await service.verify_payment(payment_header)

            return {
                "success": True,
                "is_valid": result.is_valid,
                "payer": result.payer,
                "invalid_reason": result.invalid_reason,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to verify payment: {str(e)}",
            }


class X402SettlePaymentTool(BaseTool):
    """
    X402 支付結算工具

    結算已驗證的支付。
    """

    name: str = "x402_settle_payment"
    description: str = (
        "Settle a verified X-PAYMENT. "
        "Returns the transaction hash on success."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "payment_header": {
                "type": "string",
                "description": "The X-PAYMENT header value to settle",
            },
        },
        "required": ["payment_header"],
    }

    async def execute(
        self,
        payment_header: str,
    ) -> dict:
        """
        結算支付

        Args:
            payment_header: X-PAYMENT 表頭值

        Returns:
            dict: 結算結果
        """
        try:
            service = get_x402_service()
            result = await service.settle_payment(payment_header)

            return {
                "success": True,
                "settled": result.success,
                "transaction": result.transaction,
                "network": result.network,
                "payer": result.payer,
                "error_reason": result.error_reason,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to settle payment: {str(e)}",
            }


class X402DecodeReceiptTool(BaseTool):
    """
    X402 收據解碼工具

    解碼 X-PAYMENT-RESPONSE 表頭。
    """

    name: str = "x402_decode_receipt"
    description: str = (
        "Decode an X-PAYMENT-RESPONSE header to extract payment receipt details. "
        "Returns transaction hash, network, and payer information."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "response_header": {
                "type": "string",
                "description": "The X-PAYMENT-RESPONSE header value",
            },
        },
        "required": ["response_header"],
    }

    async def execute(
        self,
        response_header: str,
    ) -> dict:
        """
        解碼支付收據

        Args:
            response_header: X-PAYMENT-RESPONSE 表頭值

        Returns:
            dict: 解碼後的收據
        """
        try:
            service = get_x402_service()
            receipt = service.decode_payment_response(response_header)

            return {
                "success": True,
                "receipt": {
                    "success": receipt.success,
                    "transaction": receipt.transaction,
                    "network": receipt.network,
                    "payer": receipt.payer,
                    "error_reason": receipt.error_reason,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to decode receipt: {str(e)}",
            }
