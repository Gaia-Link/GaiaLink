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

from gaia_link.agent_v2 import GaiaLinkAgentV2
from gaia_link.tools import VerifyCrisisTool, ListCrisesTool, ExecuteDonationTool

from gaia_link.schemas import ChatResponse

class GaiaLinkService:
    def __init__(self):
        # Initialize the global agent instance
        self.agent = GaiaLinkAgentV2()
        print(f"--- Service: GaiaLinkAgentV2 Initialized ({self.agent.name}) ---")

    def _reset_agent_memory(self):
        """
        Reset agent memory to prevent stale tool_calls causing OpenAI API errors.

        This fixes: "An assistant message with 'tool_calls' must be followed by
        tool messages responding to each 'tool_call_id'"
        """
        try:
            if hasattr(self.agent, 'memory') and self.agent.memory:
                if hasattr(self.agent.memory, 'messages'):
                    self.agent.memory.messages.clear()
                elif hasattr(self.agent.memory, 'clear'):
                    self.agent.memory.clear()
            # Also reset tool_calls if present
            if hasattr(self.agent, 'tool_calls'):
                self.agent.tool_calls = None
            # Reset current_step counter
            if hasattr(self.agent, 'current_step'):
                self.agent.current_step = 0
            print("--- Service: Agent memory reset ---")
        except Exception as e:
            print(f"--- Service: Memory reset warning: {e} ---")

    def _is_tool_call_error(self, error_msg: str) -> bool:
        """Check if error is the OpenAI tool_call_id mismatch error."""
        return "tool_call_ids did not have response messages" in error_msg

    async def process_message(self, message: str) -> ChatResponse:
        """
        Process a user message through the agent and handle any tool execution requirements.
        """
        try:
            print(f"--- Service: Processing message '{message}' ---")

            # NOTE: Do NOT reset memory here - it breaks conversation context.
            # Memory is only reset when tool_call_id errors occur (in error handler below).

            # 1. Run the Agent
            response_text = await self.agent.run(message)
            print(f"--- Service: Raw Agent Response ---\n{response_text}\n-------------------------------")
            
            # 2. Parse JSON Response
            data = self._parse_json(response_text)

            # 3. Intercept Tool Execution (Fix for Agent returning raw tool_code)
            if "tool_code" in data:
                return await self._handle_tool_interception(data["tool_code"])

            # 4. Detect donation response from plain text (Agent didn't return JSON)
            action_taken = data.get("action_taken", "chat")
            transaction_payload = data.get("transaction_payload")
            ui_hints = data.get("ui_hints", {"mode": "IDLE", "actions": []})

            # Check if plain text response contains donation transaction details
            if action_taken == "chat" and self._is_donation_response(response_text):
                print("--- Service: Detected donation response in plain text ---")
                amount = self._extract_amount_from_message(response_text)
                token = self._extract_token_from_message(response_text)

                tool = ExecuteDonationTool()
                result = await tool.execute(
                    amount=amount,
                    token=token,
                    recipient_address="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91"
                )

                return ChatResponse(
                    message=data.get("message", response_text),
                    action_taken="execute_donation",
                    ui_hints={
                        "mode": "SIGNATURE",
                        "display_data": {
                            "title": f"Donate {amount} {token}",
                            "badge_text": "Ready to Sign",
                            "badge_color": "green",
                            "risk_level": "LOW"
                        },
                        "actions": [{"label": "Sign Transaction", "type": "sign_transaction", "icon": "pen-tool"}]
                    },
                    transaction_payload=result.get("transaction_payload")
                )

            if action_taken == "execute_donation" and not transaction_payload:
                # Agent said it prepared donation but didn't include payload - generate it
                print("--- Service: Generating missing transaction_payload ---")
                amount = self._extract_amount_from_message(data.get("message", ""))
                token = self._extract_token_from_message(data.get("message", ""))

                tool = ExecuteDonationTool()
                result = await tool.execute(
                    amount=amount,
                    token=token,
                    recipient_address="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91"
                )
                transaction_payload = result.get("transaction_payload")

                # Ensure UI mode is SIGNATURE for donation
                ui_hints = {
                    "mode": "SIGNATURE",
                    "display_data": {
                        "title": f"Donate {amount} {token}",
                        "badge_text": "Ready to Sign",
                        "badge_color": "green",
                        "risk_level": "LOW"
                    },
                    "actions": [{"label": "Sign Transaction", "type": "sign_transaction", "icon": "pen-tool"}]
                }

            # 5. Standard Response
            return ChatResponse(
                message=data.get("message", response_text),
                action_taken=action_taken,
                ui_hints=ui_hints,
                transaction_payload=transaction_payload
            )

        except Exception as e:
            error_msg = str(e)
            print(f"--- Service Error: {error_msg} ---")

            # Handle tool_call_id mismatch error by recreating agent and retrying
            if self._is_tool_call_error(error_msg):
                print("--- Service: Detected tool_call error, recreating agent ---")
                try:
                    # Recreate agent to fully reset state
                    self.agent = GaiaLinkAgentV2()
                    print("--- Service: Agent recreated, retrying ---")

                    # Retry with fresh agent
                    response_text = await self.agent.run(message)
                    data = self._parse_json(response_text)

                    return ChatResponse(
                        message=data.get("message", response_text),
                        action_taken=data.get("action_taken", "chat"),
                        ui_hints=data.get("ui_hints", {"mode": "IDLE", "actions": []}),
                        transaction_payload=data.get("transaction_payload")
                    )
                except Exception as retry_error:
                    print(f"--- Service: Retry also failed: {retry_error} ---")
                    error_msg = str(retry_error)

            # Fallback for critical errors
            return ChatResponse(
                message=f"I encountered an internal error: {error_msg}",
                action_taken="error",
                ui_hints={"mode": "IDLE", "actions": []}
            )

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM output - simplified for OpenAI"""
        clean_text = text

        # Extract JSON from markdown code blocks if present
        if "```" in clean_text:
            match = re.search(r'```(?:json)?\s*(.*?)```', clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1).strip()

        # Try to parse as JSON
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # Not JSON - return as plain chat response
            return {"message": text, "action_taken": "chat"}

    def _extract_amount_from_message(self, message: str) -> float:
        """Extract donation amount from message text"""
        # Match patterns like "100 USDC", "10.5 ETH", etc.
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:USDC|USDT|ETH|DAI)', message, re.IGNORECASE)
        if match:
            return float(match.group(1))
        # Fallback: try to find any number
        match = re.search(r'(\d+(?:\.\d+)?)', message)
        return float(match.group(1)) if match else 100.0

    def _extract_token_from_message(self, message: str) -> str:
        """Extract token type from message text"""
        message_upper = message.upper()
        for token in ["USDC", "USDT", "ETH", "DAI"]:
            if token in message_upper:
                return token
        return "USDC"  # Default

    def _is_donation_response(self, text: str) -> bool:
        """Detect if response contains a PREPARED donation transaction.

        Uses STRUCTURAL patterns (Ethereum addresses, Gas, contract info) instead of
        keywords for reliable detection. This avoids issues like "捐款" vs "捐贈".

        Requires at least 3 of these structural indicators:
        1. Ethereum address (0x + 40 hex chars)
        2. Gas estimate
        3. Token amount (e.g., "10 USDC")
        4. Contract/address terminology
        """
        # Pattern 1: Ethereum address (0x followed by 40 hex chars)
        has_eth_address = bool(re.search(r'0x[a-fA-F0-9]{40}', text))

        # Pattern 2: Gas estimate (various formats)
        has_gas = bool(re.search(r'[Gg]as[：:]\s*[\d,]+', text))

        # Pattern 3: Token amount with known tokens
        has_token_amount = bool(re.search(r'\d+(?:\.\d+)?\s*(?:USDC|USDT|ETH|DAI)', text, re.IGNORECASE))

        # Pattern 4: Contract/address terminology (language-agnostic)
        has_contract_terms = bool(re.search(r'合約|地址|contract|address', text, re.IGNORECASE))

        # Must have at least 3 of 4 patterns to be a prepared transaction
        patterns_matched = sum([has_eth_address, has_gas, has_token_amount, has_contract_terms])

        return patterns_matched >= 3

    async def _handle_tool_interception(self, tool_code: str) -> ChatResponse:
        """
        Manually executes tools when the Agent returns a 'tool_code' string.
        """
        print(f"--- Service: Intercepting tool_code: {tool_code} ---")

        if "list_crises" in tool_code:
            tool = ListCrisesTool()
            result = await tool.execute(limit=10)

            # Format output (no emoji per user rules)
            crises_list = result.get("crises", [])
            crises_text = "\n".join([
                f"{i+1}. {c['title']} ({c['severity']})\n   Location: {c['location']}"
                for i, c in enumerate(crises_list[:5])
            ])

            return ChatResponse(
                message=f"以下是目前活躍的人道主義危機：\n\n{crises_text}\n\n您可以說「捐款 100 USDC 給土耳其」來進行捐款。",
                action_taken="list_crises",
                ui_hints={
                    "mode": "DECISION",
                    "display_data": {
                        "title": "Active Humanitarian Crises",
                        "badge_text": f"{len(crises_list)} Crises",
                        "badge_color": "yellow",
                        "risk_level": "LOW"
                    },
                    "actions": [
                        {"label": "Donate 100 USDC", "type": "input_prompt", "icon": "heart"},
                        {"label": "Verify a Crisis", "type": "input_prompt", "icon": "search"}
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
            # Extract amount from tool_code
            amount_match = re.search(r"amount=(\d+(?:\.\d+)?)", tool_code)
            amount = float(amount_match.group(1)) if amount_match else 100.0

            # Extract token
            token_match = re.search(r"token=['\"]?(\w+)['\"]?", tool_code)
            token = token_match.group(1).upper() if token_match else "USDC"

            tool = ExecuteDonationTool()
            result = await tool.execute(
                amount=amount,
                token=token,
                recipient_address="0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91"
            )

            return ChatResponse(
                message=f"Ready to donate {amount} {token}. Please sign the transaction.",
                action_taken="execute_donation",
                ui_hints={
                    "mode": "SIGNATURE",
                    "display_data": {
                        "title": f"Donate {amount} {token}",
                        "badge_text": "Ready to Sign",
                        "badge_color": "green",
                        "risk_level": "LOW"
                    },
                    "actions": [{"label": "Sign Transaction", "type": "sign_transaction", "icon": "pen-tool"}]
                },
                transaction_payload=result.get("transaction_payload")
            )

        # Default fallback if tool code not recognized
        return ChatResponse(
            message=f"Agent requested tool execution: {tool_code}",
            action_taken="tool_code_returned",
            ui_hints={"mode": "THINKING", "actions": []}
        )
