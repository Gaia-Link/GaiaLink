"""
Gaia Link Agent API Server

FastAPI server that exposes the GaiaLink Agent via HTTP endpoints.
Frontend connects to this server to interact with the SpoonOS Agent.
"""

import os
import sys

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any

from gaia_link.service import GaiaLinkService
from gaia_link.schemas import ChatResponse

# Initialize FastAPI app
app = FastAPI(
    title="Gaia Link Agent API",
    description="SpoonOS-based humanitarian crisis response AI agent",
    version="1.0.0",
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the service (this creates the Agent)
service: Optional[GaiaLinkService] = None


class ChatRequest(BaseModel):
    """Request body for chat endpoint"""
    message: str
    context: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_name: str
    tools: list[str]


@app.on_event("startup")
async def startup_event():
    """Initialize the GaiaLink service on startup"""
    global service
    print("=" * 60)
    print("  Gaia Link Agent API Server Starting...")
    print("=" * 60)

    try:
        service = GaiaLinkService()
        print(f"  Agent initialized: {service.agent.name}")
        print(f"  Tools: {[t.name for t in service.agent.available_tools]}")
        print("=" * 60)
    except Exception as e:
        print(f"  [ERROR] Failed to initialize service: {e}")
        raise


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return HealthResponse(
        status="healthy",
        agent_name=service.agent.name,
        tools=[t.name for t in service.agent.available_tools]
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return await root()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for interacting with the Agent.

    This is called by the frontend SpoonOSInterface component.
    """
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        print(f"\n{'='*60}")
        print(f"  Received message: {request.message[:100]}...")
        print(f"{'='*60}")

        response = await service.process_message(request.message)

        print(f"  Response action: {response.action_taken}")
        print(f"  UI mode: {response.ui_hints.get('mode', 'UNKNOWN')}")
        print(f"{'='*60}\n")

        return response

    except Exception as e:
        print(f"  [ERROR] Chat processing failed: {e}")
        import traceback
        traceback.print_exc()

        # Return error response instead of raising exception
        return ChatResponse(
            message=f"I encountered an error processing your request: {str(e)}",
            action_taken="error",
            ui_hints={"mode": "IDLE", "actions": []}
        )


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("  Starting Gaia Link Agent API Server")
    print("  Frontend should connect to: http://localhost:8000")
    print("=" * 60 + "\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
