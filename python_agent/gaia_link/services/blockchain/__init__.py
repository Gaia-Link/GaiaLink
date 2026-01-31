"""
GaiaLink Blockchain Integration Module

Provides Web3 connectivity and real smart contract interactions.
"""

from gaia_link.services.blockchain.config import (
    BlockchainConfig,
    ContractAddresses,
    get_blockchain_config,
    set_blockchain_config,
)
from gaia_link.services.blockchain.provider import (
    Web3Provider,
    get_web3_provider,
)
from gaia_link.services.blockchain.gaia_proposal import (
    GaiaProposalService,
    get_gaia_proposal_service,
)
from gaia_link.services.blockchain.gaia_whitelist import (
    GaiaWhitelistService,
    get_gaia_whitelist_service,
)

__all__ = [
    # Config
    "BlockchainConfig",
    "ContractAddresses",
    "get_blockchain_config",
    "set_blockchain_config",
    # Provider
    "Web3Provider",
    "get_web3_provider",
    # Services
    "GaiaProposalService",
    "get_gaia_proposal_service",
    "GaiaWhitelistService",
    "get_gaia_whitelist_service",
]
