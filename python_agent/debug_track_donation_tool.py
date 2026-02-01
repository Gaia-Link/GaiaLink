
import asyncio
import os
import sys

# Add python_agent to path
sys.path.append(os.path.join(os.getcwd(),'python_agent'))

try:
    from gaia_link.tools.track_donation import TrackDonationTool
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def main():
    print("Initializing TrackDonationTool...")
    tool = TrackDonationTool()
    print(f"Tool Name: {tool.name}")
    print(f"Tool Description: {tool.description}")
    
    # Test with a mock address for now
    address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" # Anvil Account 0
    print(f"\nExecuting tool for address: {address}")
    
    try:
        result = await tool.execute(wallet_address=address)
        print("\nResult:")
        print(result)
    except Exception as e:
        print(f"\nExecution Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
