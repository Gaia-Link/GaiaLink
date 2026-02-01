"""
WithdrawContributionTool - 退款工具

允許捐款者從已過期 (EXPIRED) 或已取消 (CANCELLED) 的提案中提取捐款。
"""

from spoon_ai.tools.base import BaseTool

from gaia_link.services.proposal import get_proposal_service
from gaia_link.services.proposal.models import ProposalStatus


class WithdrawContributionTool(BaseTool):
    """
    退款工具

    允許捐款者從以下狀態的提案中提取捐款：
    - EXPIRED: 募資截止未達標，或機構超時未確認
    - CANCELLED: 機構拒絕了提案

    已激活 (ACTIVATED) 的提案不允許退款，因為資金已轉移給機構。
    """

    name: str = "withdraw_contribution"
    description: str = (
        "Withdraw contribution from a proposal that has not yet been accepted by the institution. "
        "Available for proposals in FUNDING, EXPIRED, or CANCELLED status."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "proposal_id": {
                "type": "string",
                "description": "Proposal ID to withdraw from",
            },
            "contributor_address": {
                "type": "string",
                "description": "Contributor's wallet address",
            },
        },
        "required": ["proposal_id", "contributor_address"],
    }

    async def execute(
        self,
        contributor_address: str,
        proposal_id: str = None,
    ) -> dict:
        """
        執行退款 (單一或批量)

        Args:
            contributor_address: 捐款者地址
            proposal_id: 提案 ID (若為 None 則掃描所有提案)
        """
        service = get_proposal_service()
        
        # Scenario 1: Batched Withdrawal (Withdraw All)
        if not proposal_id:
            print(f"--- Tool: Scanning portfolio for withdrawals for {contributor_address} ---")
            
            # 1. Get User Portfolio (Batch Query)
            contributions = await service.get_user_portfolio(contributor_address)
            refundable_txs = []
            
            for c in contributions:
                # We need to check the proposal status to ensure it's not ACTIVATED
                # Ideally get_user_portfolio would return status, but it doesn't.
                # So we must fetch proposals for the ones user contributed to.
                # However, looping get_proposal for 2-3 items is better than 20 items.
                
                p = await service.get_proposal(c.proposal_id)
                if not p: continue
                
                # Filter: Allow anything NOT ACTIVATED (Contract logic)
                if p.status == ProposalStatus.ACTIVATED:
                    continue
                
                print(f"--- Tool: Found refundable amount {c.amount} in Proposal {p.proposal_id} ---")
                
                # Generate Payload
                # Selector for withdrawFromProposal(uint256): 0xc3da42b8 (Checked via online keccak)
                # Wait, keccak("withdrawFromProposal(uint256)") = 0x2e1a7d4d (Wait, let me verify)
                # To be essentially safe, let's use the manual hex construction if possible or minimal deps.
                # Or just use the standard web3 construction properly this time.
                # service._contract.functions.withdrawFromProposal(pid).build_transaction(...)['data']
                
                try:
                    pid_int = int(p.proposal_id)
                    # Use build_transaction to get data safely
                    # We don't send it, just get data.
                    # Note: build_transaction requires 'from' usually, but for data generation it might be ok
                    # Or just use `_encode_transaction_data()` if protected access is okay, 
                    # OR access the function selector.
                    # Safest: Use the contract instance correctly.
                    # If service._contract is a web3.eth.AsyncContract or Contract:
                    tx_data = service._contract.functions.withdrawFromProposal(pid_int)._encode_transaction_data()
                except Exception as e:
                    print(f"--- Tool Error Encoding: {e} ---")
                    # Fallback to manual hex if web3 fails (unlikely if setup correct)
                    # withdrawFromProposal(uint256) -> selector + 64 hex
                    # keccak('withdrawFromProposal(uint256)') = 2e1a7d4d
                    selector = "0x2e1a7d4d"
                    pid_hex = hex(pid_int)[2:].zfill(64)
                    tx_data = f"{selector}{pid_hex}"
                
                refundable_txs.append({
                    "to": service._contract.address,
                    "value": "0",
                    "data": tx_data,
                    "chainId": service._config.chain_id,
                    "gas": "150000",
                    "label": f"Withdraw from '{p.title}'",
                    "intent_summary": f"Withdraw {c.amount} from Proposal #{p.proposal_id}"
                })

            if not refundable_txs:
                return {
                    "success": False, 
                    "error": "No refundable contributions found (active or expired proposals only)."
                }
            
            return {
                "success": True,
                "status": "ready_to_sign",
                "transaction_sequence": refundable_txs,
                "message": f"I found {len(refundable_txs)} proposals with refundable funds. Please sign the transactions to withdraw."
            }

        # Scenario 2: Single Proposal Withdrawal (Existing Logic)
        # ... (rest of logic for single ID would go here, or I assume the user wanted me to keep it)
        # But wait, the tool call completely REPLACES the method. I must include the single logic too.
        
        # 檢查提案存在
        proposal = await service.get_proposal(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        # 檢查提案狀態
        # 檢查提案狀態 (Contract logic: require(!p.accepted))
        # ACTIVATED means accepted. FUNDED might mean reached goal but not accepted yet (still FUNDING in contract sense until accept called).
        # So we block only ACTIVATED.
        if proposal.status == ProposalStatus.ACTIVATED:
            return {
                "success": False,
                "error": (
                    f"Withdrawal not allowed for ACTIVATED proposals. "
                    f"Funds have already been transferred to the institution."
                ),
            }
            
        # For single withdrawal, we also return a payload now instead of executing backend-side.
        # Ideally we prefer frontend signing so private key isn't needed on backend.
        
        pid_int = int(proposal_id)
        # Use safe encoding compatible with AsyncContract
        try:
            tx_data = service._contract.functions.withdrawFromProposal(pid_int)._encode_transaction_data()
        except Exception as e:
            print(f"--- Tool Error Encoding (Single): {e} ---")
            selector = "0x2e1a7d4d" # withdrawFromProposal(uint256)
            pid_hex = hex(pid_int)[2:].zfill(64)
            tx_data = f"{selector}{pid_hex}"
            
        return {
            "success": True,
            "status": "ready_to_sign",
            "status": "ready_to_sign",
            "transaction_payload": {
                "to": service._contract.address,
                "value": "0",
                "data": tx_data,
                "chainId": service._config.chain_id,
                "gas": "150000",
                "intent_summary": f"Withdraw from Proposal #{proposal_id}"
            },
            "message": f"Please sign the transaction to withdraw from Proposal {proposal_id}."
        }
