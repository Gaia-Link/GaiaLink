"""
analyze_sentiment 工具 - 分析貼文情感

基於 SpoonOS BaseTool 實現，分析求助貼文的緊急程度和真實性
"""

import re
from typing import Optional

from spoon_ai.tools.base import BaseTool

# 緊急關鍵詞（按緊急程度分類）
URGENCY_KEYWORDS = {
    "CRITICAL": [
        "fire", "trapped", "dying", "救命", "快死", "被困", "著火", "溺水",
        "immediately", "urgent", "emergency", "緊急", "立即", "馬上",
        "life-threatening", "bleeding", "出血", "窒息", "choking"
    ],
    "HIGH": [
        "help", "need", "desperate", "please", "beg", "幫助", "求助", "拜託",
        "injured", "hurt", "受傷", "hungry", "飢餓", "homeless", "無家可歸",
        "medical", "醫療", "medicine", "藥物", "food", "water", "食物", "水"
    ],
    "MEDIUM": [
        "assistance", "support", "協助", "支援", "donation", "捐贈",
        "relief", "aid", "救援", "supplies", "物資"
    ]
}

# 情緒指標關鍵詞
EMOTIONAL_INDICATORS = {
    "fear": ["scared", "afraid", "terrified", "害怕", "恐懼", "擔心"],
    "desperation": ["desperate", "hopeless", "絕望", "無助", "崩潰"],
    "sadness": ["sad", "crying", "tears", "悲傷", "哭泣", "難過"],
    "anger": ["angry", "furious", "憤怒", "生氣"],
    "gratitude": ["thank", "grateful", "appreciate", "感謝", "感激"],
    "hope": ["hope", "pray", "wish", "希望", "祈禱", "期望"]
}

# 詐騙紅旗關鍵詞
SCAM_PATTERNS = [
    r"send money now",
    r"only \d+ hours left",
    r"\d+% (?:guaranteed|return)",
    r"crypto wallet",
    r"act fast",
    r"limited time",
    r"wire transfer",
    r"western union",
    r"bitcoin address",
    r"急需轉帳",
    r"限時",
    r"保證.*回報",
    r"私人帳號",
]


class AnalyzeSentimentTool(BaseTool):
    """
    分析求助貼文的情感和緊急程度

    透過自然語言處理分析貼文內容，識別緊急程度、情緒指標，
    並檢測可能的詐騙特徵。
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
                "description": "The text content of the help post to analyze"
            },
            "context": {
                "type": "object",
                "description": "Optional context information",
                "properties": {
                    "post_id": {"type": "string", "description": "Post ID"},
                    "author_history": {"type": "integer", "description": "Author's post history count"},
                    "account_age_days": {"type": "integer", "description": "Account age in days"}
                }
            }
        },
        "required": ["text"]
    }

    async def execute(self, text: str, context: Optional[dict] = None) -> dict:
        """
        執行情感分析

        Args:
            text: 待分析的貼文內容
            context: 可選的上下文資訊（作者歷史、帳號年齡等）

        Returns:
            分析結果字典，包含 urgency_level, authenticity_score, emotional_indicators, red_flags, summary
        """
        # 驗證輸入
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")

        text_lower = text.lower()

        # 分析緊急程度
        urgency_level = self._analyze_urgency(text_lower)

        # 分析情緒指標
        emotional_indicators = self._analyze_emotions(text_lower)

        # 檢測詐騙紅旗
        red_flags = self._detect_scam_patterns(text_lower)

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

        return {
            "urgency_level": urgency_level,
            "authenticity_score": authenticity_score,
            "emotional_indicators": emotional_indicators,
            "red_flags": red_flags,
            "summary": summary
        }

    def _analyze_urgency(self, text: str) -> str:
        """分析緊急程度"""
        for level in ["CRITICAL", "HIGH", "MEDIUM"]:
            keywords = URGENCY_KEYWORDS[level]
            for keyword in keywords:
                if keyword.lower() in text:
                    return level
        return "LOW"

    def _analyze_emotions(self, text: str) -> list[str]:
        """分析情緒指標"""
        detected_emotions = []

        for emotion, keywords in EMOTIONAL_INDICATORS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    detected_emotions.append(emotion)
                    break

        return detected_emotions

    def _detect_scam_patterns(self, text: str) -> list[str]:
        """檢測詐騙模式"""
        red_flags = []

        for pattern in SCAM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # 轉換模式為可讀的警告
                warning = self._pattern_to_warning(pattern)
                if warning not in red_flags:
                    red_flags.append(warning)

        return red_flags

    def _pattern_to_warning(self, pattern: str) -> str:
        """將正則模式轉換為可讀警告"""
        warnings = {
            r"send money now": "要求立即匯款",
            r"only \d+ hours left": "使用緊迫時間壓力",
            r"\d+% (?:guaranteed|return)": "承諾不合理的回報",
            r"crypto wallet": "要求轉帳到加密錢包",
            r"act fast": "催促立即行動",
            r"limited time": "使用限時策略",
            r"wire transfer": "要求電匯",
            r"western union": "要求通過 Western Union 匯款",
            r"bitcoin address": "提供比特幣地址",
            r"急需轉帳": "要求立即轉帳",
            r"限時": "使用限時策略",
            r"保證.*回報": "承諾保證回報",
            r"私人帳號": "要求轉帳到私人帳號",
        }
        return warnings.get(pattern, f"可疑模式: {pattern}")

    def _add_context_red_flags(self, red_flags: list[str], context: Optional[dict]) -> list[str]:
        """根據上下文添加額外紅旗"""
        result = red_flags.copy()

        if context:
            account_age = context.get("account_age_days")
            author_history = context.get("author_history")

            # 新帳號添加紅旗
            if account_age is not None and account_age < 30:
                result.append("New account (less than 30 days old)")

            # 無歷史紀錄添加紅旗
            if author_history is not None and author_history == 0:
                result.append("No previous post history")

        return result

    def _calculate_authenticity(
        self,
        urgency_level: str,
        emotional_indicators: list[str],
        red_flags: list[str],
        context: Optional[dict]
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
            account_age = context.get("account_age_days", 0)
            author_history = context.get("author_history", 0)

            # 新帳號減分
            if account_age is not None and account_age < 30:
                base_score -= 20
                # 這裡不能直接修改 red_flags，因為它是參數

            # 有歷史紀錄加分
            if author_history is not None and author_history > 10:
                base_score += 10

        # 確保分數在 0-100 範圍內
        return max(0, min(100, base_score))

    def _generate_summary(
        self,
        urgency_level: str,
        authenticity_score: int,
        emotional_indicators: list[str],
        red_flags: list[str]
    ) -> str:
        """生成分析摘要"""
        summary_parts = []

        # 緊急程度描述
        urgency_desc = {
            "CRITICAL": "此貼文顯示出極度緊急的求助信號",
            "HIGH": "此貼文具有較高的緊急程度",
            "MEDIUM": "此貼文顯示中等程度的求助需求",
            "LOW": "此貼文的緊急程度較低"
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
            emotions_str = "、".join(emotional_indicators[:3])
            summary_parts.append(f"檢測到的情緒包括: {emotions_str}")

        # 紅旗警告
        if red_flags:
            summary_parts.append(f"發現 {len(red_flags)} 個可疑特徵")

        return "。".join(summary_parts) + "。"
