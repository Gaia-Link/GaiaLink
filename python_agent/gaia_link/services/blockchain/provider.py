"""
Web3 Provider

Manages Web3 connection and contract instances.
"""

import logging
from typing import Any, Optional

from gaia_link.services.blockchain.config import (
    BlockchainConfig,
    get_blockchain_config,
    GAIA_CHARITY_REGISTRY_ABI,
    GAIA_PROPOSAL_MANAGER_ABI,
    ERC20_ABI,
)

logger = logging.getLogger(__name__)


class Web3Provider:
    """
    Web3 connection provider with contract instances.

    Handles:
    - Web3 connection management
    - Contract instance creation
    - Transaction signing and sending
    """

    def __init__(self, config: Optional[BlockchainConfig] = None):
        self._config = config or get_blockchain_config()
        self._web3: Any = None
        self._account: Any = None
        self._contracts: dict = {}

    @property
    def web3(self) -> Any:
        """Get Web3 instance, initializing if needed."""
        if self._web3 is None:
            self._initialize_web3()
        return self._web3

    @property
    def account(self) -> Any:
        """Get the configured account for signing."""
        if self._account is None and self._config.private_key:
            self._initialize_account()
        return self._account

    @property
    def account_address(self) -> Optional[str]:
        """Get the account address."""
        if self.account:
            return self.account.address
        return None

    def _initialize_web3(self) -> None:
        """Initialize Web3 connection."""
        try:
            from web3 import Web3
            from web3.middleware import ExtraDataToPOAMiddleware

            self._web3 = Web3(Web3.HTTPProvider(self._config.rpc_url))

            # Add PoA middleware for testnets
            self._web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            if self._web3.is_connected():
                logger.info(
                    "[OK] Web3 connected to %s (Chain ID: %s)",
                    self._config.rpc_url,
                    self._web3.eth.chain_id,
                )
            else:
                logger.warning("[WARN] Web3 connection failed")

        except ImportError:
            logger.error("[ERROR] web3 package not installed. Run: pip install web3")
            raise

    def _initialize_account(self) -> None:
        """Initialize account from private key."""
        if not self._config.private_key:
            return

        try:
            from eth_account import Account

            # Handle private key with or without 0x prefix
            pk = self._config.private_key
            if not pk.startswith("0x"):
                pk = "0x" + pk

            self._account = Account.from_key(pk)
            logger.info("[OK] Account initialized: %s", self._account.address)

        except Exception as e:
            logger.error("[ERROR] Failed to initialize account: %s", e)

    def is_connected(self) -> bool:
        """Check if Web3 is connected."""
        try:
            return self.web3.is_connected()
        except Exception:
            return False

    def get_charity_registry(self) -> Any:
        """Get GaiaCharityRegistry contract instance."""
        if "charity_registry" not in self._contracts:
            address = self._config.addresses.charity_registry
            if not address:
                raise ValueError("CHARITY_REGISTRY_ADDRESS not configured")

            self._contracts["charity_registry"] = self.web3.eth.contract(
                address=self.web3.to_checksum_address(address),
                abi=GAIA_CHARITY_REGISTRY_ABI,
            )
        return self._contracts["charity_registry"]

    def get_proposal_manager(self) -> Any:
        """Get GaiaProposalManager contract instance."""
        if "proposal_manager" not in self._contracts:
            address = self._config.addresses.proposal_manager
            if not address:
                raise ValueError("PROPOSAL_MANAGER_ADDRESS not configured")

            self._contracts["proposal_manager"] = self.web3.eth.contract(
                address=self.web3.to_checksum_address(address),
                abi=GAIA_PROPOSAL_MANAGER_ABI,
            )
        return self._contracts["proposal_manager"]

    def get_erc20(self, token_address: str) -> Any:
        """Get ERC20 token contract instance."""
        key = f"erc20_{token_address.lower()}"
        if key not in self._contracts:
            self._contracts[key] = self.web3.eth.contract(
                address=self.web3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
        return self._contracts[key]

    def send_transaction(self, tx_func: Any, value: int = 0) -> dict:
        """
        Build, sign, and send a transaction.

        Args:
            tx_func: Contract function to call
            value: ETH value to send (in wei)

        Returns:
            Transaction receipt dict
        """
        if not self.account:
            raise ValueError("No account configured for signing")

        # Build transaction
        tx = tx_func.build_transaction(
            {
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "gas": self._config.gas_limit,
                "value": value,
                "chainId": self._config.chain_id,
            }
        )

        # Add EIP-1559 gas settings if configured
        if self._config.max_fee_per_gas:
            tx["maxFeePerGas"] = self._config.max_fee_per_gas
            tx["maxPriorityFeePerGas"] = (
                self._config.max_priority_fee or self._config.max_fee_per_gas // 10
            )
        else:
            # Use legacy gas price
            tx["gasPrice"] = self.web3.eth.gas_price

        # Sign and send
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        logger.info(
            "[OK] Transaction sent: %s (status: %s)",
            tx_hash.hex(),
            "success" if receipt["status"] == 1 else "failed",
        )

        return {
            "tx_hash": tx_hash.hex(),
            "status": "success" if receipt["status"] == 1 else "failed",
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
        }


# ============================================================================
# Global Provider Singleton
# ============================================================================

_web3_provider: Optional[Web3Provider] = None


def get_web3_provider() -> Web3Provider:
    """Get the global Web3 provider instance."""
    global _web3_provider
    if _web3_provider is None:
        _web3_provider = Web3Provider()
    return _web3_provider
