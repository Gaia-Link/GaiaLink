"""
GaiaDonationHistoryService - Real Blockchain Implementation

Interacts with GaiaProposalManager smart contract to fetch user portfolio.
"""

import logging
from datetime import datetime
from typing import List, Optional

from gaia_link.services.donation_history.models import (
    DonationRecord,
    DonationHistoryResult,
    DonationStatus,
    VaultType,
)
from gaia_link.services.donation_history.base import DonationHistoryService
from gaia_link.services.blockchain.provider import Web3Provider, get_web3_provider
from gaia_link.services.blockchain.config import get_blockchain_config

logger = logging.getLogger(__name__)


class GaiaDonationHistoryService(DonationHistoryService):
    """
    Real implementation of DonationHistoryService using GaiaProposalManager contract.
    """

    def __init__(self, provider: Optional[Web3Provider] = None):
        self._provider = provider or get_web3_provider()
        self._config = get_blockchain_config()

    @property
    def _contract(self):
        """Get the proposal manager contract."""
        return self._provider.get_proposal_manager()

    async def get_donation_history(
        self,
        wallet_address: str,
        limit: int = 10,
        offset: int = 0
    ) -> DonationHistoryResult:
        """
        Get donation history for a wallet address from blockchain.
        """
        records = []
        
        try:
            # Validate address
            if not wallet_address:
                 return DonationHistoryResult(
                    records=[],
                    total_count=0,
                    wallet_address=wallet_address
                )
                
            checksum_address = self._provider.web3.to_checksum_address(wallet_address)
            
            # Call getUserPortfolio
            # Returns tuple array: [(proposalId, directAmount, noLossAmount), ...]
            data = self._contract.functions.getUserPortfolio(checksum_address).call()
            
            # Parse results
            for item in data:
                proposal_id = str(item[0]) # proposalId
                direct_amount_wei = item[1] # directAmount
                no_loss_amount_wei = item[2] # noLossAmount
                
                # Direct Donation
                if direct_amount_wei > 0:
                    records.append(DonationRecord(
                        id=f"{proposal_id}_direct", # Composite ID since we don't have tx hash here without indexing
                        amount=direct_amount_wei / 1e18,
                        currency="USDC", # Assuming USDC
                        proposal_id=proposal_id,
                        proposal_title=f"Proposal #{proposal_id}", # We could fetch title if needed, but keeping it simple
                        timestamp=datetime.now(), # Contract doesn't store timestamp info in this view
                        status=DonationStatus.COMPLETED,
                        vault_type=VaultType.DIRECT,
                        tx_hash=None
                    ))
                
                # No Loss Donation (Yield)
                if no_loss_amount_wei > 0:
                     records.append(DonationRecord(
                        id=f"{proposal_id}_noloss",
                        amount=no_loss_amount_wei / 1e18,
                        currency="USDC",
                        proposal_id=proposal_id,
                        proposal_title=f"Proposal #{proposal_id}",
                        timestamp=datetime.now(),
                        status=DonationStatus.ACTIVE, # No-loss implies active deposit
                        vault_type=VaultType.YIELD,
                        tx_hash=None
                    ))
            
            # Sort / Pagination (Local)
            total_count = len(records)
            # Reverse to show newest (by ID/implicit order) first? 
            # Proposals are usually ordered by ID.
            records.sort(key=lambda x: int(x.proposal_id), reverse=True)
            
            paginated_records = records[offset : offset + limit]

            return DonationHistoryResult(
                records=paginated_records,
                total_count=total_count,
                wallet_address=wallet_address
            )

        except Exception as e:
            logger.error(f"[ERROR] Failed to fetch on-chain history for {wallet_address}: {e}")
            # Fallback to empty
            return DonationHistoryResult(
                records=[],
                total_count=0,
                wallet_address=wallet_address,
                error=str(e)
            )
