
import asyncio
import os
import asyncio
import os
from dotenv import load_dotenv

# Load .env explicitly since BlockchainConfig uses os.getenv directly
load_dotenv("../.env")  # Try parent dir first (if running from python_agent/)
load_dotenv(".env")     # Then current dir

from gaia_link.services.blockchain.config import get_blockchain_config, GAIA_CHARITY_REGISTRY_ABI, GAIA_PROPOSAL_MANAGER_ABI
from gaia_link.services.blockchain.provider import get_web3_provider

# Seed Data
CHARITIES = [
    {"name": "Red Cross", "region": "Global"},
    {"name": "UNICEF", "region": "Global"},
    {"name": "Save the Children", "region": "Global"}
]

PROPOSALS = [
    {
        "title": "Clean Water for Gaza",
        "description": "Provide clean drinking water desalination units.",
        "target": 50000,
        "duration": 30,
        "lat": 31.3547,
        "lng": 34.3223,
        "category_id": 4, # Famine/Water
        "institution_index": 0
    },
    {
        "title": "Earthquake Relief in Turkey",
        "description": "Emergency shelter and medical supplies for survivors.",
        "target": 100000,
        "duration": 60,
        "lat": 37.0000,
        "lng": 37.0000,
        "category_id": 1, # Earthquake
        "institution_index": 0
    },
    {
        "title": "Medical Aid for Sudan",
        "description": "Essential medicines and mobile clinics.",
        "target": 75000,
        "duration": 45,
        "lat": 15.0000,
        "lng": 30.0000,
        "category_id": 3, # Conflict
        "institution_index": 1
    },
     {
        "title": "Kyiv Power Grid Restoration",
        "description": "Generators for hospitals in Kyiv.",
        "target": 120000,
        "duration": 45,
        "lat": 50.4501,
        "lng": 30.5234,
        "category_id": 3, # Conflict
        "institution_index": 0
    },
    {
        "title": "Yemen Food Security Program",
        "description": "Emergency food distribution for at-risk families.",
        "target": 80000,
        "duration": 30,
        "lat": 15.3694,
        "lng": 44.1910,
        "category_id": 4, # Famine
        "institution_index": 1
    }
]

async def main():
    config = get_blockchain_config()
    provider = get_web3_provider()
    
    if not provider.is_connected():
        print("ERROR: Not connected to Web3")
        return

    # 1. Register Charities
    print("--- Registering Charities ---")
    registry = provider.get_charity_registry()
    proposal_manager = provider.get_proposal_manager()
    
    # Check existing charities count
    next_charity_id = registry.functions.nextCharityId().call()
    print(f"Current Charity Count: {next_charity_id}")
    
    charity_ids = list(range(next_charity_id)) # Assume [0, 1, 2...]
    
    if not charity_ids:
         print("No charities found! Cannot create proposals without full ABI to register.")
         # If ABI is missing registerCharity, we can't register. 
         # But usually SetupDemo.s.sol registers some.
         return

    # 2. Create Proposals
    print("\n--- Creating Proposals ---")
    
    for p in PROPOSALS:
        # Round robin assign to available charities
        cid = charity_ids[p['institution_index'] % len(charity_ids)]
        
        print(f"Creating Proposal: {p['title']} (Charity ID: {cid})...")
        
        # createProposal(charityId, asset, title, metadata, lat, lng, category, duration)
        # lat/lng need scaling by 10000
        lat_scaled = int(p['lat'] * 10000)
        lng_scaled = int(p['lng'] * 10000)
        duration_sec = p['duration'] * 24 * 3600
        
        tx_func = proposal_manager.functions.createProposal(
            cid, 
            provider.web3.to_checksum_address(config.addresses.usdc_token),
            p['title'],
            p['description'], # metadata
            lat_scaled,
            lng_scaled,
            p['category_id'],
            duration_sec
        )
        
        try:
            receipt = provider.send_transaction(tx_func)
            print(f"  -> Success! Tx: {receipt['tx_hash']}")
        except Exception as e:
            print(f"  -> Failed: {e}")

    print("\n--- Seeding Complete ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
