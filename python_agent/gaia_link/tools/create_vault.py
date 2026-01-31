"""
create_vault 工具 - 協助機構部署獨立金庫
"""

from typing import Optional
from spoon_ai.tools.base import BaseTool
from gaia_link.services.base import BlockchainService
from gaia_link.config import get_blockchain_service
from gaia_link.services.sepolia_blockchain import GAIA_CONTRACTS, SEPOLIA_TOKEN_CONTRACTS

# createCharityVault(uint256,address,bool) selector
# keccak256("createCharityVault(uint256,address,bool)")
# = 0x2416b772
CREATE_VAULT_SELECTOR = "0x2416b772"

class CreateVaultTool(BaseTool):
    """
    Prepare a transaction for a Charity Admin to deploy a standalone vault.
    Takes charity ID, asset (token), and mode (Direct/NoLoss).
    Returns a transaction payload for signing.
    """

    name: str = "create_vault"
    description: str = (
        "Deploy a new Standalone Vault for a Charity. "
        "Useful for general funds or specific ongoing initiatives without a proposal. "
        "Requires Charity Admin signature."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "charity_id": {
                "type": "integer",
                "description": "ID of the charity (e.g. 1 for Red Cross)"
            },
            "token": {
                "type": "string",
                "enum": ["USDC", "USDT", "ETH", "DAI"],
                "description": "Asset to be managed by the vault"
            },
            "is_no_loss": {
                "type": "boolean",
                "description": "True for Yield-generating (No-Loss) Vault, False for Direct."
            }
        },
        "required": ["charity_id", "token", "is_no_loss"]
    }

    def _encode_create_vault(self, charity_id: int, token_address: str, is_no_loss: bool) -> str:
        """
        Encode createCharityVault(uint256 _charityId, IERC20 _asset, bool _isNoLoss)
        """
        # 1. Charity ID (uint256)
        param_id = hex(charity_id)[2:].zfill(64)
        
        # 2. Asset Address (address)
        clean_addr = token_address.replace("0x", "")
        param_asset = clean_addr.zfill(64)
        
        # 3. isNoLoss (bool -> uint256)
        param_bool = "0000000000000000000000000000000000000000000000000000000000000001" if is_no_loss else "0000000000000000000000000000000000000000000000000000000000000000"

        return f"{CREATE_VAULT_SELECTOR}{param_id}{param_asset}{param_bool}"

    async def execute(self, charity_id: int, token: str, is_no_loss: bool) -> dict:
        # Resolve Token Address
        token_addr = SEPOLIA_TOKEN_CONTRACTS.get(token)
        if not token_addr:
            return {"success": False, "error": f"Unsupported token: {token}"}

        # Encode Data
        calldata = self._encode_create_vault(charity_id, token_addr, is_no_loss)
        
        # Target: ProposalManager
        target = GAIA_CONTRACTS["ProposalManager"]

        vault_type = "No-Loss (Yield)" if is_no_loss else "Direct"

        return {
            "success": True,
            "status": "ready_to_sign",
            "transaction_payload": {
                "to": target,
                "value": "0",
                "data": calldata,
                "chainId": 31337,
                "intent_summary": f"Deploy {vault_type} Vault for Charity #{charity_id} ({token})"
            },
            "ui_hints": {
                # Reuse the existing sign_transaction action type in frontend
                "actions": [
                    {
                        "label": "Deploy Vault",
                        "type": "sign_transaction", 
                        "data": None # The backend will inject payload into the response root usually, or we pass it here?
                        # Wait, agentService.ts maps response.transaction_payload to action data usually.
                        # Let's check SpoonOSInterface or AgentService.
                    }
                ],
                "mode": "SIGNATURE"
            },
            "message": f"Ready to deploy a {vault_type} Vault for Charity ID {charity_id}. Please sign the transaction."
        }
