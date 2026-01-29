"""
Gaia Link Agent - 基於 SpoonOS 的人道救援 AI Agent

此模組實現了符合 SpoonOS 最低技術要求的 React Agent：
- 使用 SpoonReactAI 作為核心 Agent 架構
- 三個自定義工具繼承 BaseTool
- 支援危機驗證、情感分析、捐款執行
- 可切換的區塊鏈服務層（Mock/Sepolia）
"""

from gaia_link.agent import GaiaLinkAgent
from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
)
from gaia_link.config import get_settings, get_blockchain_service, Settings
from gaia_link.services import (
    BlockchainService,
    TransactionResult,
    MockBlockchainService,
)

__version__ = "1.1.0"
__all__ = [
    # Agent
    "GaiaLinkAgent",
    # Tools
    "VerifyCrisisTool",
    "AnalyzeSentimentTool",
    "ExecuteDonationTool",
    # Config
    "get_settings",
    "get_blockchain_service",
    "Settings",
    # Services
    "BlockchainService",
    "TransactionResult",
    "MockBlockchainService",
]
