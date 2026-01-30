"""
Sentiment 服務抽象基類

定義情感分析操作的介面
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class UrgencyLevel(str, Enum):
    """緊急程度等級"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class SentimentResult:
    """情感分析結果"""

    urgency_level: UrgencyLevel
    authenticity_score: int  # 0-100
    emotional_indicators: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    summary: str = ""

    # ML 模型專用欄位
    sentiment_label: Optional[str] = None  # positive, negative, neutral
    sentiment_score: Optional[float] = None  # 模型置信度 0-1
    model_name: Optional[str] = None  # 使用的模型名稱

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        result = {
            "urgency_level": self.urgency_level.value,
            "authenticity_score": self.authenticity_score,
            "emotional_indicators": self.emotional_indicators,
            "red_flags": self.red_flags,
            "summary": self.summary,
        }

        # 僅在有 ML 結果時包含這些欄位
        if self.sentiment_label is not None:
            result["sentiment_label"] = self.sentiment_label
        if self.sentiment_score is not None:
            result["sentiment_score"] = self.sentiment_score
        if self.model_name is not None:
            result["model_name"] = self.model_name

        return result


@dataclass
class AnalysisContext:
    """分析上下文資訊"""

    post_id: Optional[str] = None
    author_history: Optional[int] = None
    account_age_days: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["AnalysisContext"]:
        """從字典建立上下文"""
        if data is None:
            return None
        return cls(
            post_id=data.get("post_id"),
            author_history=data.get("author_history"),
            account_age_days=data.get("account_age_days"),
        )


class SentimentService(ABC):
    """
    Sentiment 服務抽象基類

    定義情感分析的標準介面
    """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """服務名稱 (mock/huggingface)"""
        pass

    @abstractmethod
    async def analyze(
        self,
        text: str,
        context: Optional[AnalysisContext] = None,
    ) -> SentimentResult:
        """
        分析文本情感

        Args:
            text: 待分析的文本
            context: 可選的上下文資訊

        Returns:
            情感分析結果
        """
        pass

    @abstractmethod
    async def detect_urgency(self, text: str) -> UrgencyLevel:
        """
        檢測緊急程度

        Args:
            text: 待分析的文本

        Returns:
            緊急程度等級
        """
        pass

    @abstractmethod
    async def detect_scam_patterns(self, text: str) -> list[str]:
        """
        檢測詐騙模式

        Args:
            text: 待分析的文本

        Returns:
            檢測到的詐騙模式列表
        """
        pass

    @abstractmethod
    async def get_emotional_indicators(self, text: str) -> list[str]:
        """
        獲取情緒指標

        Args:
            text: 待分析的文本

        Returns:
            檢測到的情緒指標列表
        """
        pass
