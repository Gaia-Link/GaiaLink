"""
Donation History 服務層

提供捐款歷史查詢的服務抽象，支援 Mock 和真實實作切換。

環境變數控制:
- USE_BLOCKCHAIN=true: 使用真實區塊鏈服務 (未來實現)
- USE_BLOCKCHAIN=false (默認): 使用 Mock 服務
"""

import logging
from typing import Optional

from gaia_link.services.donation_history.models import (
    DonationRecord,
    DonationHistoryResult,
    DonationStatus,
    VaultType,
)
from gaia_link.services.donation_history.base import DonationHistoryService
from gaia_link.services.donation_history.mock_donation_history import (
    MockDonationHistoryService,
)

logger = logging.getLogger(__name__)

# 服務實例 (延遲初始化)
_donation_history_service: Optional[DonationHistoryService] = None


def get_donation_history_service() -> DonationHistoryService:
    """
    獲取 DonationHistoryService 實例

    目前默認使用 MockDonationHistoryService。
    未來可根據環境變數切換到真實區塊鏈查詢服務。

    Returns:
        DonationHistoryService: 捐款歷史服務實例
    """
    global _donation_history_service
    if _donation_history_service is None:
        _donation_history_service = MockDonationHistoryService()
        logger.info("[MOCK] Using MockDonationHistoryService")
    return _donation_history_service


def set_donation_history_service(service: DonationHistoryService) -> None:
    """
    設置自定義 DonationHistoryService 實例

    用於測試或切換實作。

    Args:
        service: 自定義服務實例
    """
    global _donation_history_service
    _donation_history_service = service


def reset_donation_history_service() -> None:
    """
    重置服務實例

    用於測試時重置狀態。
    """
    global _donation_history_service
    _donation_history_service = None


__all__ = [
    # Models
    "DonationRecord",
    "DonationHistoryResult",
    "DonationStatus",
    "VaultType",
    # Abstract Service
    "DonationHistoryService",
    # Mock Implementation
    "MockDonationHistoryService",
    # Factory Functions
    "get_donation_history_service",
    "set_donation_history_service",
    "reset_donation_history_service",
]
