
import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load env
load_dotenv(dotenv_path="python_agent/.env")

RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
MANAGER_ADDR = os.getenv("PROPOSAL_MANAGER_ADDRESS", "0x9fe46736679d2d9a65f0992f2272de9f3c7fa6e0")
USER_ADDR = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

ABI = [
    {
        "inputs": [{"name": "_user", "type": "address"}],
        "name": "getUserPortfolio",
        "outputs": [
            {
                "components": [
                    {"name": "proposalId", "type": "uint256"},
                    {"name": "directAmount", "type": "uint256"},
                    {"name": "noLossAmount", "type": "uint256"}
                ],
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "nextProposalId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    print(f"Connecting to {RPC_URL}...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("Failed to connect.")
        return

    print(f"Manager Address: {MANAGER_ADDR}")
    manager_checksum = w3.to_checksum_address(MANAGER_ADDR)
    contract = w3.eth.contract(address=manager_checksum, abi=ABI)
    
    try:
        next_id = contract.functions.nextProposalId().call()
        print(f"Next Proposal ID: {next_id}")
        
        user_checksum = w3.to_checksum_address(USER_ADDR)
        print(f"Querying portfolio for {user_checksum}...")
        portfolio = contract.functions.getUserPortfolio(user_checksum).call()
        print(f"Raw Portfolio: {portfolio}")
        
        count = 0
        for item in portfolio:
            # item is typically a tuple or dict depending on middleware, but raw call usually gives tuple
            pid, direct, no_loss = item
            if direct > 0 or no_loss > 0:
                print(f" फाउंड Contribution! Proposal {pid}: Direct={direct}, NoLoss={no_loss}")
                count += 1
        
        print(f"Total non-zero contributions: {count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
