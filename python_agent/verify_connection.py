import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load env
load_dotenv()

rpc_url = os.getenv("SEPOLIA_RPC_URL", "http://localhost:8545")
web3 = Web3(Web3.HTTPProvider(rpc_url))

print(f"Connecting to {rpc_url}...")
if not web3.is_connected():
    print("❌ Failed to connect to Anvil")
    sys.exit(1)

print(f"✅ Connected. Chain ID: {web3.eth.chain_id}")

contracts = {
    "ProposalManager": os.getenv("PROPOSAL_MANAGER_ADDRESS"),
    "CharityRegistry": os.getenv("CHARITY_REGISTRY_ADDRESS"),
    "USDC": os.getenv("USDC_TOKEN_ADDRESS")
}

for name, address in contracts.items():
    if not address:
        print(f"❌ {name} address not found in env")
        continue
    
    code = web3.eth.get_code(address)
    if code and code != b'':
        print(f"✅ {name} found at {address}")
    else:
        print(f"❌ {name} code NOT found at {address}")

