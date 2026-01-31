"""
Proposal 服務層

提供提案系統的服務抽象，支援 Mock 和 Blockchain 實作切換。

環境變數控制:
- USE_BLOCKCHAIN=true: 使用真實區塊鏈服務
- USE_BLOCKCHAIN=false (默認): 使用 Mock 服務
"""

import os
import logging

from gaia_link.services.proposal.models import (
    ProposalStatus,
    ProposalInfo,
    ContributionInfo,
    InstitutionInfo,
)
from gaia_link.services.proposal.base import (
    ProposalService,
    WhitelistService,
)
from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
from gaia_link.services.proposal.mock_proposal import MockProposalService

logger = logging.getLogger(__name__)

# 服務實例 (延遲初始化)
_proposal_service: ProposalService | None = None
_whitelist_service: WhitelistService | None = None


def _should_use_blockchain() -> bool:
    """檢查是否應該使用區塊鏈服務"""
    use_blockchain = os.getenv("USE_BLOCKCHAIN", "false").lower()
    return use_blockchain in ("true", "1", "yes")


def get_proposal_service() -> ProposalService:
    """
    獲取 ProposalService 實例

    根據 USE_BLOCKCHAIN 環境變數自動選擇:
    - true: 使用 GaiaProposalService (真實區塊鏈)
    - false: 使用 MockProposalService

    Returns:
        ProposalService: 提案服務實例
    """
    global _proposal_service
    if _proposal_service is None:
        if _should_use_blockchain():
            try:
                from gaia_link.services.blockchain.gaia_proposal import GaiaProposalService
                _proposal_service = GaiaProposalService()
                logger.info("[BLOCKCHAIN] Using GaiaProposalService (real contract)")
            except ImportError as e:
                logger.warning("[FALLBACK] web3 not installed, using Mock: %s", e)
                _proposal_service = MockProposalService()
            except Exception as e:
                logger.warning("[FALLBACK] Blockchain init failed, using Mock: %s", e)
                _proposal_service = MockProposalService()
        else:
            _proposal_service = MockProposalService()
            logger.info("[MOCK] Using MockProposalService")
    return _proposal_service


def get_whitelist_service() -> WhitelistService:
    """
    獲取 WhitelistService 實例

    根據 USE_BLOCKCHAIN 環境變數自動選擇:
    - true: 使用 GaiaWhitelistService (真實區塊鏈)
    - false: 使用 MockWhitelistService

    Returns:
        WhitelistService: 白名單服務實例
    """
    global _whitelist_service
    if _whitelist_service is None:
        if _should_use_blockchain():
            try:
                from gaia_link.services.blockchain.gaia_whitelist import GaiaWhitelistService
                _whitelist_service = GaiaWhitelistService()
                logger.info("[BLOCKCHAIN] Using GaiaWhitelistService (real contract)")
            except ImportError as e:
                logger.warning("[FALLBACK] web3 not installed, using Mock: %s", e)
                _whitelist_service = MockWhitelistService()
            except Exception as e:
                logger.warning("[FALLBACK] Blockchain init failed, using Mock: %s", e)
                _whitelist_service = MockWhitelistService()
        else:
            _whitelist_service = MockWhitelistService()
            logger.info("[MOCK] Using MockWhitelistService")
    return _whitelist_service


def set_proposal_service(service: ProposalService) -> None:
    """設置自定義 ProposalService 實例 (用於測試或切換實作)"""
    global _proposal_service
    _proposal_service = service


def set_whitelist_service(service: WhitelistService) -> None:
    """設置自定義 WhitelistService 實例 (用於測試或切換實作)"""
    global _whitelist_service
    _whitelist_service = service


def reset_services() -> None:
    """重置所有服務實例 (用於測試)"""
    global _proposal_service, _whitelist_service
    _proposal_service = None
    _whitelist_service = None


__all__ = [
    # Models
    "ProposalStatus",
    "ProposalInfo",
    "ContributionInfo",
    "InstitutionInfo",
    # Abstract Services
    "ProposalService",
    "WhitelistService",
    # Mock Implementations
    "MockWhitelistService",
    "MockProposalService",
    # Factory Functions
    "get_proposal_service",
    "get_whitelist_service",
    "set_proposal_service",
    "set_whitelist_service",
    "reset_services",
]
