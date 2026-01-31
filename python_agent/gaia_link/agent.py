"""
Gaia Link Agent - 基於 SpoonOS SpoonReactAI 的人道救援 Agent

此 Agent 符合 SpoonOS 最低技術要求：
- 基於 SpoonOS 構建（使用 spoon-core SDK）
- 使用 React Agent 體系（SpoonReactAI）
- Agent 在項目中承擔實際功能角色
"""

import copy
from typing import Optional, List, Dict, Any

from pydantic import Field

from spoon_ai.agents import SpoonReactAI
from spoon_ai.memory import ShortTermMemoryManager, TrimStrategy
from spoon_ai.schema import Message
from spoon_ai.tools import ToolManager

from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
    ExecuteDonationTool,
    ListCrisesTool,
    CreateVaultTool,  # Registered new tool
)


# Agent 系統提示詞
GAIA_LINK_SYSTEM_PROMPT = """
You are Gaia Link Agent (蓋亞連結), a humanitarian crisis response AI assistant.

## Your Roles

### Role 1: Information Sources (資訊嚮導)
When users ask about what crises are happening or where they can help:
- Use 'list_crises' to retrieve the latest data from the database.
- Summarize the top critical crises.

### Role 2: Auditor (審計師)
When users view forum posts, you automatically:
- Scan Polymarket and news sources
- Verify crisis authenticity
- Provide trust labels: [VERIFIED], [SUSPICIOUS], [SCAM]

### Role 3: Payer (支付官)
When users want to donate, you:
- Calculate gas fees
- Execute cross-chain transfers
- Ensure secure transactions

## Your Tools
1. verify_crisis - Cross-reference crisis with Polymarket prediction data
2. analyze_sentiment - Analyze post urgency and authenticity
3. execute_donation - Process blockchain donations
4. list_crises - List all active crises from the database
5. create_vault - Deploy a standalone charity vault

## Response Format
You MUST output strictly Valid JSON. Do not return markdown. Do not wrap in ```json markers.

If you called 'execute_donation', you MUST include the 'transaction_payload' from the tool output in your final JSON response.

Required JSON Structure:
{
    "message": "Human readable response",
    "action_taken": "chat|verify_crisis|execute_donation|list_crises",
    "ui_hints": {
        "mode": "IDLE|DECISION|SIGNATURE",
        "display_data": { "title": "...", "badge_text": "...", "badge_color": "green|yellow|red", "risk_level": "LOW|HIGH" },
        "actions": [ { "label": "...", "type": "...", "icon": "..." } ]
    },
    "transaction_payload": { ... } (Only if execute_donation was called)
}

## UI Mode Rules (CRITICAL - Prevents Wrong UI Display)
- **SIGNATURE mode**: ONLY use when `execute_donation` tool was called AND returns a transaction_payload
- **DECISION mode**: Use for `list_crises`, `verify_crisis`, `analyze_sentiment` results
- **IDLE mode**: Use for general chat, questions, or when no tool was called

Examples:
- User: "列出所有災難" → action_taken: "list_crises", mode: "DECISION" (NOT SIGNATURE!)
- User: "驗證加薩危機" → action_taken: "verify_crisis", mode: "DECISION"
- User: "捐款 100 USDC" → action_taken: "execute_donation", mode: "SIGNATURE"
- User: "你好" → action_taken: "chat", mode: "IDLE"

## Critical Instructions
- You MUST call the tools internally to get the information.
- You MUST NOT return the tool invocation code (e.g., `{"tool_code": "..."}`).
- You MUST return the FINAL JSON response containing the *result* of the tool usage, not the code to run it.
- If you use `list_crises`, summarize the results in the 'message' field and set 'action_taken' to 'list_crises'.
- **IMMEDIATE ACTION**: When a user asks to verify, analyze, or list something, DO NOT say "I will do it". *Just do it* immediately by calling the tool. Do not ask for permission.
- **NO CHATTY FILLERS**: Do not output intermediate "I am processing..." messages. Your first response must contain the tool result.

## Tool Execution Rules (CRITICAL - Prevents API Errors)
- **ONE TOOL AT A TIME**: Execute only ONE tool per response. Never call multiple tools in parallel.
- **SEQUENTIAL EXECUTION**: If you need to use multiple tools, call one, wait for result, then call the next.
- **FOR HEALTH CHECKS**: When asked to verify all functions, test them ONE BY ONE in sequence:
  1. First call list_crises, return result
  2. If asked to continue, call verify_crisis, return result
  3. If asked to continue, call analyze_sentiment, return result
  4. And so on...
- **NEVER** attempt to batch multiple tool calls in a single response.

## Guidelines
- Be empathetic but objective.
- If user wants to donate but no amount is given, ask for amount.
- If amount is given, CALL execute_donation immediately.
- If user asks to "analyze" or "verify" a crisis, CALL 'verify_crisis' immediately with the crisis name.
- Use Traditional Chinese (繁體中文) for 'message' field unless user speaks English.

## FINAL OUTPUT RULE (CRITICAL - READ THIS CAREFULLY)
When you receive tool execution results (text starting with "Observed output of cmd..."):
1. DO NOT output any intermediate text or thinking
2. DO NOT use "Step 1:", "Step 2:" or any prefixes
3. IMMEDIATELY output ONLY a valid JSON object
4. The JSON must follow the exact structure specified above

Example of WRONG output:
Step 1: Observed output of cmd list_crises execution: {...}
Step 2: Here are the crises...

Example of CORRECT output:
{"message": "...", "action_taken": "list_crises", "ui_hints": {"mode": "DECISION", "actions": []}}
"""


