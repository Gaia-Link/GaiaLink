"""
GaiaLinkAgent 整合測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest

from gaia_link.agent import GaiaLinkAgent, GAIA_LINK_SYSTEM_PROMPT
from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
)


class TestGaiaLinkAgent:
    """GaiaLinkAgent 測試"""

    @pytest.fixture
    def agent(self):
        """建立 Agent 實例"""
        return GaiaLinkAgent()

    def test_agent_has_correct_name(self, agent):
        """Agent 應有正確的名稱"""
        assert agent.name == "gaia_link_agent"

    def test_agent_has_description(self, agent):
        """Agent 應有描述"""
        assert len(agent.description) > 0
        assert "humanitarian" in agent.description.lower() or "crisis" in agent.description.lower()

    def test_agent_has_system_prompt(self, agent):
        """Agent 應有系統提示詞（SpoonReactAI 會自動生成包含工具描述的 prompt）"""
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0
        # SpoonReactAI 會自動生成包含工具資訊的 prompt
        assert "verify_crisis" in agent.system_prompt
        assert "analyze_sentiment" in agent.system_prompt
        assert "execute_donation" in agent.system_prompt

    def test_agent_has_four_tools(self, agent):
        """Agent 應註冊四個核心工具"""
        tool_names = [tool.name for tool in agent.available_tools]

        assert len(tool_names) == 4
        assert "verify_crisis" in tool_names
        assert "analyze_sentiment" in tool_names
        assert "execute_donation" in tool_names
        assert "list_crises" in tool_names

    def test_agent_tools_are_correct_types(self, agent):
        """Agent 的工具應是正確的類型"""
        tools = {tool.name: tool for tool in agent.available_tools}

        assert isinstance(tools["verify_crisis"], VerifyCrisisTool)
        assert isinstance(tools["analyze_sentiment"], AnalyzeSentimentTool)
        assert isinstance(tools["execute_donation"], ExecuteDonationTool)

    def test_agent_max_steps_is_reasonable(self, agent):
        """Agent 的最大步數應合理"""
        assert 1 <= agent.max_steps <= 20

    def test_agent_get_info(self, agent):
        """get_info 應返回正確的資訊"""
        info = agent.get_info()

        assert info["name"] == "gaia_link_agent"
        assert "description" in info
        assert "tools" in info
        assert len(info["tools"]) == 4
        assert "max_steps" in info

    def test_system_prompt_contains_role_definitions(self):
        """系統提示詞應包含角色定義"""
        assert "Auditor" in GAIA_LINK_SYSTEM_PROMPT or "審計師" in GAIA_LINK_SYSTEM_PROMPT
        assert "Payer" in GAIA_LINK_SYSTEM_PROMPT or "支付官" in GAIA_LINK_SYSTEM_PROMPT

    def test_system_prompt_contains_tool_descriptions(self):
        """系統提示詞應包含工具說明"""
        assert "verify_crisis" in GAIA_LINK_SYSTEM_PROMPT
        assert "analyze_sentiment" in GAIA_LINK_SYSTEM_PROMPT
        assert "execute_donation" in GAIA_LINK_SYSTEM_PROMPT

    def test_system_prompt_contains_response_format(self):
        """系統提示詞應包含回應格式說明"""
        assert "JSON" in GAIA_LINK_SYSTEM_PROMPT
        # System prompt 應包含 JSON 結構說明
        assert "message" in GAIA_LINK_SYSTEM_PROMPT.lower()
        assert "action_taken" in GAIA_LINK_SYSTEM_PROMPT.lower()


class TestAgentSpoonOSCompliance:
    """SpoonOS 合規性測試"""

    @pytest.fixture
    def agent(self):
        return GaiaLinkAgent()

    def test_agent_inherits_from_spoon_react_ai(self, agent):
        """Agent 應繼承自 SpoonReactAI (符合 SpoonOS React Agent 要求)"""
        from spoon_ai.agents import SpoonReactAI

        assert isinstance(agent, SpoonReactAI)

    def test_tools_inherit_from_base_tool(self, agent):
        """所有工具應繼承自 BaseTool"""
        from spoon_ai.tools.base import BaseTool

        for tool in agent.available_tools:
            assert isinstance(tool, BaseTool)

    def test_tools_have_execute_method(self, agent):
        """所有工具應有 execute 方法"""
        for tool in agent.available_tools:
            assert hasattr(tool, "execute")
            assert callable(tool.execute)

    def test_tools_have_to_param_method(self, agent):
        """所有工具應有 to_param 方法"""
        for tool in agent.available_tools:
            assert hasattr(tool, "to_param")
            param = tool.to_param()
            assert param["type"] == "function"
            assert "function" in param
            assert "name" in param["function"]
            assert "description" in param["function"]
            assert "parameters" in param["function"]
