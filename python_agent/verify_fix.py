import re
import asyncio
from gaia_link.service import GaiaLinkService

async def test_regex():
    service = GaiaLinkService()
    
    # Test cases for proposal name extraction
    test_messages = [
        "向Morocco Earthquake Reconstruction提案直接捐款10usdc",
        "幫我向 Turkey Earthquake Relief 提案捐款 50 USDC",
        "donate 100 USDC to Gaza Humanitarian Crisis project",
        "幫助 Sudan Famine Relief 提案"
    ]
    
    print("\n--- Testing Regex Extraction ---")
    for msg in test_messages:
        # Mock combined_text as handled in service.py
        combined = f"{msg} | Agent says something"
        name = service._extract_proposal_name_from_message(combined)
        print(f"Message: {msg}")
        print(f"Extracted Name: '{name}'")
        
    print("\n--- Testing Service Data Prioritization ---")
    # Simulate data returned from agent turn
    data = {
        "message": "I've prepared the donation",
        "details": {
            "proposal_id": "6",
            "amount": 10.0,
            "token": "USDC"
        }
    }
    
    # We can't easily run the full process_message without a live node, 
    # but we can check the logic we added.
    agent_msg = data.get("message")
    details = data.get("details", {})
    override_id = details.get("proposal_id")
    print(f"Agent Resolved ID: {override_id}")

if __name__ == "__main__":
    asyncio.run(test_regex())
