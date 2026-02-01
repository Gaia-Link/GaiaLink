
import asyncio
import os
from dotenv import load_dotenv

# Load env before imports
load_dotenv("../.env")
load_dotenv(".env")

from gaia_link.services.proposal import get_proposal_service
from gaia_link.services.proposal.models import ProposalStatus

async def main():
    service = get_proposal_service()
    print(f"Service Type: {type(service)}")
    
    print("--- Listing All Proposals ---")
    all_proposals = await service.list_proposals()
    print(f"Total count: {len(all_proposals)}")
    for p in all_proposals[:5]:
        print(f"[{p.proposal_id}] {p.title} - Status: {p.status.name} - Expiry: {p.deadline}")

    print("\n--- Listing Active Proposals (Status=FUNDING) ---")
    active = await service.list_proposals(status=ProposalStatus.FUNDING)
    print(f"Active count: {len(active)}")
    
if __name__ == "__main__":
    asyncio.run(main())
