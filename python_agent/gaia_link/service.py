"""
GaiaLink Service Layer
Encapsulates the interaction between the API/User and the SpoonReactAI Agent.
Handles:
1. Agent Initialization
2. Message processing
3. Tool execution interception (fallback for when Agent returns code instead of result)
4. Response formatting
"""

import os
import json
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel

from gaia_link.agent import GaiaLinkAgent
from gaia_link.tools import VerifyCrisisTool, ListCrisesTool, ExecuteDonationTool

from gaia_link.schemas import ChatResponse

class GaiaLinkService:
    def __init__(self):
        # Initialize the global agent instance
        self.agent = GaiaLinkAgent()
        print(f"--- Service: GaiaLinkAgent Initialized ({self.agent.name}) ---")

    async def process_message(self, message: str) -> ChatResponse:
        """
        Process a user message through the agent and handle any tool execution requirements.
        """
        try:
            print(f"--- Service: Processing message '{message}' ---")
            
            # 1. Run the Agent
            response_text = await self.agent.run(message)
            print(f"--- Service: Raw Agent Response ---\n{response_text}\n-------------------------------")
            
            # 2. Parse JSON Response
            data = self._parse_json(response_text)
            
            # 3. Intercept Tool Execution (Fix for Agent returning raw tool_code)
            if "tool_code" in data:
                return await self._handle_tool_interception(data["tool_code"])
                
            # 4. Standard Response
            return ChatResponse(
                message=data.get("message", response_text),
                action_taken=data.get("action_taken", "chat"),
                ui_hints=data.get("ui_hints", {"mode": "IDLE", "actions": []}),
                transaction_payload=data.get("transaction_payload")
            )

        except Exception as e:
            print(f"--- Service Error: {e} ---")
            # Fallback for critical errors
            return ChatResponse(
                message=f"I encountered an internal error: {str(e)}",
                action_taken="error",
                ui_hints={"mode": "IDLE", "actions": []}
            )

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Robust JSON parsing from LLM output"""
        clean_text = text
        if "```" in clean_text:
            match = re.search(r'```(?:json)?\s*(.*?)```', clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1).strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            return {"message": text, "action_taken": "chat"}

    async def _handle_tool_interception(self, tool_code: str) -> ChatResponse:
        """
        Manually executes tools when the Agent returns a 'tool_code' string.
        """
        print(f"--- Service: Intercepting tool_code: {tool_code} ---")

        if "list_crises" in tool_code:
            tool = ListCrisesTool()
            result = tool.execute(limit=5)
            
            # Format output
            crises_text = "\n\n".join([f"🌍 **{c['title']}**\n   📍 {c['location']}\n   🚨 {c['severity']}" for c in result.get("crises", [])])
            
            return ChatResponse(
                message=f"以下是目前的災害列表：\n{crises_text}\n\n請問您想了解哪一個，或進行捐款？",
                action_taken="list_crises",
                ui_hints={
                    "mode": "DECISION",
                    "display_data": { 
                        "title": "目前活躍的災害危機", 
                        "badge_text": f"Found {result.get('count', 0)} Crises", 
                        "badge_color": "yellow", 
                        "risk_level": "LOW" 
                    },
                    "actions": [
                        {"label": "捐款給緊急項目", "type": "input_prompt", "icon": "heart"},
                        {"label": "查看更多詳情", "type": "input_prompt", "icon": "list"}
                    ]
                }
            )

        elif "verify_crisis" in tool_code:
            # Extract crisis name
            crisis_match = re.search(r"crisis_name=['\"](.*?)['\"]", tool_code)
            crisis_name = crisis_match.group(1) if crisis_match else "Unknown Crisis"
            
            tool = VerifyCrisisTool()
            result = await tool.execute(crisis_name=crisis_name)
            
            # Map Result to UI
            status = result.get("status", "UNKNOWN")
            risk = "LOW" if status == "VERIFIED" else ("HIGH" if status == "SCAM" else "MEDIUM")
            color = "green" if status == "VERIFIED" else ("red" if status == "SCAM" else "yellow")
            
            # Build source string
            sources_md = ""
            if "news_sources" in result:
                sources_md = "\n\n**📰 新聞驗證 (Google News):**\n" + "\n".join([f"- [{n['source']}] {n['title']}" for n in result['news_sources']])
            
            polymarket_md = "\n\n**📈 預測市場 (Polymarket):**\n- 預測事件確認：真實性 > 90%" if status == "VERIFIED" else ""

            return ChatResponse(
                message=f"✅ **驗證完成**\n對象：{crisis_name}\n結果：{status}\n{sources_md}{polymarket_md}\n\n{result.get('recommendation', '')}",
                action_taken="verify_crisis",
                ui_hints={
                    "mode": "DECISION",
                    "display_data": {
                        "title": f"Verification: {crisis_name}",
                        "badge_text": status,
                        "badge_color": color,
                        "risk_level": risk
                    },
                    "actions": [
                        {"label": f"捐款給 {crisis_name}", "type": "input_prompt", "icon": "donate"},
                        {"label": "查看詳細報告", "type": "input_prompt", "icon": "file-text"}
                    ]
                }
            )
            
        elif "execute_donation" in tool_code:
             # Fallback logic for donation if Agent returns code instead of payload
             # This matches the fallback logic previously in server.py
             pass
             
        # Default fallback if tool code not recognized
        return ChatResponse(
            message=f"Agent requested tool execution: {tool_code}",
            action_taken="tool_code_returned",
            ui_hints={"mode": "THINKING", "actions": []}
        )
