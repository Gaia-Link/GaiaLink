"""
Mock Sentiment 服務實作

使用規則基礎的情感分析，用於測試和離線模式
"""

import re
from typing import Optional

from gaia_link.services.sentiment.base import (
    AnalysisContext,
    SentimentResult,
    SentimentService,
    UrgencyLevel,
)


# 緊急關鍵詞（按緊急程度分類）
URGENCY_KEYWORDS = {
    UrgencyLevel.CRITICAL: [
        "fire",
        "trapped",
        "dying",
        "救命",
        "快死",
        "被困",
        "著火",
        "溺水",
        "immediately",
        "urgent",
        "emergency",
        "緊急",
        "立即",
        "馬上",
        "life-threatening",
        "bleeding",
        "出血",
        "窒息",
        "choking",
    ],
    UrgencyLevel.HIGH: [
        "help",
        "need",
        "desperate",
        "please",
        "beg",
        "幫助",
        "求助",
        "拜託",
        "injured",
        "hurt",
        "受傷",
        "hungry",
        "飢餓",
        "homeless",
        "無家可歸",
        "medical",
        "醫療",
        "medicine",
        "藥物",
        "food",
        "water",
        "食物",
        "水",
    ],
    UrgencyLevel.MEDIUM: [
        "assistance",
        "support",
        "協助",
        "支援",
        "donation",
        "捐贈",
        "relief",
        "aid",
        "救援",
        "supplies",
        "物資",
    ],
}

# 情緒指標關鍵詞
EMOTIONAL_INDICATORS = {
    "fear": ["scared", "afraid", "terrified", "害怕", "恐懼", "擔心"],
    "desperation": ["desperate", "hopeless", "絕望", "無助", "崩潰"],
    "sadness": ["sad", "crying", "tears", "悲傷", "哭泣", "難過"],
    "anger": ["angry", "furious", "憤怒", "生氣"],
    "gratitude": ["thank", "grateful", "appreciate", "感謝", "感激"],
    "hope": ["hope", "pray", "wish", "希望", "祈禱", "期望"],
}

# 詐騙紅旗關鍵詞
SCAM_PATTERNS = [
    (r"send money now", "要求立即匯款"),
    (r"only \d+ hours left", "使用緊迫時間壓力"),
    (r"\d+% (?:guaranteed|return)", "承諾不合理的回報"),
    (r"crypto wallet", "要求轉帳到加密錢包"),
    (r"act fast", "催促立即行動"),
    (r"limited time", "使用限時策略"),
    (r"wire transfer", "要求電匯"),
    (r"western union", "要求通過 Western Union 匯款"),
    (r"bitcoin address", "提供比特幣地址"),
    (r"急需轉帳", "要求立即轉帳"),
    (r"限時", "使用限時策略"),
    (r"保證.*回報", "承諾保證回報"),
    (r"私人帳號", "要求轉帳到私人帳號"),
]