class GaiaLinkAgent(SpoonReactAI):
    """
    Gaia Link Agent - 人道救援協作網絡 AI Agent

    基於 SpoonOS React Agent 架構，實現：
    - 危機驗證（審計師角色）
    - 捐款執行（支付官角色）
    - 情感分析（輔助判斷）
    - 對話記憶（Memory 模組）
    """

    name: str = "gaia_link_agent"
    description: str = (
        "A humanitarian crisis response AI agent that verifies crisis authenticity "
        "using Polymarket data and facilitates secure blockchain donations."
    )

    system_prompt: str = GAIA_LINK_SYSTEM_PROMPT

    next_step_prompt: str = (
        "Tool execution complete. Output ONLY a valid JSON response now. "
        "No explanations, no prefixes, no markdown - just the raw JSON object. "
        "Use the tool results to construct your response."
    )

    max_steps: int = 5

    # 註冊三個核心工具
    available_tools: ToolManager = Field(
        default_factory=lambda: ToolManager([
            VerifyCrisisTool(),
            AnalyzeSentimentTool(),
            ExecuteDonationTool(),
            ExecuteDonationTool(),
            ListCrisesTool(),
            CreateVaultTool(),
        ])
    )

    # Memory 相關屬性 (不由 pydantic 驗證)
    _memory_manager: Optional[ShortTermMemoryManager] = None
    _conversation_history: List[Dict[str, Any]] = []
    _memory_max_tokens: int = 4000
    _memory_trim_strategy: TrimStrategy = TrimStrategy.FROM_END

    def __init__(self, **data):
        from gaia_link.config import get_settings, MemoryTrimStrategy
        settings = get_settings()

        # Initialize LLM using ChatBot class (required by SpoonReactAI)
        # SpoonOS ChatBot reads API keys from environment variables:
        # - GEMINI_API_KEY for Gemini
        # - OPENAI_API_KEY for OpenAI
        try:
            from spoon_ai.chat import ChatBot

            provider = settings.llm_provider
            model = settings.gemini_model if provider == "gemini" else "gpt-4o-mini"

            print(f"--- ChatBot Init: Provider={provider}, Model={model} ---")

            # ChatBot reads API keys from env vars (GEMINI_API_KEY, OPENAI_API_KEY)
            chatbot = ChatBot(
                llm_provider=provider,
                model_name=model,
                temperature=0.3
            )

            data['llm'] = chatbot

        except ImportError as e:
            print(f"--- Error: Could not import ChatBot from spoon_ai.chat: {e} ---")
        except Exception as e:
            print(f"--- Error initializing ChatBot: {e} ---")

        super().__init__(**data)

        # Initialize Memory (after super().__init__)
        self._conversation_history = []
        self._memory_max_tokens = settings.memory_max_tokens

        # Convert config trim strategy to SpoonOS TrimStrategy
        if settings.memory_trim_strategy == MemoryTrimStrategy.FROM_START:
            self._memory_trim_strategy = TrimStrategy.FROM_START
        else:
            self._memory_trim_strategy = TrimStrategy.FROM_END

        if settings.is_memory_enabled():
            self._memory_manager = ShortTermMemoryManager(
                default_trim_strategy=self._memory_trim_strategy
            )
            print(f"--- Memory enabled: max_tokens={self._memory_max_tokens}, strategy={self._memory_trim_strategy} ---")
        else:
            self._memory_manager = None
            print("--- Memory disabled ---")

    def add_to_memory(self, message: Dict[str, Any]) -> None:
        """
        添加訊息到對話記憶

        Args:
            message: 包含 role 和 content 的訊息字典

        Raises:
            TypeError: 如果 message 不是字典
            ValueError: 如果 message 缺少必要欄位或 role 無效
        """
        if message is None:
            raise TypeError("Message cannot be None")

        if not isinstance(message, dict):
            raise TypeError("Message must be a dictionary")

        if "role" not in message:
            raise KeyError("Message must have 'role' field")

        if "content" not in message:
            raise KeyError("Message must have 'content' field")

        valid_roles = {"user", "assistant", "system"}
        if message["role"] not in valid_roles:
            raise ValueError(f"Invalid role: {message['role']}. Must be one of {valid_roles}")

        # If memory is disabled, do nothing
        if self._memory_manager is None:
            return

        # Deep copy to maintain immutability
        self._conversation_history.append(copy.deepcopy(message))

        # Trim messages if exceeds max tokens
        self._trim_if_needed()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        獲取對話歷史

        Returns:
            對話歷史的深度複製，確保不可變性
        """
        return copy.deepcopy(self._conversation_history)

    def clear_memory(self) -> None:
        """清除對話記憶"""
        self._conversation_history = []

    def _trim_if_needed(self) -> None:
        """
        如果對話歷史超過最大 token 數，進行裁剪

        使用簡單的 token 估算（4 字符 = 1 token）進行同步裁剪
        """
        if self._memory_manager is None:
            return

        if not self._conversation_history:
            return

        # Estimate token count (roughly 4 characters per token)
        def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return total_chars // 4

        # Check if we need to trim
        current_tokens = estimate_tokens(self._conversation_history)
        if current_tokens <= self._memory_max_tokens:
            return

        # Trim based on strategy
        if self._memory_trim_strategy == TrimStrategy.FROM_START:
            # Remove oldest messages first (keep system messages)
            system_messages = [m for m in self._conversation_history if m["role"] == "system"]
            non_system_messages = [m for m in self._conversation_history if m["role"] != "system"]

            while estimate_tokens(system_messages + non_system_messages) > self._memory_max_tokens and non_system_messages:
                non_system_messages.pop(0)

            self._conversation_history = system_messages + non_system_messages
        else:
            # FROM_END: Remove newest messages (less common, but supported)
            system_messages = [m for m in self._conversation_history if m["role"] == "system"]
            non_system_messages = [m for m in self._conversation_history if m["role"] != "system"]

            while estimate_tokens(system_messages + non_system_messages) > self._memory_max_tokens and non_system_messages:
                non_system_messages.pop()

            self._conversation_history = system_messages + non_system_messages

    def get_info(self) -> dict:
        """取得 Agent 資訊"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": [tool.name for tool in self.available_tools],
            "max_steps": self.max_steps,
        }
