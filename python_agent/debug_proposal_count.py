
import asyncio
import os
from dotenv import load_dotenv

load_dotenv("../.env")
load_dotenv(".env")

from gaia_link.services.blockchain.config import get_blockchain_config, GAIA_PROPOSAL_MANAGER_ABI
from gaia_link.services.blockchain.provider import get_web3_provider

async def main():
    config = get_blockchain_config()
    # Force use of loaded settings
    print(f"RPC URL: {config.rpc_url}")
    print(f"Proposal Manager: {config.addresses.proposal_manager}")
    
    provider = get_web3_provider()
    
    if not provider.is_connected():
        print("ERROR: Not connected to Web3")
        return

    pm = provider.get_proposal_manager()
    
    try:
        next_id = pm.functions.nextProposalId().call()
        print(f"Next Proposal ID: {next_id}")
        
        if next_id > 0:
            print(f"Fetching Proposal #0...")
            data = pm.functions.proposals(0).call()
            print(f"Data: {data}")
        else:
            print("No proposals found.")
            
    except Exception as e:
        print(f"Error querying contract: {e}")

if __name__ == "__main__":
    asyncio.run(main())
