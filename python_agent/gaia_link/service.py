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
from gaia_link.services.blockchain.config import get_blockchain_config

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

    async def process_message(self, message: str, context_data: Dict[str, Any] = None) -> ChatResponse:
        """
        Process a user message through the agent and handle any tool execution requirements.
        """
        try:
            print(f"--- Service: Processing message '{message}' ---")

            # NOTE: Do NOT reset memory here - it breaks conversation context.
            # Memory is only reset when tool_call_id errors occur (in error handler below).

            # 1. Run the Agent
            # Inject Context into Message if present
            user_context_info = ""
            if "user_address" in context_data and context_data["user_address"]:
                user_context_info += f"\n[System Context] User Wallet Address: {context_data['user_address']}"
            
            full_message = message + user_context_info
            
            print(f"--- Service: Sending message with context: '{full_message}' ---")
            response_text = await self.agent.run(full_message)
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
            tx_sequence_list = None

            # AUTO-NAVIGATION Fallback: Detect coords in response text
            has_move_intent = any(kw in message.lower() for kw in ["轉移", "定位", "center", "move", "focus", "聚焦", "正中央", "導航", "navigate"])
            if has_move_intent and not any(a.get("type") == "FLY_TO_LOCATION" for a in ui_hints.get("actions", [])):
                # Match various lat/lng formats (including "緯度: 34.352")
                lat_match = re.search(r'(?:[緯w][度d]|lat|latitude)[^-\d]*(-?\d+\.\d+)', response_text, re.IGNORECASE)
                lng_match = re.search(r'(?:[經j][度d]|lng|lng|longitude)[^-\d]*(-?\d+\.\d+)', response_text, re.IGNORECASE)
                
                if lat_match and lng_match:
                    lat = float(lat_match.group(1))
                    lng = float(lng_match.group(1))
                    print(f"--- Service: Auto-injecting FLY_TO to ({lat}, {lng}) ---")
                    
                    if "actions" not in ui_hints: ui_hints["actions"] = []
                    ui_hints["actions"].insert(0, {
                        "label": "Locking On Location",
                        "type": "FLY_TO_LOCATION",
                        "data": {"lat": lat, "lng": lng, "zoom": 12},
                        "icon": "globe"
                    })
                    action_taken = "fly_to_location"
                    
                    # CLEANUP: Replace "tutorial-like" instructions with professional ones
                    if any(kw in response_text for kw in ["請將地標中心", "座標如下", "你可以將", "指令如下"]):
                        data["message"] = "已經為您鎖定目標區域，畫面正在轉移與縮放中。"

            # 4. Detect donation response
            is_donation_intent = (
                action_taken == "execute_donation" or 
                self._is_donation_response(response_text) or
                (self._is_donation_response(message) and any(kw in response_text for kw in ["捐", "地址", "白名單", "1", "USDC"]))
            )

            if is_donation_intent:
                print(f"--- Service: Preparing donation response (Action: {action_taken}) ---")
                # Combine original message + agent response to ensure we have all context (amount, token, name)
                combined_text = f"{message} | {data.get('message', response_text)}"
                return await self._prepare_donation_response(combined_text)

            # 4.5 Detect Withdrawal Response (Fix for missing blue button)
            # Check if agent mentioned "提取", "withdraw" and "successfully" or "found"
            is_withdrawal = "withdraw" in response_text.lower() or "提取" in response_text
            
            if is_withdrawal:
                # Scan memory for the tool output to retrieve transaction_sequence
                if hasattr(self.agent, "memory"):
                     # Try to find the latest tool message from 'withdraw_contribution'
                     # Access internal memory storage (depends on SpoonReactAI impl)
                     # Usually agent.memory.messages is a list of {"role":..., "content":...}
                     # "content" for tool role is the output string.
                     # We need to parse that string if it's JSON.
                     
                     try:
                         # Iterate backwards
                         for msg in reversed(self.agent.memory.messages):
                             # Robust access for role and content (Object or Dict)
                             role = getattr(msg, "role", None) or msg.get("role")
                             content = getattr(msg, "content", None) or msg.get("content")
                             
                             if role == "tool" and "transaction_sequence" in str(content):
                                 import json
                                 try:
                                     # Tool output is a stringified JSON
                                     tool_output = json.loads(content)
                                     if "transaction_sequence" in tool_output:
                                         print("--- Service: Found withdrawal payload in memory, injecting into UI ---")
                                         transaction_payload = tool_output.get("transaction_payload") # For single
                                         tx_sequence = tool_output.get("transaction_sequence") # For batch
                                         
                                         # Construct UI hints
                                         ui_hints["mode"] = "SIGNATURE" # Or DECISION
                                         ui_hints["actions"] = [{
                                             "label": "Sign Withdrawal Transactions", 
                                             "type": "sign_transaction", 
                                             "icon": "download"
                                         }]
                                         
                                         # Pass sequence as payload to frontend (frontend supports checking sequence)
                                         # If sequence exists, we put it in transaction_sequence (frontend logic: if sequence, use it)
                                         # Typically frontend expects `transaction_payload` for single, but we can pass sequence list.
                                         # Let's attach it to `transaction_payload` as a special 'sequence' wrapper or just rely on SpoonOSInterface to support `txSequence`
                                         # SpoonOSInterface lines 34: `const [txSequence, setTxSequence] = useState<any[]>([]);`
                                         
                                         # We need to figure out how to pass 'txSequence' to frontend.
                                         # ChatResponse has 'transaction_payload'.
                                         # If we pass a LIST to transaction_payload, frontend might break if it expects object.
                                         # However, SpoonOSInterface handles `activePayload` via `txSequence`.
                                         # We need to signal frontend to set txSequence.
                                         # Let's wrap it? 
                                         # Checked SpoonOSInterface: it doesn't seem to parse `transaction_payload` as a sequence automatically unless specific trigger.
                                         # Wait, I checked SpoonOSInterface earlier. 
                                         # Line 220: `response: response`
                                         # Maybe I need to update SpoonOSInterface to handle `transaction_sequence` in response.
                                         
                                         # For now, let's inject it into `ui_hints` strictly.
                                         # ui_hints["transaction_sequence"] = tx_sequence
                                         
                                         # Better: Capture it for the top-level response
                                         tx_sequence_list = tx_sequence
                                         
                                         # Also set transaction_payload to first item for safety?
                                         if tx_sequence:
                                             transaction_payload = tx_sequence[0] 
                                         
                                         break
                                 except Exception as e:
                                     print(f"--- Service: Failed to parse tool output: {e} ---")
                     except Exception as e:
                         print(f"--- Service: Failed to scan memory: {e} ---")

            # 5. Standard Response
            return ChatResponse(
                message=data.get("message", response_text),
                action_taken=action_taken,
                ui_hints=ui_hints,
                transaction_payload=transaction_payload,
                transaction_sequence=tx_sequence_list
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

    def _extract_proposal_id_from_message(self, message: str) -> Optional[str]:
        """Extract proposal ID from message text"""
        # Match patterns like "Proposal #0", "ID: 0", "提案 0", "proposal 0"
        match = re.search(r'(?:proposal|提案|ID|#)\s*:?\s*(\d+)', message, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_proposal_name_from_message(self, message: str) -> Optional[str]:
        """Extract proposal name from message text for direct donation"""
        # CRITICAL: Split by '|' to ensure we only analyze the user's message, not the agent's appended response
        # which creates a "combined_text" in process_message.
        # This prevents "Donate to Gaza | I will..." from being captured as "Gaza | I will..."
        clean_message = message.split('|')[0].strip()
        
        # Look for phrases like "向 [Name] 捐款", "donate to [Name]"
        patterns = [
            r'(?:向|給)\s*([^直接\s]+(?: [^直接\s]+)*)\s*(?:直接)?(?:捐款|捐贈|捐)',
            r'donate(?:ing)?\s+(?:(?:\d+(?:\.\d+)?)\s*(?:USDC|USDT|ETH|DAI|tokens?)?\s+)?to\s+(.+)',
            r'donate\s+to\s+(.+?)(?:\s+(?:directly|now|1|usdc|usdt|eth|dai)|$)',
            r'到\s+(.+?)(?:\s+(?:直接|捐款|捐)|$|，|,)', # New: "到 [Name]"
            r'for\s+(.+?)(?:\s+(?:campaign|project)|$)',
            r'給\s*(.+?)\s*捐款',
            r'幫助\s*(.+)',
            r'^(.+?)(?:提案|project|proposal)\s*(?:我要|我想|I want|allows)', 
            r'(.*?)\s*(?:的)?幫我',
            r'向\s*(.+?)\s*(?:直接|捐)',
            r'^(.+?)(?=\s*(?:我要|我想|I want).*(?:捐|donate))',
        ]
        
        # 1. Try to extract from User Message
        for pattern in patterns:
            match = re.search(pattern, clean_message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Remove artifacts
                name = re.sub(r'(?:\s|^)\d+(\.\d+)?\s*(USDC|USDT|ETH|DAI).*$', '', name, flags=re.IGNORECASE).strip()
                name = re.sub(r'\s+(directly|now|immediately)$', '', name, flags=re.IGNORECASE).strip()
                if name and len(name) > 2: return name

        # 2. Fallback: Parse from Agent Response (if available in message)
        # message is "User Text | Agent Text"
        parts = message.split('|')
        if len(parts) > 1:
            agent_text = parts[1].strip()
            # Look for quoted name in agent response: 「Name」 or "Name"
            # Matches: 「Herat Afghanistan Earthquake」
            quote_match = re.search(r'[「"“](.+?)[」"”]', agent_text)
            if quote_match:
                print(f"--- Service: Recovered proposal name from agent response: {quote_match.group(1)} ---")
                return quote_match.group(1)
        
        return None

    def _is_donation_response(self, text: str) -> bool:
        """Detect if response suggests a donation is being prepared or discussed.
        
        More aggressive detection to ensure the UI button appears.
        """
        # Pattern 1: Keywords suggesting intent
        has_donation_intent = bool(re.search(r'捐贈|捐款|donate|donation|give|help with|支付|授權', text, re.IGNORECASE))
        
        # Pattern 2: Token amount (e.g., "1 USDC", "1USDC")
        has_token_amount = bool(re.search(r'\d+(?:\.\d+)?\s*(USDC|USDT|ETH|DAI)', text, re.IGNORECASE))
        
        # Pattern 3: Structural indicators (ETH address or Gas)
        has_structural = bool(re.search(r'0x[a-fA-F0-9]{40}|[Gg]as', text))
        
        # Exclude history/listing context - CRITICAL FIX
        # If the text explicitly mentions "records", "history", "list", "past", "total", ignore donation keywords
        if re.search(r'history|record|list|past|total|amount donated|紀錄|記錄|清單|查詢|總額|總計|捐款過', text, re.IGNORECASE):
             return False

        # Match if it has (intent AND amount) OR structural indicators
        return (has_donation_intent and has_token_amount) or has_structural

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
                        {"label": "Verify a Crisis", "type": "input_prompt", "icon": "search"}
                    ]
                }
            )

            # If we have a top crisis with coordinates, trigger FLY_TO for the first one
            if crises_list and "coordinates" in crises_list[0] and crises_list[0]["coordinates"]:
                coords = crises_list[0]["coordinates"]
                # Add fly_to action to ui_hints
                response_obj.ui_hints["actions"].insert(0, {
                    "label": f"View {crises_list[0]['title']}", 
                    "type": "FLY_TO_LOCATION", 
                    "data": {"lat": coords["lat"], "lng": coords["lng"], "zoom": 10},
                    "icon": "globe"
                })

            return response_obj

            return response_obj

        elif "query_proposals" in tool_code:
            # Extract result from tool execution if possible, or wait for next turn
            # But here we are post-execution (in process_message, 'result' is available?)
            # Actually process_message logic separates tool execution.
            # We need to handle this where 'result' is available.
            # Looking at code flow: process_message calls tool.execute, gets result.
            
            # Since this block is inside a long elif chain checking tool_code string,
            # this logic seems to be for converting tool OUTPUT to ChatResponse.
            # Let's adapt the existing pattern.
            
            proposals = result.get("proposals", []) if isinstance(result, dict) else []
            count = result.get("total_count", 0) if isinstance(result, dict) else 0
            
            if count > 0:
                top_proposal = proposals[0]
                message = f"Found {count} proposals. Top result: {top_proposal['title']} in {top_proposal.get('region', 'unknown region')}."
                
                ui_hints = {
                    "mode": "DECISION",
                    "display_data": {
                        "type": "proposal_list", 
                        "data": proposals
                    },
                    "actions": []
                }
                
                # Add View/Fly actions for the top proposal
                if "location" in top_proposal and top_proposal["location"]:
                    loc = top_proposal["location"]
                    ui_hints["actions"].append({
                        "label": f"View {top_proposal['title']}",
                        "type": "OPEN_PROPOSAL",
                        "data": {
                            "id": top_proposal["id"],
                            "lat": loc["lat"],
                            "lng": loc["lng"]
                        },
                        "icon": "eye"
                    })
                    # Also fly there immediately? Maybe just let user click.
                    # User asked: "if mentioned, fly to and open".
                    # So we should probably send a fly action automatically or as part of the response effect.
                    # But separate actions are better for UI buttons.
                    # For immediate effect, maybe we can send a "side_effect" or just put it in actions and frontend triggers it?
                    # The previous impl for list_crises added a button.
                    # Let's add a button that does BOTH fly and open.
                    
                response_obj = ChatResponse(
                    message=message,
                    action_taken="query_proposals",
                    ui_hints=ui_hints,
                    transaction_payload=None
                )
                return response_obj


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
            # Parse parameters from tool code string like: execute_donation(amount=100, token='USDC', ...)
            # This is much more robust than regex on the message
            try:
                # Extract args using regex on the code string
                # Note: This is a simple parser for named args. 
                amount_match = re.search(r"amount=['\"]?(\d+(?:\.\d+)?)['\"]?", tool_code)
                token_match = re.search(r"token=['\"](\w+)['\"]", tool_code)
                name_match = re.search(r"proposal_name=['\"](.*?)['\"]", tool_code)
                id_match = re.search(r"proposal_id=['\"](\d+)['\"]", tool_code)
                
                override_amount = float(amount_match.group(1)) if amount_match else None
                override_token = token_match.group(1) if token_match else None
                override_name = name_match.group(1) if name_match else None
                override_id = id_match.group(1) if id_match else None
                
                print(f"--- Service: Parsed Tool Args - Name: {override_name}, ID: {override_id}, Amount: {override_amount} ---")
                
                return await self._prepare_donation_response(
                    tool_code, 
                    override_amount=override_amount,
                    override_token=override_token,
                    override_proposal_name=override_name,
                    override_proposal_id=override_id
                )
            except Exception as e:
                print(f"--- Service: Error parsing tool args, falling back to regex: {e} ---")
                return await self._prepare_donation_response(tool_code)

        # Default fallback if tool code not recognized
        return ChatResponse(
            message=f"Agent requested tool execution: {tool_code}",
            action_taken="tool_code_returned",
            ui_hints={"mode": "THINKING", "actions": []}
        )

    async def _prepare_donation_response(self, text: str, 
                                         override_amount: float = None, 
                                         override_token: str = None, 
                                         override_proposal_name: str = None,
                                         override_proposal_id: str = None) -> ChatResponse:
        """Shared helper to generate a standardized donation response with payload and button."""
        # Use overrides if provided, otherwise fallback to regex extraction
        amount = override_amount if override_amount is not None else self._extract_amount_from_message(text)
        token = override_token if override_token else self._extract_token_from_message(text)
        
        # ID/Name logic: Override > Regex
        proposal_id = override_proposal_id if override_proposal_id else self._extract_proposal_id_from_message(text)
        proposal_name = override_proposal_name if override_proposal_name else self._extract_proposal_name_from_message(text)

        # Handle 'random' donation request if ID/Name are missing
        if not proposal_id and not proposal_name and any(kw in text.lower() for kw in ["隨機", "random", "any", "選一個"]):
            from gaia_link.services.blockchain.gaia_proposal import get_gaia_proposal_service
            from gaia_link.services.proposal.models import ProposalStatus
            import random
            
            p_service = get_gaia_proposal_service()
            all_proposals = await p_service.list_proposals(status=ProposalStatus.FUNDING)
            
            if all_proposals:
                selected = random.choice(all_proposals)
                proposal_id = selected.proposal_id
                proposal_name = selected.title
                print(f"--- Service: Selected random proposal: {proposal_name} (ID: {proposal_id}) ---")
                # Prepend the selection to the text so the tool sees it
                text = f"Randomly selected {proposal_name} (ID: {proposal_id}) | {text}"
        
        # Detect vault type
        vault_type = "YIELD" if any(kw in text.lower() for kw in ["無損", "yield", "lossless", "pool", "earn"]) else "DIRECT"

        # Detect if user explicitly wants to approve
        is_approval = "approve" in text.lower() or "授權" in text or "allowance" in text.lower()

        blockchain_config = get_blockchain_config()
        
        tool = ExecuteDonationTool()
        result = await tool.execute(
            amount=amount,
            token=token,
            proposal_id=proposal_id,
            proposal_name=proposal_name,
            recipient_address=blockchain_config.addresses.proposal_manager,
            vault_type=vault_type, # Pass vault_type
            action="APPROVE" if is_approval else "DEPOSIT"
        )

        # Update proposal_id if tool resolved it from name
        details = result.get("details") or {}
        if not proposal_id and details.get("proposal_id"):
             proposal_id = details["proposal_id"]
             print(f"--- Service: Updated proposal_id to {proposal_id} from tool resolution ---")

        if not result.get("success"):
            return ChatResponse(
                message=f"I couldn't prepare the donation: {result.get('error', 'Unknown error')}. Please make sure you specified a valid project name or ID.",
                action_taken="error",
                ui_hints={"mode": "IDLE", "actions": []}
            )

        # Extract proposal details
        details = result.get("details", {})
        proposal_id = details.get("proposal_id")
        proposal_name = details.get("proposal_name")
        location = details.get("location")
        
        # Base actions available for donation intents
        base_actions = []
        if location:
            base_actions.append({
                "label": f"View {proposal_name or 'Proposal'}", 
                "type": "FLY_TO_LOCATION", 
                "data": {**location, "zoom": 12}, # Very close zoom for specific proposals
                "icon": "globe"
            })

        if is_approval:
            return ChatResponse(
                message=f"I've prepared the USDC approval for {amount} {token}. Once this is signed, you can proceed with the donation.",
                action_taken="execute_donation",
                ui_hints={
                    "mode": "DECISION",
                    "display_data": {
                        "title": f"Approve {amount} {token}",
                        "badge_text": "Approval Needed",
                        "badge_color": "yellow",
                        "risk_level": "LOW"
                    },
                    "actions": base_actions + [{"label": "Sign Approval", "type": "sign_transaction", "icon": "shield-check"}]
                },
                transaction_payload=result.get("transaction_payload")
            )

        # Handle Donation (DEPOSIT)
        proposal_info = f" to Proposal #{proposal_id}" if proposal_id else ""
        
        # If USDC, we provide a sequence: [APPROVE, DEPOSIT]
        if token == "USDC":
            approve_result = await tool.execute(
                amount=amount,
                token=token,
                proposal_id=proposal_id,
                proposal_name=proposal_name,
                recipient_address=blockchain_config.addresses.proposal_manager,
                action="APPROVE"
            )

            if not approve_result.get("success"):
                return ChatResponse(
                    message=f"I couldn't prepare the approval: {approve_result.get('error', 'Unknown error')}.",
                    action_taken="error",
                    ui_hints={"mode": "IDLE", "actions": []}
                )

            approve_payload = approve_result.get("transaction_payload") or {}
            deposit_payload = result.get("transaction_payload") or {}
            
            return ChatResponse(
                message=text if len(text) > 20 else f"I've prepared the two-step donation for {amount} {token}{proposal_info}. \n\n1. **Approve**: Authorize the contract to spend your USDC.\n2. **Confirm**: Execute the actual donation.",
                action_taken="execute_donation",
                ui_hints={
                    "mode": "DECISION",
                    "display_data": {
                        "title": f"Donate {amount} {token}{proposal_info}",
                        "badge_text": "2 Steps Required",
                        "badge_color": "blue",
                        "risk_level": "LOW"
                    },
                    "actions": base_actions + [
                        {"label": "Start Donation", "type": "sign_transaction", "icon": "pen-tool"}
                    ]
                },
                transaction_payload=approve_payload, # First step
                transaction_sequence=[
                    {**approve_payload, "label": "Step 1: Approve USDC"},
                    {**deposit_payload, "label": "Step 2: Confirm Donation"}
                ]
            )

        # Default single transaction (e.g. ETH)
        return ChatResponse(
            message=text if len(text) > 20 else f"I've prepared your donation of {amount} {token}{proposal_info}.",
            action_taken="execute_donation",
            ui_hints={
                "mode": "DECISION",
                "display_data": {
                    "title": f"Donate {amount} {token}{proposal_info}",
                    "badge_text": "Ready to Sign",
                    "badge_color": "green",
                    "risk_level": "LOW"
                },
                "actions": base_actions + [
                    {"label": "Sign Donation", "type": "sign_transaction", "icon": "pen-tool"}
                ]
            },
            transaction_payload=result.get("transaction_payload")
        )
