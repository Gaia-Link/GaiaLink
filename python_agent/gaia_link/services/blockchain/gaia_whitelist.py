"""
GaiaWhitelistService - Real Blockchain Implementation

Interacts with GaiaCharityRegistry smart contract.
"""

import logging
from typing import List, Optional

from gaia_link.services.proposal.models import InstitutionInfo
from gaia_link.services.proposal.base import WhitelistService
from gaia_link.services.blockchain.provider import Web3Provider, get_web3_provider

logger = logging.getLogger(__name__)


class GaiaWhitelistService(WhitelistService):
    """
    Real implementation of WhitelistService using GaiaCharityRegistry contract.

    Provides 2-tier governance:
    - Tier 1: Platform Owner registers charities
    - Tier 2: Charity Admin manages members
    """

    def __init__(self, provider: Optional[Web3Provider] = None):
        self._provider = provider or get_web3_provider()

    @property
    def _contract(self):
        """Get the charity registry contract."""
        return self._provider.get_charity_registry()

    async def is_whitelisted(self, institution_id: str) -> bool:
        """Check if an institution (charity) is active in the registry."""
        try:
            charity_id = int(institution_id)
            name, admin, is_active = self._contract.functions.getCharity(charity_id).call()
            return is_active and admin != "0x" + "0" * 40

        except Exception as e:
            logger.error("[ERROR] Failed to check whitelist for %s: %s", institution_id, e)
            return False

    async def get_institution(self, institution_id: str) -> Optional[InstitutionInfo]:
        """Get institution details from the registry."""
        try:
            charity_id = int(institution_id)
            name, admin, is_active = self._contract.functions.getCharity(charity_id).call()

            # Check if charity exists
            if admin == "0x" + "0" * 40:
                return None

            return InstitutionInfo(
                institution_id=institution_id,
                name=name,
                wallet_address=admin,
                is_verified=is_active,
                description=f"Registered charity (ID: {charity_id})",
            )

        except Exception as e:
            logger.error("[ERROR] Failed to get institution %s: %s", institution_id, e)
            return None

    async def list_institutions(self) -> List[InstitutionInfo]:
        """List all registered charities."""
        institutions = []

        try:
            next_id = self._contract.functions.nextCharityId().call()

            for charity_id in range(1, next_id):  # IDs start at 1
                try:
                    name, admin, is_active = self._contract.functions.getCharity(charity_id).call()

                    # Skip if doesn't exist
                    if admin == "0x" + "0" * 40:
                        continue

                    institutions.append(
                        InstitutionInfo(
                            institution_id=str(charity_id),
                            name=name,
                            wallet_address=admin,
                            is_verified=is_active,
                            description=f"Registered charity (ID: {charity_id})",
                        )
                    )

                except Exception as e:
                    logger.warning("[WARN] Failed to parse charity %d: %s", charity_id, e)

        except Exception as e:
            logger.error("[ERROR] Failed to list institutions: %s", e)

        return institutions

    async def is_member(self, institution_id: str, address: str) -> bool:
        """Check if an address is a member of the charity."""
        try:
            charity_id = int(institution_id)
            checksum_address = self._provider.web3.to_checksum_address(address)

            return self._contract.functions.isMember(charity_id, checksum_address).call()

        except Exception as e:
            logger.error(
                "[ERROR] Failed to check membership for %s in %s: %s",
                address,
                institution_id,
                e,
            )
            return False


# ============================================================================
# Global Service Singleton
# ============================================================================

_gaia_whitelist_service: Optional[GaiaWhitelistService] = None


def get_gaia_whitelist_service() -> GaiaWhitelistService:
    """Get the global GaiaWhitelistService instance."""
    global _gaia_whitelist_service
    if _gaia_whitelist_service is None:
        _gaia_whitelist_service = GaiaWhitelistService()
    return _gaia_whitelist_service
