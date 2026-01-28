"""
analyze_sentiment 工具單元測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest

from gaia_link.tools.analyze_sentiment import AnalyzeSentimentTool


class TestAnalyzeSentimentTool:
    """analyze_sentiment 工具測試"""

    @pytest.fixture
    def tool(self):
        """建立工具實例"""
        return AnalyzeSentimentTool()

    def test_tool_has_correct_name(self, tool):
        """工具應有正確的名稱"""
        assert tool.name == "analyze_sentiment"

    def test_tool_has_description(self, tool):
        """工具應有描述"""
        assert len(tool.description) > 0
        assert "sentiment" in tool.description.lower() or "analyze" in tool.description.lower()

    def test_tool_has_required_parameters(self, tool):
        """工具應有必要的參數定義"""
        assert "text" in tool.parameters["properties"]
        assert "text" in tool.parameters["required"]

    @pytest.mark.asyncio
    async def test_execute_returns_critical_for_urgent_text(self, tool):
        """緊急求救文本應返回 CRITICAL 緊急程度"""
        urgent_text = "Please help! My house is on fire, people are trapped inside! We need rescue immediately!"

        result = await tool.execute(text=urgent_text)

        assert "urgency_level" in result
        assert result["urgency_level"] in ["CRITICAL", "HIGH"]
        assert "authenticity_score" in result
        assert 0 <= result["authenticity_score"] <= 100
        assert "emotional_indicators" in result
        assert "red_flags" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_execute_returns_low_for_casual_text(self, tool):
        """普通文本應返回 LOW 緊急程度"""
        casual_text = "The weather is nice today. I'm going for a walk."

        result = await tool.execute(text=casual_text)

        assert result["urgency_level"] in ["LOW", "MEDIUM"]

    @pytest.mark.asyncio
    async def test_execute_detects_scam_patterns(self, tool):
        """應能檢測詐騙模式"""
        scam_text = "URGENT: Send money NOW to this crypto wallet! Only 24 hours left! 1000% guaranteed return! Act fast!"

        result = await tool.execute(text=scam_text)

        assert len(result["red_flags"]) > 0
        assert result["authenticity_score"] < 50

    @pytest.mark.asyncio
    async def test_execute_with_context(self, tool):
        """應能處理帶上下文的分析"""
        text = "我們急需醫療物資，村子裡很多人受傷了"
        context = {
            "post_id": "post_123",
            "author_history": 50,
            "account_age_days": 365
        }

        result = await tool.execute(text=text, context=context)

        # 有歷史紀錄的帳號應有更高的可信度
        assert result["authenticity_score"] >= 50

    @pytest.mark.asyncio
    async def test_execute_with_new_account_context(self, tool):
        """新帳號應降低可信度"""
        text = "Emergency! Need immediate help!"
        context = {
            "post_id": "post_456",
            "author_history": 0,
            "account_age_days": 1
        }

        result = await tool.execute(text=text, context=context)

        # 新帳號應有較低的可信度
        assert result["authenticity_score"] < 80
        # 應標記為風險因素
        assert any("account" in flag.lower() or "new" in flag.lower() for flag in result["red_flags"])

    @pytest.mark.asyncio
    async def test_execute_detects_emotional_indicators(self, tool):
        """應能識別情緒指標"""
        emotional_text = "Please, I'm begging you! My children are hungry and we have no food. I'm so scared and desperate!"

        result = await tool.execute(text=emotional_text)

        assert len(result["emotional_indicators"]) > 0

    @pytest.mark.asyncio
    async def test_execute_returns_summary(self, tool):
        """應返回分析摘要"""
        text = "Earthquake destroyed our village. Need tents and food."

        result = await tool.execute(text=text)

        assert len(result["summary"]) > 0
        assert isinstance(result["summary"], str)

    @pytest.mark.asyncio
    async def test_execute_empty_text_raises_error(self, tool):
        """空文本應拋出錯誤"""
        with pytest.raises((ValueError, Exception)):
            await tool.execute(text="")

    def test_tool_to_param_format(self, tool):
        """to_param 應返回正確的函數調用格式"""
        param = tool.to_param()

        assert param["type"] == "function"
        assert param["function"]["name"] == "analyze_sentiment"