class MockSentimentService(SentimentService):
    """
    Mock Sentiment 服務

    使用規則基礎的情感分析，適用於測試和離線模式。
    遷移自原 AnalyzeSentimentTool 的邏輯。
    """

    @property
    def service_name(self) -> str:
        """服務名稱"""
        return "mock"

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
        # 驗證輸入
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")

        text_lower = text.lower()

        # 分析各項指標
        urgency_level = await self.detect_urgency(text_lower)
        emotional_indicators = await self.get_emotional_indicators(text_lower)
        red_flags = await self.detect_scam_patterns(text_lower)

        # 根據上下文添加額外紅旗
        red_flags = self._add_context_red_flags(red_flags, context)

        # 計算真實性分數
        authenticity_score = self._calculate_authenticity(
            urgency_level, emotional_indicators, red_flags, context
        )

        # 生成摘要
        summary = self._generate_summary(
            urgency_level, authenticity_score, emotional_indicators, red_flags
        )

        return SentimentResult(
            urgency_level=urgency_level,
            authenticity_score=authenticity_score,
            emotional_indicators=emotional_indicators,
            red_flags=red_flags,
            summary=summary,
        )

    async def detect_urgency(self, text: str) -> UrgencyLevel:
        """
        檢測緊急程度

        Args:
            text: 待分析的文本

        Returns:
            緊急程度等級
        """
        text_lower = text.lower()

        for level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH, UrgencyLevel.MEDIUM]:
            keywords = URGENCY_KEYWORDS[level]
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return level

        return UrgencyLevel.LOW

    async def detect_scam_patterns(self, text: str) -> list[str]:
        """
        檢測詐騙模式

        Args:
            text: 待分析的文本

        Returns:
            檢測到的詐騙模式列表
        """
        text_lower = text.lower()
        red_flags = []

        for pattern, warning in SCAM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if warning not in red_flags:
                    red_flags.append(warning)

        return red_flags

    async def get_emotional_indicators(self, text: str) -> list[str]:
        """
        獲取情緒指標

        Args:
            text: 待分析的文本

        Returns:
            檢測到的情緒指標列表
        """
        text_lower = text.lower()
        detected_emotions = []

        for emotion, keywords in EMOTIONAL_INDICATORS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    detected_emotions.append(emotion)
                    break

        return detected_emotions

    def _add_context_red_flags(
        self,
        red_flags: list[str],
        context: Optional[AnalysisContext],
    ) -> list[str]:
        """根據上下文添加額外紅旗"""
        result = red_flags.copy()

        if context:
            # 新帳號添加紅旗
            if context.account_age_days is not None and context.account_age_days < 30:
                result.append("New account (less than 30 days old)")

            # 無歷史紀錄添加紅旗
            if context.author_history is not None and context.author_history == 0:
                result.append("No previous post history")

        return result

    def _calculate_authenticity(
        self,
        urgency_level: UrgencyLevel,
        emotional_indicators: list[str],
        red_flags: list[str],
        context: Optional[AnalysisContext],
    ) -> int:
        """計算真實性分數"""
        base_score = 70

        # 根據紅旗減分
        red_flag_penalty = len(red_flags) * 15
        base_score -= red_flag_penalty

        # 根據情緒指標調整
        if emotional_indicators:
            # 有情緒表達通常更真實
            base_score += min(len(emotional_indicators) * 5, 15)

        # 根據上下文調整
        if context:
            # 新帳號減分
            if context.account_age_days is not None and context.account_age_days < 30:
                base_score -= 20

            # 有歷史紀錄加分
            if context.author_history is not None and context.author_history > 10:
                base_score += 10

        # 確保分數在 0-100 範圍內
        return max(0, min(100, base_score))

    def _generate_summary(
        self,
        urgency_level: UrgencyLevel,
        authenticity_score: int,
        emotional_indicators: list[str],
        red_flags: list[str],
    ) -> str:
        """生成分析摘要"""
        summary_parts = []

        # 緊急程度描述
        urgency_desc = {
            UrgencyLevel.CRITICAL: "此貼文顯示出極度緊急的求助信號",
            UrgencyLevel.HIGH: "此貼文具有較高的緊急程度",
            UrgencyLevel.MEDIUM: "此貼文顯示中等程度的求助需求",
            UrgencyLevel.LOW: "此貼文的緊急程度較低",
        }
        summary_parts.append(urgency_desc.get(urgency_level, ""))

        # 真實性評估
        if authenticity_score >= 70:
            summary_parts.append("真實性評估為可信")
        elif authenticity_score >= 40:
            summary_parts.append("真實性評估為需要進一步查證")
        else:
            summary_parts.append("真實性評估為可疑，建議謹慎")

        # 情緒指標
        if emotional_indicators:
            emotions_str = ", ".join(emotional_indicators[:3])
            summary_parts.append(f"檢測到的情緒包括: {emotions_str}")

        # 紅旗警告
        if red_flags:
            summary_parts.append(f"發現 {len(red_flags)} 個可疑特徵")

        return ". ".join(summary_parts) + "."
