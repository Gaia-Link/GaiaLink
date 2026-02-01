import os
from dotenv import load_dotenv
from pathlib import Path

# Try to load exactly like server.py
env_path = Path(__file__).parent / '.env'
print(f"Checking local .env: {env_path} (Exists: {env_path.exists()})")
load_dotenv(dotenv_path=env_path)

parent_env_path = Path(__file__).parent.parent / '.env'
print(f"Checking parent .env: {parent_env_path} (Exists: {parent_env_path.exists()})")
load_dotenv(dotenv_path=parent_env_path)

print(f"PROPOSAL_MANAGER_ADDRESS: {os.getenv('PROPOSAL_MANAGER_ADDRESS')}")
print(f"CHARITY_REGISTRY_ADDRESS: {os.getenv('CHARITY_REGISTRY_ADDRESS')}")
print(f"USDC_TOKEN_ADDRESS: {os.getenv('USDC_TOKEN_ADDRESS')}")
