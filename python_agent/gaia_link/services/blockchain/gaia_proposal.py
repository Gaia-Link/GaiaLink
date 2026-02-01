"""
GaiaProposalService - Real Blockchain Implementation

Interacts with GaiaProposalManager smart contract.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from gaia_link.services.proposal.models import (
    ProposalStatus,
    ProposalInfo,
    ContributionInfo,
)
from gaia_link.services.proposal.base import ProposalService
from gaia_link.services.blockchain.provider import Web3Provider, get_web3_provider
from gaia_link.services.blockchain.config import get_blockchain_config

logger = logging.getLogger(__name__)


# Crisis category mapping (matches contract)
CATEGORY_MAP = {
    1: "earthquake",
    2: "flood",
    3: "conflict",
    4: "famine",
    5: "pandemic",
}


class GaiaProposalService(ProposalService):
    """
    Real implementation of ProposalService using GaiaProposalManager contract.

    Maps contract functions to Python service interface.
    """

    def __init__(self, provider: Optional[Web3Provider] = None):
        self._provider = provider or get_web3_provider()
        self._config = get_blockchain_config()

    @property
    def _contract(self):
        """Get the proposal manager contract."""
        return self._provider.get_proposal_manager()

    def _parse_proposal(self, proposal_id: int, data: tuple) -> ProposalInfo:
        """Parse contract proposal data into ProposalInfo."""
        (
            proposer,
            charity_id,
            asset,
            title,
            metadata,
            lat,
            lng,
            category,
            expiry,
            accepted,
            total_direct,
            total_no_loss,
            direct_vault,
            no_loss_vault,
        ) = data

        # Determine status
        now = datetime.now()
        expiry_dt = datetime.fromtimestamp(expiry)

        if accepted:
            status = ProposalStatus.ACTIVATED
        elif now > expiry_dt:
            status = ProposalStatus.EXPIRED
        else:
            status = ProposalStatus.FUNDING

        # Convert lat/lng from scaled int24 to float
        lat_float = lat / 10000.0
        lng_float = lng / 10000.0

        # Get category name
        category_name = CATEGORY_MAP.get(category, "other")

        # Calculate total amount (assuming 18 decimals for now)
        total_wei = total_direct + total_no_loss
        total_amount = total_wei / 1e18  # Convert from wei

        return ProposalInfo(
            proposal_id=str(proposal_id),
            address=self._contract.address, # Manager address as proxy
            creator=proposer,
            institution=str(charity_id), # Using ID as identifier
            institution_name=f"Charity #{charity_id}", # Placeholder, ideal would be to fetch from registry
            title=title,
            description=metadata,  # IPFS CID stored in metadata
            target_amount=0,  # Contract doesn't track target
            total_raised=total_amount,
            status=status,
            deadline=expiry_dt,
            # Optional fields
            location={"lat": lat_float, "lng": lng_float},
            # stored dynamically as extra attributes if model allows, but ProposalInfo has fixed fields
            # We map category/vaults if possible or ignore if not in model
        )

    async def create_proposal(
        self,
        title: str,
        description: str,
        target_amount: float,
        deadline_days: int,
        institution_address: str,
        creator_address: str,
        region: Optional[str] = None,
        # Specialized Gaia parameters as optional kwargs
        **kwargs
    ) -> ProposalInfo:
        """
        Create a new proposal on-chain.
        
        Maps standard ProposalService parameters to Gaia-specific contract call.
        """
        # Get Gaia-specific params from kwargs or defaults
        asset_address = kwargs.get("asset_address") or self._config.addresses.usdc_token
        lat = kwargs.get("lat")
        lng = kwargs.get("lng")
        category = kwargs.get("category", 1) # default to 1 (earthquake)
        """Create a new proposal on-chain."""
        # Get asset address (default to configured USDC)
        asset = asset_address or self._config.addresses.usdc_token
        if not asset:
            raise ValueError("No asset token configured")

        # Convert lat/lng to scaled int24
        lat_scaled = int((lat or 0) * 10000)
        lng_scaled = int((lng or 0) * 10000)

        # Duration in seconds
        duration_seconds = deadline_days * 24 * 60 * 60

        # Build transaction
        tx_func = self._contract.functions.createProposal(
            int(institution_address),  # Gaia uses numeric ID as "address" in this context or it's a mapping issue
            self._provider.web3.to_checksum_address(asset_address),  # asset
            title,  # title
            description,  # metadata (IPFS CID)
            lat_scaled,  # lat
            lng_scaled,  # lng
            category,  # category
            duration_seconds,  # duration
        )

        # Send transaction
        result = self._provider.send_transaction(tx_func)

        if result["status"] != "success":
            raise Exception(f"Transaction failed: {result}")

        # Get the new proposal ID from nextProposalId - 1
        next_id = self._contract.functions.nextProposalId().call()
        proposal_id = next_id - 1

        logger.info("[OK] Proposal created on-chain: ID=%d, tx=%s", proposal_id, result["tx_hash"])

        # Fetch and return the created proposal
        return await self.get_proposal(str(proposal_id))

    async def get_proposal(self, proposal_id: str) -> Optional[ProposalInfo]:
        """Get a proposal by ID from the contract."""
        try:
            pid = int(proposal_id)
            data = self._contract.functions.proposals(pid).call()

            # Check if proposal exists (proposer != zero address)
            if data[0] == "0x" + "0" * 40:
                return None

            return self._parse_proposal(pid, data)

        except Exception as e:
            logger.error("[ERROR] Failed to get proposal %s: %s", proposal_id, e)
            return None

    async def list_proposals(
        self,
        status: Optional[ProposalStatus] = None,
        institution: Optional[str] = None,
        region: Optional[str] = None,
        creator: Optional[str] = None,
        title_query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ProposalInfo]:
        """List all proposals, optionally filtered."""
        proposals = []

        try:
            next_id = self._contract.functions.nextProposalId().call()

            for pid in range(next_id):
                try:
                    data = self._contract.functions.proposals(pid).call()

                    # Skip if proposal doesn't exist
                    if data[0] == "0x" + "0" * 40:
                        continue

                    proposal = self._parse_proposal(pid, data)

                    # Apply filters
                    if status and proposal.status != status:
                        continue
                    if institution and proposal.institution != institution:
                        continue
                    
                    if title_query and title_query.lower() not in proposal.title.lower():
                        continue

                    proposals.append(proposal)

                except Exception as e:
                    logger.warning("[WARN] Failed to parse proposal %d: %s", pid, e)

        except Exception as e:
            logger.error("[ERROR] Failed to list proposals: %s", e)

        return proposals

    async def contribute(
        self,
        proposal_id: str,
        amount: float,
        contributor_address: str,
        **kwargs
    ) -> ContributionInfo:
        """Contribute to a proposal (requires ERC20 approval first)."""
        is_no_loss = kwargs.get("is_no_loss", False)
        pid = int(proposal_id)

        # Convert amount to wei (assuming 18 decimals)
        amount_wei = int(amount * 1e18)

        # First, approve the proposal manager to spend tokens
        asset_address = self._config.addresses.usdc_token
        token = self._provider.get_erc20(asset_address)

        approve_tx = token.functions.approve(
            self._contract.address,
            amount_wei,
        )
        approve_result = self._provider.send_transaction(approve_tx)

        if approve_result["status"] != "success":
            raise Exception(f"Approval failed: {approve_result}")

        # Now deposit
        deposit_tx = self._contract.functions.depositToProposal(
            pid,
            amount_wei,
            is_no_loss,
        )
        result = self._provider.send_transaction(deposit_tx)

        if result["status"] != "success":
            raise Exception(f"Deposit failed: {result}")

        logger.info(
            "[OK] Contribution: %s -> proposal %s (%s), tx=%s",
            contributor_address,
            proposal_id,
            "no-loss" if is_no_loss else "direct",
            result["tx_hash"],
        )

        return ContributionInfo(
            contribution_id=result["tx_hash"],
            proposal_id=proposal_id,
            contributor_address=contributor_address,
            amount=amount,
            contributed_at=datetime.now(),
            is_no_loss=is_no_loss,
        )

    async def withdraw_contribution(
        self,
        proposal_id: str,
        contributor_address: str,
    ) -> bool:
        """Withdraw contribution from a proposal."""
        pid = int(proposal_id)

        tx_func = self._contract.functions.withdrawFromProposal(pid)
        result = self._provider.send_transaction(tx_func)

        if result["status"] != "success":
            logger.error("[ERROR] Withdrawal failed: %s", result)
            return False

        logger.info(
            "[OK] Withdrawal from proposal %s, tx=%s",
            proposal_id,
            result["tx_hash"],
        )
        return True

    async def activate(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> ProposalInfo:
        """Activate proposal (alias for activate_proposal)."""
        success = await self.activate_proposal(proposal_id)
        if not success:
            raise Exception("Failed to activate proposal")
        return await self.get_proposal(proposal_id)

    async def reject(
        self,
        proposal_id: str,
        institution_address: str,
    ) -> ProposalInfo:
        """Reject proposal (Not implemented on contract)."""
        raise NotImplementedError("Reject not supported on blockchain yet")

    async def check_and_update_status(self, proposal_id: str) -> ProposalInfo:
        """Check status (On-chain status is dynamic)."""
        return await self.get_proposal(proposal_id)

    async def withdraw(
        self,
        proposal_id: str,
        contributor_address: str,
    ) -> ContributionInfo:
        """Withdraw contribution (alias for withdraw_contribution)."""
        success = await self.withdraw_contribution(proposal_id, contributor_address)
        if not success:
            raise Exception("Failed to withdraw")
        # Return empty info as it's withdrawn
        return ContributionInfo(
            contribution_id="withdrawn",
            proposal_id=proposal_id,
            contributor_address=contributor_address,
            amount=0,
            contributed_at=datetime.now(),
            is_no_loss=False,
        )

    async def get_contributions(
        self,
        proposal_id: str,
        contributor: Optional[str] = None,
    ) -> List[ContributionInfo]:
        """Get contributions (limited support)."""
        if contributor:
            info = await self.get_contribution(proposal_id, contributor)
            return [info] if info else []
        return [] # Full list not supported without indexer

    async def get_contribution(
        self,
        proposal_id: str,
        contributor_address: str,
    ) -> Optional[ContributionInfo]:
        """Get user's contribution to a proposal."""
        try:
            pid = int(proposal_id)
            address = self._provider.web3.to_checksum_address(contributor_address)

            data = self._contract.functions.userBalances(pid, address).call()
            direct_amount, no_loss_amount = data

            total_wei = direct_amount + no_loss_amount
            if total_wei == 0:
                return None

            return ContributionInfo(
                contribution_id=f"{proposal_id}_{contributor_address}",
                proposal_id=proposal_id,
                contributor_address=contributor_address,
                amount=total_wei / 1e18,
                contributed_at=datetime.now(),  # Contract doesn't store timestamp
                is_no_loss=no_loss_amount > 0,
            )

        except Exception as e:
            logger.error("[ERROR] Failed to get contribution: %s", e)
            return None


# ============================================================================
# Global Service Singleton
# ============================================================================

_gaia_proposal_service: Optional[GaiaProposalService] = None


def get_gaia_proposal_service() -> GaiaProposalService:
    """Get the global GaiaProposalService instance."""
    global _gaia_proposal_service
    if _gaia_proposal_service is None:
        _gaia_proposal_service = GaiaProposalService()
    return _gaia_proposal_service
