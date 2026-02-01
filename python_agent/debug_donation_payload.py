
import asyncio
import os
from dotenv import load_dotenv

# Load env
load_dotenv("../.env")

from gaia_link.tools.execute_donation import ExecuteDonationTool

async def main():
    tool = ExecuteDonationTool()
    
    # Turkey-Syria Earthquake Relief Proposal ID is 0 based on SetupDemo script
    # Actually SetupDemo starts with 1, but nextProposalId - 1 logic might be 0 indexed internally if first is 0. 
    # Wait, in SetupDemo: manager.createProposal(1, token, "Turkey-Syria ...")
    # In list_proposals output: [0] Turkey-Syria Earthquake Relief
    
    result = await tool.execute(
        amount=1.0,
        token="USDC",
        proposal_id="0",
        vault_type="DIRECT"
    )
    
    print("--- Donation Result ---")
    print(f"Success: {result['success']}")
    if result['success']:
        payload = result['transaction_payload']
        print(f"To: {payload['to']}")
        print(f"Data: {payload['data']}")
        print(f"Value: {payload['value']}")
        print(f"ChainId: {payload['chainId']}")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
