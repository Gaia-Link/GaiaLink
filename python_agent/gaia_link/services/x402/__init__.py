"""
X402 支付服務模組

提供 HTTP 402 Payment Required 支付功能。
"""

from .models import (
    PaymentStatus,
    PaymentRequirements,
    PaymentRequest,
    PaymentHeader,
    VerifyResult,
    SettleResult,
    PaymentReceipt,
    X402Config,
)
from .base import X402Service

# 服務實例快取
_x402_service: X402Service | None = None


def get_x402_service() -> X402Service:
    """
    獲取 X402 服務實例

    根據環境變數 X402_ENABLED 決定使用哪個實作:
    - False/未設定: MockX402Service
    - True: GaiaX402Service (需要 spoon-core)

    Returns:
        X402Service: 服務實例
    """
    global _x402_service
    if _x402_service is None:
        import os

        if os.getenv("X402_ENABLED", "false").lower() == "true":
            from .gaia_x402 import GaiaX402Service

            _x402_service = GaiaX402Service()
        else:
            from .mock_x402 import MockX402Service

            _x402_service = MockX402Service()
    return _x402_service


def set_x402_service(service: X402Service) -> None:
    """設置 X402 服務實例 (用於測試)"""
    global _x402_service
    _x402_service = service


def reset_x402_service() -> None:
    """重置服務實例"""
    global _x402_service
    _x402_service = None


__all__ = [
    # 模型
    "PaymentStatus",
    "PaymentRequirements",
    "PaymentRequest",
    "PaymentHeader",
    "VerifyResult",
    "SettleResult",
    "PaymentReceipt",
    "X402Config",
    # 服務
    "X402Service",
    # 工廠函數
    "get_x402_service",
    "set_x402_service",
    "reset_x402_service",
]
