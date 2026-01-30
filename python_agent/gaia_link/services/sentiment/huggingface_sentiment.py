"""
HuggingFace Sentiment 服務實作

使用 HuggingFace Transformers 進行 ML 基礎的情感分析
"""

import asyncio
from typing import Optional

from gaia_link.services.sentiment.base import (
    AnalysisContext,
    SentimentResult,
    SentimentService,
    UrgencyLevel,
)
from gaia_link.services.sentiment.mock_sentiment import (
    EMOTIONAL_INDICATORS,
    SCAM_PATTERNS,
    URGENCY_KEYWORDS,
    MockSentimentService,
)

# 預設模型名稱
DEFAULT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

# 情感標籤映射
SENTIMENT_LABEL_MAP = {
    "POSITIVE": "positive",
    "NEGATIVE": "negative",
    "NEUTRAL": "neutral",
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
}


class HuggingFaceSentimentService(SentimentService):
    """
    HuggingFace Sentiment 服務

    使用 HuggingFace Transformers 進行 ML 基礎的情感分析。
    結合 ML 模型輸出和規則基礎的緊急程度/詐騙檢測。
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        max_length: int = 512,
    ):
        """
        初始化 HuggingFace Sentiment 服務

        Args:
            model_name: HuggingFace 模型名稱
            device: 執行設備 (cpu/cuda)
            max_length: 最大輸入長度
        """
        self._model_name = model_name
        self._device = device
        self._max_length = max_length
        self._pipeline = None
        self._mock_service = MockSentimentService()

    @property
    def service_name(self) -> str:
        """服務名稱"""
        return "huggingface"

    def _get_pipeline(self):
        """延遲載入 pipeline"""
        if self._pipeline is None:
            try:
                from transformers import pipeline

                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model=self._model_name,
                    device=self._device,
                    truncation=True,
                    max_length=self._max_length,
                )
            except ImportError:
                raise ImportError(
                    "transformers package is required for HuggingFace sentiment service. "
                    "Install it with: pip install transformers torch"
                )
        return self._pipeline

    async def analyze(
        self,
        text: str,
        context: Optional[AnalysisContext] = None,
    ) -> SentimentResult:
        """
        分析文本情感

        結合 HuggingFace ML 模型和規則基礎的分析。

        Args:
            text: 待分析的文本
            context: 可選的上下文資訊

        Returns:
            情感分析結果
        """
        # 驗證輸入
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")

        # 使用 ML 模型進行情感分析
        ml_result = await self._run_ml_inference(text)

        # 使用規則基礎的分析
        urgency_level = await self.detect_urgency(text)
        emotional_indicators = await self.get_emotional_indicators(text)
        red_flags = await self.detect_scam_patterns(text)

        # 根據上下文添加額外紅旗
        red_flags = self._mock_service._add_context_red_flags(red_flags, context)

        # 計算真實性分數（結合 ML 結果）
        authenticity_score = self._calculate_authenticity_with_ml(
            urgency_level,
            emotional_indicators,
            red_flags,
            context,
            ml_result,
        )

        # 生成摘要
        summary = self._generate_summary_with_ml(
            urgency_level,
            authenticity_score,
            emotional_indicators,
            red_flags,
            ml_result,
        )

        return SentimentResult(
            urgency_level=urgency_level,
            authenticity_score=authenticity_score,
            emotional_indicators=emotional_indicators,
            red_flags=red_flags,
            summary=summary,
            sentiment_label=ml_result.get("label"),
            sentiment_score=ml_result.get("score"),
            model_name=self._model_name,
        )

    async def _run_ml_inference(self, text: str) -> dict:
        """
        執行 ML 推理

        Args:
            text: 待分析的文本

        Returns:
            ML 推理結果 {"label": str, "score": float}
        """
        pipeline = self._get_pipeline()

        # 在線程池中執行以避免阻塞
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: pipeline(text)[0])

        # 標準化標籤
        label = SENTIMENT_LABEL_MAP.get(result["label"], result["label"].lower())

        return {
            "label": label,
            "score": round(result["score"], 4),
        }

    async def detect_urgency(self, text: str) -> UrgencyLevel:
        """
        檢測緊急程度

        使用規則基礎的方法（與 MockSentimentService 相同）。

        Args:
            text: 待分析的文本

        Returns:
            緊急程度等級
        """
        return await self._mock_service.detect_urgency(text)

    async def detect_scam_patterns(self, text: str) -> list[str]:
        """
        檢測詐騙模式

        使用規則基礎的方法（與 MockSentimentService 相同）。

        Args:
            text: 待分析的文本

        Returns:
            檢測到的詐騙模式列表
        """
        return await self._mock_service.detect_scam_patterns(text)

    async def get_emotional_indicators(self, text: str) -> list[str]:
        """
        獲取情緒指標

        使用規則基礎的方法（與 MockSentimentService 相同）。

        Args:
            text: 待分析的文本

        Returns:
            檢測到的情緒指標列表
        """
        return await self._mock_service.get_emotional_indicators(text)

    def _calculate_authenticity_with_ml(
        self,
        urgency_level: UrgencyLevel,
        emotional_indicators: list[str],
        red_flags: list[str],
        context: Optional[AnalysisContext],
        ml_result: dict,
    ) -> int:
        """計算真實性分數（結合 ML 結果）"""
        # 從規則基礎獲取基礎分數
        base_score = self._mock_service._calculate_authenticity(
            urgency_level, emotional_indicators, red_flags, context
        )

        # 根據 ML 情感結果調整
        sentiment_label = ml_result.get("label", "")
        sentiment_score = ml_result.get("score", 0.5)

        # 負面情感可能表示真實的求助
        if sentiment_label == "negative" and sentiment_score > 0.8:
            # 高置信度的負面情感，在緊急情況下可能更真實
            if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
                base_score += 5

        # 正面情感在緊急求助中可能是紅旗
        elif sentiment_label == "positive" and sentiment_score > 0.8:
            if urgency_level == UrgencyLevel.CRITICAL:
                base_score -= 5  # 緊急求助但情感正面可能是詐騙

        return max(0, min(100, base_score))

    def _generate_summary_with_ml(
        self,
        urgency_level: UrgencyLevel,
        authenticity_score: int,
        emotional_indicators: list[str],
        red_flags: list[str],
        ml_result: dict,
    ) -> str:
        """生成分析摘要（包含 ML 結果）"""
        # 使用規則基礎生成基礎摘要
        base_summary = self._mock_service._generate_summary(
            urgency_level, authenticity_score, emotional_indicators, red_flags
        )

        # 添加 ML 分析結果
        sentiment_label = ml_result.get("label", "unknown")
        sentiment_score = ml_result.get("score", 0)

        ml_summary = f"ML 情感分析: {sentiment_label} (置信度: {sentiment_score:.1%})"

        return f"{base_summary} {ml_summary}."
