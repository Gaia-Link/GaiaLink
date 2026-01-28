"""
Gaia Link Agent - 基於 SpoonOS SpoonReactAI 的人道救援 Agent

此 Agent 符合 SpoonOS 最低技術要求：
- 基於 SpoonOS 構建（使用 spoon-core SDK）
- 使用 React Agent 體系（SpoonReactAI）
- Agent 在項目中承擔實際功能角色
"""

from pydantic import Field

from spoon_ai.agents import SpoonReactAI
from spoon_ai.tools import ToolManager

from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
)


# Agent 系統提示詞
GAIA_LINK_SYSTEM_PROMPT = """
You are Gaia Link Agent (蓋亞連結), a humanitarian crisis response AI assistant.

## Your Roles

### Role 1: Auditor (審計師)
When users view forum posts, you automatically:
- Scan Polymarket and news sources
- Verify crisis authenticity
- Provide trust labels: [VERIFIED], [SUSPICIOUS], [SCAM]

### Role 2: Payer (支付官)
When users want to donate, you:
- Calculate gas fees
- Execute cross-chain transfers
- Ensure secure transactions

## Your Tools
1. verify_crisis - Cross-reference crisis with Polymarket prediction data
2. analyze_sentiment - Analyze post urgency and authenticity
3. execute_donation - Process blockchain donations

## Response Format
Always respond in JSON format that is frontend-friendly:
{
    "message": "Human readable response",
    "action_taken": "action_name",
    "recommendation": {
        "action": "PROCEED|CAUTION|ABORT",
        "confidence": 0-100,
        "reason": "explanation"
    }
}

## Guidelines
- Be empathetic but objective in crisis verification
- Prioritize user safety and fund security
- Provide clear, actionable recommendations
- Use Traditional Chinese (繁體中文) for responses when appropriate
"""


class GaiaLinkAgent(SpoonReactAI):
    """
    Gaia Link Agent - 人道救援協作網絡 AI Agent

    基於 SpoonOS React Agent 架構，實現：
    - 危機驗證（審計師角色）
    - 捐款執行（支付官角色）
    - 情感分析（輔助判斷）
    """

    name: str = "gaia_link_agent"
    description: str = (
        "A humanitarian crisis response AI agent that verifies crisis authenticity "
        "using Polymarket data and facilitates secure blockchain donations."
    )

    system_prompt: str = GAIA_LINK_SYSTEM_PROMPT

    next_step_prompt: str = (
        "Based on the previous analysis, determine the next action. "
        "If crisis verification is complete, provide a recommendation. "
        "If donation is requested, verify recipient and execute transaction."
    )

    max_steps: int = 5

    # 註冊三個核心工具
    available_tools: ToolManager = Field(
        default_factory=lambda: ToolManager([
            VerifyCrisisTool(),
            AnalyzeSentimentTool(),
            ExecuteDonationTool(),
        ])
    )

    def get_info(self) -> dict:
        """取得 Agent 資訊"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": [tool.name for tool in self.available_tools],
            "max_steps": self.max_steps,
        }
