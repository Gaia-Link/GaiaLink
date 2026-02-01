import asyncio
import sys
import os

# Add the python_agent directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'python_agent'))

from gaia_link.service import GaiaLinkService
from gaia_link.services.blockchain.config import get_blockchain_config

async def test_donation_by_name():
    # Set environment variables for the test
    os.environ["USE_BLOCKCHAIN"] = "true"
    os.environ["BLOCKCHAIN_NETWORK"] = "anvil"
    
    service = GaiaLinkService()
    
    # Test message
    message = "幫我向Amazon Rainforest Conservation直接捐1usdc"
    print(f"\n[TEST] Processing message: {message}")
    
    response = await service.process_message(message)
    
    # Internal debugging info
    ext_amount = service._extract_amount_from_message(message)
    ext_token = service._extract_token_from_message(message)
    ext_id = service._extract_proposal_id_from_message(message)
    ext_name = service._extract_proposal_name_from_message(message)
    
    print(f"\n[DEBUG] Extracted: Amount={ext_amount}, Token={ext_token}, ID={ext_id}, Name={ext_name}")
    
    # Check what's in the blockchain
    from gaia_link.services.proposal import get_proposal_service
    prop_service = get_proposal_service()
    all_props = await prop_service.list_proposals()
    print(f"[DEBUG] Blockchain Proposals Count: {len(all_props)}")
    if all_props:
        print(f"[DEBUG] First few proposals: {[p.title for p in all_props[:3]]}")
        match = await prop_service.list_proposals(title_query="Amazon")
        print(f"[DEBUG] Search 'Amazon' results: {[p.title for p in match]}")

    print("\n--- Response ---")
    print(f"Message: {response.message}")
    print(f"Action: {response.action_taken}")
    print(f"UI Hints: {response.ui_hints}")
    
    if response.transaction_sequence:
        print("\n--- Transaction Sequence ---")
        for i, tx in enumerate(response.transaction_sequence):
            print(f"[{i}] {tx.get('label', 'Unnamed Step')}")
            print(f"    To: {tx.get('to')}")
            print(f"    Data: {tx.get('data')[:66]}...")
            
    if response.transaction_payload:
        payload = response.transaction_payload
        print("\n--- Current Transaction Payload (First Step) ---")
        print(f"To: {payload.get('to')}")
        print(f"Data: {payload.get('data')[:66]}...")
        print(f"ChainID: {payload.get('chainId')}")
        print(f"Intent: {payload.get('intent_summary')}")
        
        # Check if Proposal ID 13 is in the sequence's second step or current payload
        # Since USDC donation now puts DEPOSIT in sequence[1]
        data_to_check = payload.get('data')
        if response.transaction_sequence and len(response.transaction_sequence) > 1:
            data_to_check = response.transaction_sequence[1].get('data')

        if "0000000000000000000000000000000d" in data_to_check:
            print("\n[SUCCESS] Successfully resolved 'Amazon Rainforest Conservation' to Proposal ID 13!")
        else:
            print("\n[WARNING] Could not find Proposal ID 13 (0xd) in expected payload data.")
    else:
        print("\n[FAILED] No transaction payload generated.")

if __name__ == "__main__":
    asyncio.run(test_donation_by_name())
