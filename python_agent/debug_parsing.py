
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../.env")
load_dotenv(".env")

from gaia_link.services.blockchain.config import get_blockchain_config, GAIA_PROPOSAL_MANAGER_ABI
from gaia_link.services.blockchain.provider import get_web3_provider
from gaia_link.services.proposal.models import ProposalStatus

# Copied from gaia_proposal.py to test in isolation
CATEGORY_MAP = {
    1: "earthquake",
    2: "flood",
    3: "conflict",
    4: "famine",
    5: "pandemic",
}

def parse_proposal(proposal_id, data):
    print(f"Parsing ID {proposal_id} with data: {data}")
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

    print(f"  > Expiry timestamp: {expiry}")
    expiry_dt = datetime.fromtimestamp(expiry)
    print(f"  > Expiry DT: {expiry_dt}")

    # Convert lat/lng from scaled int24 to float
    lat_float = lat / 10000.0
    lng_float = lng / 10000.0
    print(f"  > Loc: {lat_float}, {lng_float}")

    return "Success"

async def main():
    config = get_blockchain_config()
    provider = get_web3_provider()
    pm = provider.get_proposal_manager()
    
    try:
        pid = 0
        print(f"Fetching Proposal {pid}...")
        data = pm.functions.proposals(pid).call()
        
        result = parse_proposal(pid, data)
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
