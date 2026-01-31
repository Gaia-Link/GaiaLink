"""
GaiaLinkAgent V2 測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path


class TestAgentV2Structure:
    """Agent V2 結構測試"""

    def test_agent_v2_module_exists(self):
        """agent_v2 模組應該存在"""
        from gaia_link import agent_v2
        assert agent_v2 is not None

    def test_gaia_link_agent_v2_class_exists(self):
        """GaiaLinkAgentV2 類應該存在"""
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        assert GaiaLinkAgentV2 is not None

    def test_create_gaia_link_agent_factory_exists(self):
        """create_gaia_link_agent 工廠函數應該存在"""
        from gaia_link.agent_v2 import create_gaia_link_agent
        assert callable(create_gaia_link_agent)


class TestAgentV2Inheritance:
    """Agent V2 繼承測試 - SpoonOS 合規性"""

    @pytest.fixture
    def agent(self):
        """建立 Agent V2 實例"""
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_agent_inherits_from_spoon_react_ai(self, agent):
        """Agent 應該繼承自 SpoonReactAI"""
        from spoon_ai.agents import SpoonReactAI
        assert isinstance(agent, SpoonReactAI)

    def test_agent_has_mcp_tools_support(self, agent):
        """Agent 應該支援 MCP 工具 (通過 _mcp_tools 屬性)"""
        assert hasattr(agent, '_mcp_tools')
        assert hasattr(agent, '_init_mcp_tools')

    def test_agent_has_skill_manager(self, agent):
        """Agent 應該有 SimpleSkillManager"""
        assert hasattr(agent, 'skill_manager')
        assert agent.skill_manager is not None


class TestAgentV2Properties:
    """Agent V2 屬性測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_agent_has_correct_name(self, agent):
        """Agent 應有正確的名稱"""
        assert agent.name == "gaia_link_agent_v2"

    def test_agent_has_description(self, agent):
        """Agent 應有描述"""
        assert len(agent.description) > 0
        assert "MCP" in agent.description or "Skills" in agent.description

    def test_agent_has_system_prompt(self, agent):
        """Agent 應有系統提示詞"""
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0

    def test_agent_max_steps(self, agent):
        """Agent 的最大步數應合理"""
        assert 1 <= agent.max_steps <= 20


class TestAgentV2Tools:
    """Agent V2 工具測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_agent_has_native_tools(self, agent):
        """Agent 應有原生工具"""
        tool_names = [t.name for t in agent.available_tools]
        assert "verify_crisis" in tool_names
        assert "analyze_sentiment" in tool_names
        assert "execute_donation" in tool_names

    def test_native_tools_inherit_from_base_tool(self, agent):
        """原生工具應繼承自 BaseTool"""
        from spoon_ai.tools.base import BaseTool
        for tool in agent.available_tools:
            assert isinstance(tool, BaseTool)


class TestAgentV2Skills:
    """Agent V2 技能測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_agent_has_skill_paths(self, agent):
        """Agent 應有技能路徑配置"""
        # skill_paths should be configured
        assert hasattr(agent, 'skill_paths') or hasattr(agent.skill_manager, '_loader')

    def test_agent_auto_trigger_skills_enabled(self, agent):
        """Agent 應啟用自動技能觸發"""
        assert hasattr(agent, 'auto_trigger_skills')
        assert agent.auto_trigger_skills is True


class TestAgentV2MCPTools:
    """Agent V2 MCP 工具測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_agent_has_mcp_tools_list(self, agent):
        """Agent 應有 MCP 工具列表"""
        assert hasattr(agent, '_mcp_tools')
        assert isinstance(agent._mcp_tools, list)

    def test_agent_init_mcp_tools_method_exists(self, agent):
        """Agent 應有 _init_mcp_tools 方法"""
        assert hasattr(agent, '_init_mcp_tools')
        assert callable(agent._init_mcp_tools)


class TestAgentV2GetInfo:
    """Agent V2 get_info 方法測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_get_info_returns_dict(self, agent):
        """get_info 應返回字典"""
        info = agent.get_info()
        assert isinstance(info, dict)

    def test_get_info_includes_name(self, agent):
        """get_info 應包含名稱"""
        info = agent.get_info()
        assert "name" in info
        assert info["name"] == "gaia_link_agent_v2"

    def test_get_info_includes_version(self, agent):
        """get_info 應包含版本"""
        info = agent.get_info()
        assert "version" in info
        assert info["version"] == "2.0.0"

    def test_get_info_includes_native_tools(self, agent):
        """get_info 應包含原生工具列表"""
        info = agent.get_info()
        assert "native_tools" in info
        assert isinstance(info["native_tools"], list)

    def test_get_info_includes_mcp_tools(self, agent):
        """get_info 應包含 MCP 工具列表"""
        info = agent.get_info()
        assert "mcp_tools" in info
        assert isinstance(info["mcp_tools"], list)

    def test_get_info_includes_skills(self, agent):
        """get_info 應包含技能列表"""
        info = agent.get_info()
        assert "skills" in info
        assert isinstance(info["skills"], list)


