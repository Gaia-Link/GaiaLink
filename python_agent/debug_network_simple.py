
import asyncio
from web3 import Web3

# Config from frontend/src/lib/contracts.ts (will fill in after reading)
# AND from .env

async def check_connection(rpc_url, contract_address):
    print(f"Connecting to {rpc_url}...")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("FAILED to connect to Web3")
        return

    print(f"Connected! Chain ID: {w3.eth.chain_id}")
    print(f"Checking code at {contract_address}...")
    
    code = w3.eth.get_code(w3.to_checksum_address(contract_address))
    if code and len(code) > 0:
        print("SUCCESS: Contract code found!")
    else:
        print("ERROR: No code at address. Wrong address or network reset?")

if __name__ == "__main__":
    # Hardcoded values we expect
    RPC = "http://localhost:8545" 
    # Valid address from contracts.ts/.env
    ADDRESS = "0x114e375B6FCC6d6fCb68c7A1d407E652C54F25FB" 
    
    asyncio.run(check_connection(RPC, ADDRESS))
