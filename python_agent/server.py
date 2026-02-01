import os
import logging
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set defaults only if not already configured in .env
if not os.getenv("LLM_PROVIDER"):
    os.environ["LLM_PROVIDER"] = "openai"

logger.info(f"LLM Provider: {os.getenv('LLM_PROVIDER')}")


app = FastAPI(title="GaiaLink Agent API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Service
from gaia_link.service import GaiaLinkService
service = GaiaLinkService()

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {"status": "ok", "agent": "GaiaLinkAgent"}

async def handle_donation_request(message_lower: str):
    """Handle donation requests with real ERC20 calldata generation."""
    from gaia_link.tools import ExecuteDonationTool

    # Parse amount from message
    amount = 100.0
    if "50" in message_lower: amount = 50.0
    elif "200" in message_lower: amount = 200.0
    elif "500" in message_lower: amount = 500.0

    tool = ExecuteDonationTool()
    result = await tool.execute(
        amount=amount,
        token="USDC",
        recipient_address="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91"
    )

    return {
        "message": f"Ready to donate {amount} USDC to the humanitarian aid vault on Sepolia testnet. Please review and sign the transaction.",
        "action_taken": "execute_donation",
        "ui_hints": {
            "mode": "DECISION",
            "display_data": {
                "title": f"Donate {amount} USDC",
                "badge_text": "Ready to Sign",
                "badge_color": "green",
                "risk_level": "LOW"
            },
            "actions": [{ "label": "Sign Transaction", "type": "sign_transaction", "icon": "pen-tool" }]
        },
        "transaction_payload": result.get("transaction_payload")
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint for the GaiaLink Agent.
    Receives a message and returns a structured response for the Frontend UI.
    """
    try:
        logger.info(f"Received message: {request.message}")
        message_lower = request.message.lower()

        # Check if using mock mode (direct rule-based responses)
        llm_provider = os.getenv("LLM_PROVIDER", "").lower()

        if llm_provider == "mock":
            logger.info("Using MOCK mode - rule-based responses")

            # Donation intent detection
            if ("donate" in message_lower or "捐" in message_lower or
                "usdc" in message_lower or "give" in message_lower):
                return await handle_donation_request(message_lower)

            # Crisis list request
            if ("crisis" in message_lower or "disaster" in message_lower or
                "災難" in message_lower or "list" in message_lower or "列出" in message_lower):
                return {
                    "message": "Here are the active humanitarian crises:\n\n1. Turkey Earthquake Relief - CRITICAL\n2. Ukraine Humanitarian Aid - HIGH\n3. Gaza Humanitarian Crisis - CRITICAL\n4. Sudan Famine Relief - HIGH\n5. Yemen Crisis Response - MEDIUM\n\nYou can donate to any of these by saying 'donate [amount] USDC'.",
                    "action_taken": "list_crises",
                    "ui_hints": {"mode": "DECISION", "actions": [
                        {"label": "Donate 100 USDC", "type": "select_vault", "icon": "dollar-sign"},
                        {"label": "View Details", "type": "view_details", "icon": "info"}
                    ]}
                }

            # Default response
            return {
                "message": "I'm the GaiaLink Agent. I can help you:\n\n- Donate to humanitarian crises (e.g., 'donate 100 USDC')\n- View active crisis situations\n- Track your donation impact\n\nHow can I assist you today?",
                "action_taken": "idle_help",
                "ui_hints": {"mode": "IDLE", "actions": []}
            }

        # ------------------------------------------------------------------
        # HYBRID AGENT EXECUTION via SERVICE LAYER (for real LLM providers)
        # ------------------------------------------------------------------
        try:
             return await service.process_message(request.message, context_data=request.context)

        except Exception as e:
            logger.warning(f"Service failed ({e}). Falling back to rule-based.")

            # Fallback to donation handler
            if ("donate" in message_lower or "捐" in message_lower or "usdc" in message_lower):
                return await handle_donation_request(message_lower)

            return {
                "message": f"I encountered an error: {str(e)}. You can still try 'donate 100 USDC' to test the donation flow.",
                "action_taken": "error",
                "ui_hints": {"mode": "IDLE", "actions": []}
            }

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