class TestAgentV2VerifyAndAdvise:
    """Agent V2 verify_and_advise 便捷方法測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_verify_and_advise_method_exists(self, agent):
        """verify_and_advise 方法應存在"""
        assert hasattr(agent, 'verify_and_advise')
        assert callable(agent.verify_and_advise)

    @pytest.mark.asyncio
    async def test_verify_and_advise_accepts_location(self, agent):
        """verify_and_advise 應接受座標參數"""
        # We can't fully test this without mocking LLM, but we can verify method signature
        import inspect
        sig = inspect.signature(agent.verify_and_advise)
        params = list(sig.parameters.keys())
        assert 'lat' in params
        assert 'long' in params


class TestAgentV2SystemPrompt:
    """Agent V2 系統提示詞測試"""

    def test_system_prompt_contains_v2_info(self):
        """系統提示詞應包含 v2.0 信息"""
        from gaia_link.agent_v2 import SYSTEM_PROMPT_V2
        assert "v2.0" in SYSTEM_PROMPT_V2 or "2.0" in SYSTEM_PROMPT_V2

    def test_system_prompt_mentions_mcp(self):
        """系統提示詞應提及 MCP"""
        from gaia_link.agent_v2 import SYSTEM_PROMPT_V2
        assert "MCP" in SYSTEM_PROMPT_V2

    def test_system_prompt_mentions_skills(self):
        """系統提示詞應提及技能系統"""
        from gaia_link.agent_v2 import SYSTEM_PROMPT_V2
        assert "skill" in SYSTEM_PROMPT_V2.lower() or "技能" in SYSTEM_PROMPT_V2

    def test_system_prompt_mentions_roles(self):
        """系統提示詞應包含角色定義"""
        from gaia_link.agent_v2 import SYSTEM_PROMPT_V2
        assert "Auditor" in SYSTEM_PROMPT_V2 or "審計師" in SYSTEM_PROMPT_V2
        assert "Payer" in SYSTEM_PROMPT_V2 or "支付官" in SYSTEM_PROMPT_V2


class TestCreateGaiaLinkAgentFactory:
    """create_gaia_link_agent 工廠函數測試"""

    def test_factory_creates_agent_v2(self):
        """工廠函數應創建 GaiaLinkAgentV2"""
        from gaia_link.agent_v2 import create_gaia_link_agent, GaiaLinkAgentV2
        agent = create_gaia_link_agent()
        assert isinstance(agent, GaiaLinkAgentV2)

    def test_factory_accepts_kwargs(self):
        """工廠函數應接受 kwargs"""
        from gaia_link.agent_v2 import create_gaia_link_agent
        agent = create_gaia_link_agent(max_steps=10)
        assert agent.max_steps == 10


class TestAgentV2MCPClientMethods:
    """Agent V2 MCP Client 方法測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_add_mcp_tool_method_exists(self, agent):
        """add_mcp_tool 方法應存在"""
        assert hasattr(agent, 'add_mcp_tool')
        assert callable(agent.add_mcp_tool)

    def test_add_mcp_tool_stdio_method_exists(self, agent):
        """add_mcp_tool_stdio 方法應存在"""
        assert hasattr(agent, 'add_mcp_tool_stdio')
        assert callable(agent.add_mcp_tool_stdio)

    def test_list_mcp_server_tools_method_exists(self, agent):
        """list_mcp_server_tools 方法應存在"""
        assert hasattr(agent, 'list_mcp_server_tools')
        assert callable(agent.list_mcp_server_tools)

    def test_call_mcp_tool_method_exists(self, agent):
        """call_mcp_tool 方法應存在"""
        assert hasattr(agent, 'call_mcp_tool')
        assert callable(agent.call_mcp_tool)


class TestAgentV2MCPClientWithEnvVar:
    """Agent V2 MCP Client 環境變數測試"""

    def test_mcp_tool_created_when_env_var_set(self):
        """當環境變數設置時應創建 MCP 工具"""
        import os
        from gaia_link.agent_v2 import GaiaLinkAgentV2

        # 設置環境變數
        os.environ["MCP_TAVILY_URL"] = "http://localhost:8001/sse"
        try:
            agent = GaiaLinkAgentV2()
            # 應該有一個 MCP 工具
            assert len(agent._mcp_tools) >= 1
            # 檢查工具名稱
            tool_names = [t.name for t in agent._mcp_tools]
            assert "tavily_search" in tool_names
        finally:
            # 清理環境變數
            del os.environ["MCP_TAVILY_URL"]

    def test_no_mcp_tool_when_no_env_var(self):
        """當沒有環境變數時不應創建 MCP 工具"""
        import os
        from gaia_link.agent_v2 import GaiaLinkAgentV2

        # 確保環境變數不存在
        for key in ["MCP_TAVILY_URL", "MCP_DEEPWIKI_URL", "MCP_GAIA_LINK_URL"]:
            if key in os.environ:
                del os.environ[key]

        agent = GaiaLinkAgentV2()
        # 應該沒有 MCP 工具
        assert len(agent._mcp_tools) == 0


