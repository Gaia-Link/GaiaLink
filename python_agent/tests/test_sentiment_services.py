"""
Sentiment 服務層單元測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest

from gaia_link.services.sentiment import (
    AnalysisContext,
    MockSentimentService,
    SentimentResult,
    SentimentService,
    UrgencyLevel,
)


class TestUrgencyLevel:
    """UrgencyLevel 枚舉測試"""

    def test_critical_value(self):
        """CRITICAL 應有正確的值"""
        assert UrgencyLevel.CRITICAL.value == "CRITICAL"

    def test_high_value(self):
        """HIGH 應有正確的值"""
        assert UrgencyLevel.HIGH.value == "HIGH"

    def test_medium_value(self):
        """MEDIUM 應有正確的值"""
        assert UrgencyLevel.MEDIUM.value == "MEDIUM"

    def test_low_value(self):
        """LOW 應有正確的值"""
        assert UrgencyLevel.LOW.value == "LOW"


class TestSentimentResult:
    """SentimentResult 數據類測試"""

    def test_create_basic_result(self):
        """應能建立基本結果"""
        result = SentimentResult(
            urgency_level=UrgencyLevel.HIGH,
            authenticity_score=75,
        )
        assert result.urgency_level == UrgencyLevel.HIGH
        assert result.authenticity_score == 75
        assert result.emotional_indicators == []
        assert result.red_flags == []

    def test_create_full_result(self):
        """應能建立完整結果"""
        result = SentimentResult(
            urgency_level=UrgencyLevel.CRITICAL,
            authenticity_score=85,
            emotional_indicators=["fear", "desperation"],
            red_flags=["new account"],
            summary="Urgent request detected",
            sentiment_label="negative",
            sentiment_score=0.92,
            model_name="distilbert-base-uncased-finetuned-sst-2-english",
        )
        assert result.sentiment_label == "negative"
        assert result.sentiment_score == 0.92
        assert result.model_name is not None

    def test_to_dict_basic(self):
        """to_dict 應返回基本字典"""
        result = SentimentResult(
            urgency_level=UrgencyLevel.MEDIUM,
            authenticity_score=60,
        )
        data = result.to_dict()

        assert data["urgency_level"] == "MEDIUM"
        assert data["authenticity_score"] == 60
        assert "sentiment_label" not in data

    def test_to_dict_with_ml_fields(self):
        """to_dict 應包含 ML 欄位（當存在時）"""
        result = SentimentResult(
            urgency_level=UrgencyLevel.HIGH,
            authenticity_score=70,
            sentiment_label="negative",
            sentiment_score=0.85,
            model_name="test-model",
        )
        data = result.to_dict()

        assert data["sentiment_label"] == "negative"
        assert data["sentiment_score"] == 0.85
        assert data["model_name"] == "test-model"


class TestAnalysisContext:
    """AnalysisContext 數據類測試"""

    def test_create_empty_context(self):
        """應能建立空上下文"""
        context = AnalysisContext()
        assert context.post_id is None
        assert context.author_history is None
        assert context.account_age_days is None

    def test_create_full_context(self):
        """應能建立完整上下文"""
        context = AnalysisContext(
            post_id="post_123",
            author_history=50,
            account_age_days=365,
        )
        assert context.post_id == "post_123"
        assert context.author_history == 50
        assert context.account_age_days == 365

    def test_from_dict_none(self):
        """from_dict 應處理 None"""
        context = AnalysisContext.from_dict(None)
        assert context is None

    def test_from_dict_empty(self):
        """from_dict 應處理空字典"""
        context = AnalysisContext.from_dict({})
        assert context is not None
        assert context.post_id is None

    def test_from_dict_full(self):
        """from_dict 應處理完整字典"""
        data = {
            "post_id": "post_456",
            "author_history": 100,
            "account_age_days": 730,
        }
        context = AnalysisContext.from_dict(data)
        assert context.post_id == "post_456"
        assert context.author_history == 100
        assert context.account_age_days == 730


class TestMockSentimentService:
    """MockSentimentService 測試"""

    @pytest.fixture
    def service(self):
        """建立服務實例"""
        return MockSentimentService()

    def test_service_name(self, service):
        """服務名稱應為 mock"""
        assert service.service_name == "mock"

    @pytest.mark.asyncio
    async def test_analyze_urgent_text(self, service):
        """緊急文本應返回高緊急程度"""
        text = "Help! My house is on fire! People are trapped inside!"
        result = await service.analyze(text)

        assert isinstance(result, SentimentResult)
        assert result.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]
        assert 0 <= result.authenticity_score <= 100

    @pytest.mark.asyncio
    async def test_analyze_casual_text(self, service):
        """普通文本應返回低緊急程度"""
        text = "The weather is nice today."
        result = await service.analyze(text)

        assert result.urgency_level == UrgencyLevel.LOW

    @pytest.mark.asyncio
    async def test_analyze_with_context(self, service):
        """應能處理帶上下文的分析"""
        text = "We need medical supplies urgently"
        context = AnalysisContext(
            post_id="post_123",
            author_history=50,
            account_age_days=365,
        )
        result = await service.analyze(text, context)

        # 有歷史紀錄的帳號應有更高的可信度
        assert result.authenticity_score >= 50

    @pytest.mark.asyncio
    async def test_analyze_new_account(self, service):
        """新帳號應降低可信度"""
        text = "Emergency! Need immediate help!"
        context = AnalysisContext(
            post_id="post_456",
            author_history=0,
            account_age_days=1,
        )
        result = await service.analyze(text, context)

        # 新帳號應有紅旗
        assert len(result.red_flags) > 0

    @pytest.mark.asyncio
    async def test_analyze_scam_text(self, service):
        """詐騙文本應檢測出紅旗"""
        text = "URGENT: Send money NOW to this crypto wallet! 1000% guaranteed return!"
        result = await service.analyze(text)

        assert len(result.red_flags) > 0
        assert result.authenticity_score < 50

    @pytest.mark.asyncio
    async def test_detect_urgency_critical(self, service):
        """應檢測出 CRITICAL 緊急程度"""
        text = "fire trapped dying emergency immediately"
        level = await service.detect_urgency(text)
        assert level == UrgencyLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_detect_urgency_high(self, service):
        """應檢測出 HIGH 緊急程度"""
        text = "We desperately need medical help and food"
        level = await service.detect_urgency(text)
        assert level == UrgencyLevel.HIGH

    @pytest.mark.asyncio
    async def test_detect_urgency_medium(self, service):
        """應檢測出 MEDIUM 緊急程度"""
        text = "Requesting assistance with relief supplies for donation"
        level = await service.detect_urgency(text)
        assert level == UrgencyLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_detect_urgency_low(self, service):
        """應檢測出 LOW 緊急程度"""
        text = "Just checking in to say hello"
        level = await service.detect_urgency(text)
        assert level == UrgencyLevel.LOW

    @pytest.mark.asyncio
    async def test_detect_scam_patterns(self, service):
        """應檢測詐騙模式"""
        text = "Send money now! Only 24 hours left! Act fast!"
        patterns = await service.detect_scam_patterns(text)

        assert len(patterns) > 0
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_detect_scam_patterns_clean(self, service):
        """乾淨文本應無詐騙模式"""
        text = "Our village was hit by earthquake. We need tents."
        patterns = await service.detect_scam_patterns(text)

        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_get_emotional_indicators(self, service):
        """應檢測情緒指標"""
        text = "I'm so scared and desperate. Please help us!"
        indicators = await service.get_emotional_indicators(text)

        assert len(indicators) > 0
        assert "fear" in indicators or "desperation" in indicators

    @pytest.mark.asyncio
    async def test_get_emotional_indicators_empty(self, service):
        """無情緒文本應返回空列表"""
        text = "Request for supplies: 10 boxes of medicine."
        indicators = await service.get_emotional_indicators(text)

        assert isinstance(indicators, list)

    @pytest.mark.asyncio
    async def test_analyze_chinese_text(self, service):
        """應支援中文文本"""
        text = "救命！地震了！房子倒塌，人被困住了！"
        result = await service.analyze(text)

        assert result.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]

    @pytest.mark.asyncio
    async def test_analyze_empty_text_raises_error(self, service):
        """空文本應拋出錯誤"""
        with pytest.raises(ValueError):
            await service.analyze("")


class TestSentimentServiceDependencyInjection:
    """SentimentService 依賴注入測試"""

    @pytest.fixture
    def mock_service(self):
        """建立 Mock 服務實例"""
        return MockSentimentService()

    def test_is_abstract(self):
        """SentimentService 應為抽象類"""
        with pytest.raises(TypeError):
            SentimentService()  # type: ignore

    def test_mock_is_instance_of_base(self, mock_service):
        """MockSentimentService 應為 SentimentService 的實例"""
        assert isinstance(mock_service, SentimentService)
