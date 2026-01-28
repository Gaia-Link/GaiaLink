"""
Gaia Link Agent - 基於 SpoonOS 的人道救援 AI Agent

此模組實現了符合 SpoonOS 最低技術要求的 React Agent：
- 使用 SpoonReactAI 作為核心 Agent 架構
- 三個自定義工具繼承 BaseTool
- 支援危機驗證、情感分析、捐款執行
"""

from gaia_link.agent import GaiaLinkAgent
from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
)

__version__ = "1.0.0"
__all__ = [
    "GaiaLinkAgent",
    "VerifyCrisisTool",
    "AnalyzeSentimentTool",
    "ExecuteDonationTool",
]
