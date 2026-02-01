"""
Blockchain Configuration

Contract addresses, ABIs, and network settings.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

# ============================================================================
# Contract ABIs (Minimal - only functions we need)
# ============================================================================

GAIA_CHARITY_REGISTRY_ABI = [
    # View Functions
    {
        "inputs": [{"name": "_charityId", "type": "uint256"}],
        "name": "getCharity",
        "outputs": [
            {"name": "name", "type": "string"},
            {"name": "admin", "type": "address"},
            {"name": "isActive", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "_charityId", "type": "uint256"},
            {"name": "_account", "type": "address"},
        ],
        "name": "isMember",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "nextCharityId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "charityId", "type": "uint256"},
            {"indexed": False, "name": "name", "type": "string"},
            {"indexed": True, "name": "admin", "type": "address"},
        ],
        "name": "CharityRegistered",
        "type": "event",
    },
]

GAIA_PROPOSAL_MANAGER_ABI = [
    # View Functions
    {
        "inputs": [{"name": "", "type": "uint256"}],
        "name": "proposals",
        "outputs": [
            {"name": "proposer", "type": "address"},
            {"name": "charityId", "type": "uint256"},
            {"name": "asset", "type": "address"},
            {"name": "title", "type": "string"},
            {"name": "metadata", "type": "string"},
            {"name": "lat", "type": "int24"},
            {"name": "lng", "type": "int24"},
            {"name": "category", "type": "uint8"},
            {"name": "expiry", "type": "uint256"},
            {"name": "accepted", "type": "bool"},
            {"name": "totalDirect", "type": "uint256"},
            {"name": "totalNoLoss", "type": "uint256"},
            {"name": "directVault", "type": "address"},
            {"name": "noLossVault", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "", "type": "uint256"},
            {"name": "", "type": "address"},
        ],
        "name": "userBalances",
        "outputs": [
            {"name": "directAmount", "type": "uint256"},
            {"name": "noLossAmount", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "_user", "type": "address"}],
        "name": "getUserPortfolio",
        "outputs": [
            {
                "components": [
                    {"name": "proposalId", "type": "uint256"},
                    {"name": "directAmount", "type": "uint256"},
                    {"name": "noLossAmount", "type": "uint256"},
                ],
                "name": "",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "nextProposalId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # Write Functions
    {
        "inputs": [
            {"name": "_charityId", "type": "uint256"},
            {"name": "_asset", "type": "address"},
            {"name": "_title", "type": "string"},
            {"name": "_metadata", "type": "string"},
            {"name": "_lat", "type": "int24"},
            {"name": "_lng", "type": "int24"},
            {"name": "_category", "type": "uint8"},
            {"name": "_duration", "type": "uint256"},
        ],
        "name": "createProposal",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "_proposalId", "type": "uint256"},
            {"name": "_amount", "type": "uint256"},
            {"name": "_isNoLoss", "type": "bool"},
        ],
        "name": "depositToProposal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "_proposalId", "type": "uint256"}],
        "name": "acceptProposal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "_proposalId", "type": "uint256"}],
        "name": "withdrawFromProposal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "proposalId", "type": "uint256"},
            {"indexed": False, "name": "title", "type": "string"},
            {"indexed": True, "name": "charityId", "type": "uint256"},
            {"indexed": False, "name": "lat", "type": "int24"},
            {"indexed": False, "name": "lng", "type": "int24"},
            {"indexed": False, "name": "category", "type": "uint8"},
        ],
        "name": "ProposalCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "proposalId", "type": "uint256"},
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "isNoLoss", "type": "bool"},
        ],
        "name": "FundsDeposited",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "proposalId", "type": "uint256"},
            {"indexed": False, "name": "directVault", "type": "address"},
            {"indexed": False, "name": "noLossVault", "type": "address"},
        ],
        "name": "ProposalAccepted",
        "type": "event",
    },
]

ERC20_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
        "constant": True
    },
]


# ============================================================================
# Configuration Classes
# ============================================================================


@dataclass
class ContractAddresses:
    """Contract addresses for a specific network."""

    charity_registry: str = ""
    proposal_manager: str = ""
    usdc_token: str = ""


@dataclass
class BlockchainConfig:
    """Blockchain connection configuration."""

    # Network
    rpc_url: str = ""
    chain_id: int = 1  # Default Ethereum Mainnet

    # Contracts
    addresses: ContractAddresses = field(default_factory=ContractAddresses)

    # Account (for signing transactions)
    private_key: Optional[str] = None

    # Gas settings
    gas_limit: int = 500000
    max_fee_per_gas: Optional[int] = None  # Wei
    max_priority_fee: Optional[int] = None  # Wei

    @classmethod
    def from_env(cls) -> "BlockchainConfig":
        """Load configuration from environment variables."""
        charity_registry = os.getenv("CHARITY_REGISTRY_ADDRESS", "")
        proposal_manager = os.getenv("PROPOSAL_MANAGER_ADDRESS", "")
        usdc_token = os.getenv("USDC_TOKEN_ADDRESS", "")
        
        print(f"--- Config: Loading from ENV ---")
        print(f"--- Config: ProposalManager: {proposal_manager}")
        print(f"--- Config: CharityRegistry: {charity_registry}")
        print(f"--- Config: USDC Token: {usdc_token}")

        return cls(
            rpc_url=os.getenv("RPC_URL", "http://127.0.0.1:8545"),
            chain_id=int(os.getenv("CHAIN_ID", "31337")),  # Anvil default
            addresses=ContractAddresses(
                charity_registry=charity_registry,
                proposal_manager=proposal_manager,
                usdc_token=usdc_token,
            ),
            private_key=os.getenv("WALLET_PRIVATE_KEY"),
            gas_limit=int(os.getenv("GAS_LIMIT", "500000")),
        )

    def is_valid(self) -> bool:
        """Check if configuration is valid for blockchain operations."""
        return bool(
            self.rpc_url
            and self.addresses.charity_registry
            and self.addresses.proposal_manager
        )


# ============================================================================
# Global Config Singleton
# ============================================================================

_blockchain_config: Optional[BlockchainConfig] = None


def get_blockchain_config() -> BlockchainConfig:
    """Get the current blockchain configuration."""
    global _blockchain_config
    if _blockchain_config is None:
        _blockchain_config = BlockchainConfig.from_env()
    return _blockchain_config


def set_blockchain_config(config: BlockchainConfig) -> None:
    """Set the blockchain configuration."""
    global _blockchain_config
    _blockchain_config = config
