
from web3 import Web3
import json

# Connect to Anvil
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

# Contracts
REGISTRY_ADDR = "0xefab0beb0a557e452b398035ea964948c750b2fd"

REGISTRY_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "getCharity",
        "outputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "address", "name": "admin", "type": "address"},
            {"internalType": "bool", "name": "isActive", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def check_charity(charity_id):
    try:
        registry = w3.eth.contract(address=REGISTRY_ADDR, abi=REGISTRY_ABI)
        data = registry.functions.getCharity(charity_id).call()
        print(f"Charity {charity_id}: Name={data[0]}, Admin={data[1]}, Active={data[2]}")
    except Exception as e:
        print(f"Failed to fetch Charity {charity_id}: {e}")

def get_selector(sig):
    return w3.keccak(text=sig).hex()[:10]

print("--- Selectors ---")
sig = "createProposal(uint256,address,string,string,int24,int24,uint8,uint256)"
print(f"{sig} -> {get_selector(sig)}")

print("\n--- Charity Status ---")
check_charity(0)
check_charity(1)
check_charity(2)
