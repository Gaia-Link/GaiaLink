"""
Gaia Link Sentiment Services - 情感分析服務層

提供可替換的情感分析實作，支援 Mock 和 HuggingFace 模型切換
"""

from gaia_link.services.sentiment.base import (
    AnalysisContext,
    SentimentResult,
    SentimentService,
    UrgencyLevel,
)

# Mock 服務可直接導入
from gaia_link.services.sentiment.mock_sentiment import MockSentimentService


# HuggingFace 服務需要 transformers 依賴，延遲導入
def get_huggingface_sentiment_service(*args, **kwargs):
    """工廠函數：創建 HuggingFaceSentimentService 實例"""
    from gaia_link.services.sentiment.huggingface_sentiment import (
        HuggingFaceSentimentService,
    )

    return HuggingFaceSentimentService(*args, **kwargs)


__all__ = [
    "SentimentService",
    "SentimentResult",
    "AnalysisContext",
    "UrgencyLevel",
    "MockSentimentService",
    "get_huggingface_sentiment_service",
]
