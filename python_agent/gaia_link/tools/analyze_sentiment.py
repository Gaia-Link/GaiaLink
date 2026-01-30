"""
analyze_sentiment 工具 - 分析貼文情感

基於 SpoonOS BaseTool 實現，分析求助貼文的緊急程度和真實性。
使用服務層抽象支援 Mock 和 HuggingFace ML 模型切換。
"""

from typing import Optional

from spoon_ai.tools.base import BaseTool

from gaia_link.services.sentiment import (
    AnalysisContext,
    MockSentimentService,
    SentimentService,
)


class AnalyzeSentimentTool(BaseTool):
    """
    分析求助貼文的情感和緊急程度

    透過自然語言處理分析貼文內容，識別緊急程度、情緒指標，
    並檢測可能的詐騙特徵。

    支援依賴注入，可使用 Mock 或 HuggingFace ML 模型。
    """

    name: str = "analyze_sentiment"
    description: str = (
        "Analyze the sentiment and urgency level of a help post. "
        "Detects emotional indicators, urgency level (CRITICAL/HIGH/MEDIUM/LOW), "
        "authenticity score, and potential red flags for scam detection."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text content of the help post to analyze",
            },
            "context": {
                "type": "object",
                "description": "Optional context information",
                "properties": {
                    "post_id": {"type": "string", "description": "Post ID"},
                    "author_history": {
                        "type": "integer",
                        "description": "Author's post history count",
                    },
                    "account_age_days": {
                        "type": "integer",
                        "description": "Account age in days",
                    },
                },
            },
        },
        "required": ["text"],
    }

    def __init__(
        self,
        sentiment_service: Optional[SentimentService] = None,
        **kwargs,
    ):
        """
        初始化工具

        Args:
            sentiment_service: 可選的 Sentiment 服務實例。
                              如果未提供，將根據配置自動創建。
        """
        super().__init__(**kwargs)
        self._sentiment_service = sentiment_service

    def _get_service(self) -> SentimentService:
        """獲取 Sentiment 服務實例"""
        if self._sentiment_service is not None:
            return self._sentiment_service

        # 根據配置獲取服務
        try:
            from gaia_link.config import get_sentiment_service

            return get_sentiment_service()
        except Exception:
            # 回退到 Mock 服務
            return MockSentimentService()

    async def execute(self, text: str, context: Optional[dict] = None) -> dict:
        """
        執行情感分析

        Args:
            text: 待分析的貼文內容
            context: 可選的上下文資訊（作者歷史、帳號年齡等）

        Returns:
            分析結果字典，包含 urgency_level, authenticity_score,
            emotional_indicators, red_flags, summary
        """
        service = self._get_service()

        # 轉換上下文
        analysis_context = AnalysisContext.from_dict(context)

        # 執行分析
        result = await service.analyze(text, analysis_context)

        # 返回字典格式
        return result.to_dict()
