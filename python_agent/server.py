import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

import os
# Force SpoonOS to see Gemini config
os.environ["LLM_PROVIDER"] = "gemini"
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-to-bypass-validation"

print(f"DEBUG: LLM_PROVIDER = {os.getenv('LLM_PROVIDER')}")
print(f"DEBUG: GOOGLE_API_KEY = {os.getenv('GOOGLE_API_KEY')[:5]}..." if os.getenv('GOOGLE_API_KEY') else "DEBUG: GOOGLE_API_KEY = None")


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

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint for the GaiaLink Agent.
    Receives a message and returns a structured response for the Frontend UI.
    """
    try:
        print(f"Received message: {request.message}")
        message_lower = request.message.lower()

        # ------------------------------------------------------------------
        # HYBRID AGENT EXECUTION via SERVICE LAYER
        # ------------------------------------------------------------------
        try:
             # Delegate to Service Layer
             return await service.process_message(request.message)
             
        except Exception as e:
            print(f"--- LOG: Service Failed ({e}). Falling back to Simulation. ---")
            
            # FALLBACK SIMULATION LOGIC (Kept for absolute safety demo)
            if ("donate" in message_lower or "捐" in message_lower) or ("usdc" in message_lower):
                amount = 100.0
                if "50" in message_lower: amount = 50.0
                
                from gaia_link.tools import ExecuteDonationTool
                tool = ExecuteDonationTool()
                result = await tool.execute(amount=amount, token="USDC", recipient_address="0xDem0VaultAddressForTurkeyRelief00000000", vault_type="DIRECT")
                
                return {
                    "message": f"I understand you want to donate {amount} USDC. (Fallback Mode) " + result.get("message", ""),
                    "action_taken": "execute_donation",
                    "ui_hints": {
                        "mode": "SIGNATURE",
                        "display_data": {
                            "title": "Donation Request",
                            "badge_text": "Ready to Sign",
                            "badge_color": "green",
                            "risk_level": "LOW"
                        },
                        "actions": [{ "label": "Sign Transaction", "type": "sign_transaction", "icon": "pen-tool" }]
                    },
                    "transaction_payload": result.get("transaction_payload")
                }
            
            return {
                "message": f"I am the GaiaLink Agent. I encountered an error: {str(e)}.",
                "action_taken": "error",
                "ui_hints": {"mode": "IDLE", "actions": []}
            }

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
