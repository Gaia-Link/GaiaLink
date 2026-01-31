"""
Gaia Link Services - 外部服務抽象層

提供可替換的服務實作，支援 Mock 和真實服務切換
"""

# Blockchain 服務
from gaia_link.services.base import BlockchainService, TransactionResult
from gaia_link.services.mock_blockchain import MockBlockchainService

# Polymarket 服務
from gaia_link.services.polymarket import (
    PolymarketService,
    MarketData,
    CrisisSearchResult,
    MockPolymarketService,
)

# Sentiment 服務
from gaia_link.services.sentiment import (
    SentimentService,
    SentimentResult,
    AnalysisContext,
    UrgencyLevel,
    MockSentimentService,
)

# Rate Limiting 服務
from gaia_link.services.ratelimit import (
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStatus,
    InMemoryRateLimiter,
    get_in_memory_rate_limiter,
)

# Audit Logging 服務
from gaia_link.services.audit import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditLevel,
    AuditQuery,
    InMemoryAuditLogger,
    get_in_memory_audit_logger,
)

# Proposal Service (V2)
from gaia_link.services.proposal import (
    ProposalStatus,
    ProposalInfo,
    ContributionInfo,
    InstitutionInfo,
    ProposalService,
    WhitelistService,
    MockProposalService,
    MockWhitelistService,
    get_proposal_service,
    get_whitelist_service,
    set_proposal_service,
    set_whitelist_service,
    reset_services as reset_proposal_services,
)

# X402 Payment Service (V2)
from gaia_link.services.x402 import (
    PaymentStatus,
    PaymentRequirements,
    PaymentRequest,
    PaymentHeader,
    VerifyResult,
    SettleResult,
    PaymentReceipt,
    X402Config,
    X402Service,
    get_x402_service,
    set_x402_service,
    reset_x402_service,
)

# Donation History Service (V2)
from gaia_link.services.donation_history import (
    DonationRecord,
    DonationHistoryResult,
    DonationStatus,
    VaultType,
    DonationHistoryService,
    MockDonationHistoryService,
    get_donation_history_service,
    set_donation_history_service,
    reset_donation_history_service,
)

# Pool Service (V2 - Phase 4)
from gaia_link.services.pool import (
    VaultType as PoolVaultType,
    CreatorType,
    RecommendationPriority,
    PoolInfo,
    PoolListResult,
    PoolRecommendation,
    YieldInfo,
    PoolService,
    MockPoolService,
    get_pool_service,
    set_pool_service,
    reset_pool_service,
)


# SepoliaBlockchainService 需要 web3 依賴，延遲導入
def get_sepolia_service(*args, **kwargs):
    """工廠函數：創建 SepoliaBlockchainService 實例"""
    from gaia_link.services.sepolia_blockchain import SepoliaBlockchainService

    return SepoliaBlockchainService(*args, **kwargs)


# RealPolymarketService 需要 aiohttp，延遲導入
def get_real_polymarket_service(*args, **kwargs):
    """工廠函數：創建 RealPolymarketService 實例"""
    from gaia_link.services.polymarket import (
        get_real_polymarket_service as _get_real,
    )

    return _get_real(*args, **kwargs)


# HuggingFaceSentimentService 需要 transformers，延遲導入
def get_huggingface_sentiment_service(*args, **kwargs):
    """工廠函數：創建 HuggingFaceSentimentService 實例"""
    from gaia_link.services.sentiment import (
        get_huggingface_sentiment_service as _get_hf,
    )

    return _get_hf(*args, **kwargs)


# =============================================================================
# Blockchain Integration (Web3) - 延遲導入
# =============================================================================


def get_gaia_proposal_service(*args, **kwargs):
    """工廠函數：創建 GaiaProposalService 實例 (真實區塊鏈)"""
    from gaia_link.services.blockchain.gaia_proposal import GaiaProposalService

    return GaiaProposalService(*args, **kwargs)


def get_gaia_whitelist_service(*args, **kwargs):
    """工廠函數：創建 GaiaWhitelistService 實例 (真實區塊鏈)"""
    from gaia_link.services.blockchain.gaia_whitelist import GaiaWhitelistService

    return GaiaWhitelistService(*args, **kwargs)


def get_web3_provider(*args, **kwargs):
    """工廠函數：創建 Web3Provider 實例"""
    from gaia_link.services.blockchain.provider import Web3Provider

    return Web3Provider(*args, **kwargs)


__all__ = [
    # Blockchain
    "BlockchainService",
    "TransactionResult",
    "MockBlockchainService",
    "get_sepolia_service",
    # Polymarket
    "PolymarketService",
    "MarketData",
    "CrisisSearchResult",
    "MockPolymarketService",
    "get_real_polymarket_service",
    # Sentiment
    "SentimentService",
    "SentimentResult",
    "AnalysisContext",
    "UrgencyLevel",
    "MockSentimentService",
    "get_huggingface_sentiment_service",
    # Rate Limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitStatus",
    "InMemoryRateLimiter",
    "get_in_memory_rate_limiter",
    # Audit Logging
    "AuditLogger",
    "AuditEntry",
    "AuditEventType",
    "AuditLevel",
    "AuditQuery",
    "InMemoryAuditLogger",
    "get_in_memory_audit_logger",
    # Proposal Service (V2)
    "ProposalStatus",
    "ProposalInfo",
    "ContributionInfo",
    "InstitutionInfo",
    "ProposalService",
    "WhitelistService",
    "MockProposalService",
    "MockWhitelistService",
    "get_proposal_service",
    "get_whitelist_service",
    "set_proposal_service",
    "set_whitelist_service",
    "reset_proposal_services",
    # X402 Payment Service (V2)
    "PaymentStatus",
    "PaymentRequirements",
    "PaymentRequest",
    "PaymentHeader",
    "VerifyResult",
    "SettleResult",
    "PaymentReceipt",
    "X402Config",
    "X402Service",
    "get_x402_service",
    "set_x402_service",
    "reset_x402_service",
    # Donation History Service (V2)
    "DonationRecord",
    "DonationHistoryResult",
    "DonationStatus",
    "VaultType",
    "DonationHistoryService",
    "MockDonationHistoryService",
    "get_donation_history_service",
    "set_donation_history_service",
    "reset_donation_history_service",
    # Blockchain Integration (V2)
    "get_gaia_proposal_service",
    "get_gaia_whitelist_service",
    "get_web3_provider",
    # Pool Service (V2 - Phase 4)
    "PoolVaultType",
    "CreatorType",
    "RecommendationPriority",
    "PoolInfo",
    "PoolListResult",
    "PoolRecommendation",
    "YieldInfo",
    "PoolService",
    "MockPoolService",
    "get_pool_service",
    "set_pool_service",
    "reset_pool_service",
]