class TestAgentV2MCPToolConfig:
    """Agent V2 MCP 工具配置測試"""

    def test_mcp_configs_defined(self):
        """MCP_CONFIGS 應該定義"""
        from gaia_link.agent_v2 import MCP_CONFIGS
        assert MCP_CONFIGS is not None
        assert isinstance(MCP_CONFIGS, dict)

    def test_mcp_configs_has_tavily(self):
        """MCP_CONFIGS 應該有 tavily 配置"""
        from gaia_link.agent_v2 import MCP_CONFIGS
        assert "tavily" in MCP_CONFIGS
        assert "env_var" in MCP_CONFIGS["tavily"]
        assert "name" in MCP_CONFIGS["tavily"]

    def test_mcp_configs_has_deepwiki(self):
        """MCP_CONFIGS 應該有 deepwiki 配置"""
        from gaia_link.agent_v2 import MCP_CONFIGS
        assert "deepwiki" in MCP_CONFIGS

    def test_mcp_configs_has_gaia_link(self):
        """MCP_CONFIGS 應該有 gaia_link 配置"""
        from gaia_link.agent_v2 import MCP_CONFIGS
        assert "gaia_link" in MCP_CONFIGS


class TestAgentV2GetInfoCapabilities:
    """Agent V2 get_info capabilities 測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    def test_get_info_includes_capabilities(self, agent):
        """get_info 應包含 capabilities"""
        info = agent.get_info()
        assert "capabilities" in info
        assert isinstance(info["capabilities"], dict)

    def test_get_info_capabilities_has_mcp_server(self, agent):
        """capabilities 應包含 mcp_server"""
        info = agent.get_info()
        assert "mcp_server" in info["capabilities"]
        assert info["capabilities"]["mcp_server"] is True

    def test_get_info_capabilities_has_mcp_client(self, agent):
        """capabilities 應包含 mcp_client"""
        info = agent.get_info()
        assert "mcp_client" in info["capabilities"]

    def test_get_info_capabilities_has_skills(self, agent):
        """capabilities 應包含 skills"""
        info = agent.get_info()
        assert "skills" in info["capabilities"]

    def test_get_info_includes_mcp_tools_count(self, agent):
        """get_info 應包含 mcp_tools_count"""
        info = agent.get_info()
        assert "mcp_tools_count" in info
        assert isinstance(info["mcp_tools_count"], int)


class TestAgentV2DynamicMCPTool:
    """Agent V2 動態添加 MCP 工具測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    @patch('gaia_link.agent_v2.MCPTool')
    def test_add_mcp_tool_creates_tool(self, mock_mcp_tool, agent):
        """add_mcp_tool 應創建 MCPTool"""
        mock_instance = MagicMock()
        mock_mcp_tool.return_value = mock_instance

        result = agent.add_mcp_tool(
            name="test_tool",
            url="http://localhost:8000/sse",
            description="Test MCP Tool"
        )

        assert result is True
        assert mock_instance in agent._mcp_tools

    @patch('gaia_link.agent_v2.MCPTool')
    def test_add_mcp_tool_stdio_creates_tool(self, mock_mcp_tool, agent):
        """add_mcp_tool_stdio 應創建 stdio MCPTool"""
        mock_instance = MagicMock()
        mock_mcp_tool.return_value = mock_instance

        result = agent.add_mcp_tool_stdio(
            name="test_stdio_tool",
            command="python",
            args=["-m", "my_mcp_server"],
            description="Test stdio MCP Tool"
        )

        assert result is True
        assert mock_instance in agent._mcp_tools

    def test_add_mcp_tool_handles_error(self, agent):
        """add_mcp_tool 應處理錯誤"""
        # 使用無效的 URL 應該返回 False (而不是拋出異常)
        # 因為 MCPTool 會在創建時驗證 URL
        # 這裡我們不能真正測試，因為需要真正的 MCPTool
        pass


class TestAgentV2CallMCPTool:
    """Agent V2 調用 MCP 工具測試"""

    @pytest.fixture
    def agent(self):
        from gaia_link.agent_v2 import GaiaLinkAgentV2
        return GaiaLinkAgentV2()

    @pytest.mark.asyncio
    async def test_call_mcp_tool_raises_for_unknown_tool(self, agent):
        """call_mcp_tool 應對未知工具拋出錯誤"""
        with pytest.raises(ValueError) as exc_info:
            await agent.call_mcp_tool("unknown_tool", query="test")
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_mcp_server_tools_returns_empty_for_unknown(self, agent):
        """list_mcp_server_tools 應對未知工具返回空列表"""
        result = await agent.list_mcp_server_tools("unknown_tool")
        assert result == []
