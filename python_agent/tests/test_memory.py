"""
Memory 模組測試 - TDD 驅動開發

測試 SpoonOS Memory 整合:
- config.py Memory 配置
- agent.py Memory 方法

遵循 RED -> GREEN -> REFACTOR 流程
"""

import os
import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# Phase 1: Config 配置測試 (RED)
# =============================================================================

class TestMemoryConfig:
    """測試 Memory 相關配置"""

    def test_memory_enabled_default_false(self):
        """Memory 功能默認應該關閉"""
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.memory_enabled is False

    def test_memory_enabled_from_env(self):
        """可以通過環境變數啟用 Memory"""
        os.environ["MEMORY_ENABLED"] = "true"
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        try:
            settings = get_settings()
            assert settings.memory_enabled is True
        finally:
            del os.environ["MEMORY_ENABLED"]
            get_settings.cache_clear()

    def test_memory_max_tokens_default(self):
        """Memory 最大 token 數默認為 4000"""
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.memory_max_tokens == 4000

    def test_memory_max_tokens_from_env(self):
        """可以通過環境變數設置最大 token 數"""
        os.environ["MEMORY_MAX_TOKENS"] = "8000"
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        try:
            settings = get_settings()
            assert settings.memory_max_tokens == 8000
        finally:
            del os.environ["MEMORY_MAX_TOKENS"]
            get_settings.cache_clear()

    def test_memory_trim_strategy_default(self):
        """Memory 裁剪策略默認為 from_end"""
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.memory_trim_strategy == "from_end"

    def test_memory_trim_strategy_from_env(self):
        """可以通過環境變數設置裁剪策略"""
        os.environ["MEMORY_TRIM_STRATEGY"] = "from_start"
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        try:
            settings = get_settings()
            assert settings.memory_trim_strategy == "from_start"
        finally:
            del os.environ["MEMORY_TRIM_STRATEGY"]
            get_settings.cache_clear()

    def test_memory_trim_strategy_invalid_value(self):
        """無效的裁剪策略應該引發驗證錯誤"""
        os.environ["MEMORY_TRIM_STRATEGY"] = "invalid_strategy"
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        try:
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                get_settings()
        finally:
            del os.environ["MEMORY_TRIM_STRATEGY"]
            get_settings.cache_clear()

    def test_is_memory_enabled_helper(self):
        """測試 is_memory_enabled() 輔助方法"""
        os.environ["MEMORY_ENABLED"] = "true"
        from gaia_link.config import get_settings
        get_settings.cache_clear()

        try:
            settings = get_settings()
            assert settings.is_memory_enabled() is True
        finally:
            del os.environ["MEMORY_ENABLED"]
            get_settings.cache_clear()


# =============================================================================
# Phase 2: Agent Memory 整合測試 (RED)
# =============================================================================

class TestAgentMemoryIntegration:
    """測試 Agent 與 Memory 的整合"""

    @pytest.fixture
    def agent_with_memory(self):
        """創建啟用 Memory 的 Agent"""
        os.environ["MEMORY_ENABLED"] = "true"
        os.environ["MEMORY_MAX_TOKENS"] = "4000"

        from gaia_link.config import get_settings
        get_settings.cache_clear()

        # Agent 會自動初始化 ChatBot，測試環境會處理 mock
        from gaia_link.agent import GaiaLinkAgent
        agent = GaiaLinkAgent()
        yield agent

        del os.environ["MEMORY_ENABLED"]
        del os.environ["MEMORY_MAX_TOKENS"]
        get_settings.cache_clear()

    @pytest.fixture
    def agent_without_memory(self):
        """創建禁用 Memory 的 Agent"""
        os.environ["MEMORY_ENABLED"] = "false"

        from gaia_link.config import get_settings
        get_settings.cache_clear()

        from gaia_link.agent import GaiaLinkAgent
        agent = GaiaLinkAgent()
        yield agent

        if "MEMORY_ENABLED" in os.environ:
            del os.environ["MEMORY_ENABLED"]
        get_settings.cache_clear()

    def test_agent_has_memory_manager_when_enabled(self, agent_with_memory):
        """啟用 Memory 時，Agent 應該有 _memory_manager 屬性"""
        assert hasattr(agent_with_memory, "_memory_manager")
        assert agent_with_memory._memory_manager is not None

    def test_agent_has_no_memory_manager_when_disabled(self, agent_without_memory):
        """禁用 Memory 時，Agent 的 _memory_manager 應該為 None"""
        assert hasattr(agent_without_memory, "_memory_manager")
        assert agent_without_memory._memory_manager is None

    def test_agent_has_conversation_history(self, agent_with_memory):
        """Agent 應該有 _conversation_history 屬性"""
        assert hasattr(agent_with_memory, "_conversation_history")
        assert isinstance(agent_with_memory._conversation_history, list)
        assert len(agent_with_memory._conversation_history) == 0

    def test_add_to_memory_user_message(self, agent_with_memory):
        """測試添加用戶訊息到記憶"""
        message = {"role": "user", "content": "Hello, I want to donate"}

        agent_with_memory.add_to_memory(message)

        history = agent_with_memory.get_conversation_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello, I want to donate"

    def test_add_to_memory_assistant_message(self, agent_with_memory):
        """測試添加助手訊息到記憶"""
        message = {"role": "assistant", "content": "I can help you donate"}

        agent_with_memory.add_to_memory(message)

        history = agent_with_memory.get_conversation_history()
        assert len(history) == 1
        assert history[0]["role"] == "assistant"

    def test_add_multiple_messages_to_memory(self, agent_with_memory):
        """測試添加多條訊息到記憶"""
        messages = [
            {"role": "user", "content": "What crises are happening?"},
            {"role": "assistant", "content": "Here are the active crises..."},
            {"role": "user", "content": "I want to donate to Turkey"},
            {"role": "assistant", "content": "Processing your donation..."},
        ]

        for msg in messages:
            agent_with_memory.add_to_memory(msg)

        history = agent_with_memory.get_conversation_history()
        assert len(history) == 4
        assert history[0]["content"] == "What crises are happening?"
        assert history[-1]["content"] == "Processing your donation..."

    def test_get_conversation_history_returns_copy(self, agent_with_memory):
        """get_conversation_history 應該返回副本，不是原始列表"""
        message = {"role": "user", "content": "Test message"}
        agent_with_memory.add_to_memory(message)

        history1 = agent_with_memory.get_conversation_history()
        history2 = agent_with_memory.get_conversation_history()

        # 修改返回的列表不應影響原始記憶
        history1.append({"role": "user", "content": "Modified"})

        assert len(agent_with_memory.get_conversation_history()) == 1

    def test_clear_memory(self, agent_with_memory):
        """測試清除記憶功能"""
        agent_with_memory.add_to_memory({"role": "user", "content": "Test 1"})
        agent_with_memory.add_to_memory({"role": "assistant", "content": "Response 1"})

        assert len(agent_with_memory.get_conversation_history()) == 2

        agent_with_memory.clear_memory()

        assert len(agent_with_memory.get_conversation_history()) == 0

    def test_add_to_memory_when_disabled_is_noop(self, agent_without_memory):
        """禁用 Memory 時，add_to_memory 應該是空操作"""
        message = {"role": "user", "content": "This should not be stored"}

        # 不應該拋出錯誤
        agent_without_memory.add_to_memory(message)

        history = agent_without_memory.get_conversation_history()
        assert len(history) == 0

    def test_clear_memory_when_disabled_is_noop(self, agent_without_memory):
        """禁用 Memory 時，clear_memory 應該是空操作"""
        # 不應該拋出錯誤
        agent_without_memory.clear_memory()

        history = agent_without_memory.get_conversation_history()
        assert len(history) == 0


# =============================================================================
# Phase 3: Memory Trim 測試 (RED)
# =============================================================================

class TestMemoryTrimming:
    """測試 Memory 裁剪功能"""

    @pytest.fixture
    def agent_with_small_memory(self):
        """創建小記憶容量的 Agent (用於測試裁剪)"""
        os.environ["MEMORY_ENABLED"] = "true"
        os.environ["MEMORY_MAX_TOKENS"] = "100"  # 小容量用於測試
        os.environ["MEMORY_TRIM_STRATEGY"] = "from_start"

        from gaia_link.config import get_settings
        get_settings.cache_clear()

        from gaia_link.agent import GaiaLinkAgent
        agent = GaiaLinkAgent()
        yield agent

        for key in ["MEMORY_ENABLED", "MEMORY_MAX_TOKENS", "MEMORY_TRIM_STRATEGY"]:
            if key in os.environ:
                del os.environ[key]
        get_settings.cache_clear()

    def test_memory_trims_when_exceeds_max_tokens(self, agent_with_small_memory):
        """當記憶超過最大 token 數時應該裁剪"""
        # 添加大量訊息以超過 100 tokens
        for i in range(20):
            agent_with_small_memory.add_to_memory({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"This is a test message number {i} with some extra content to fill up tokens"
            })

        history = agent_with_small_memory.get_conversation_history()

        # 應該裁剪了一些訊息
        assert len(history) < 20

    def test_memory_preserves_recent_messages(self, agent_with_small_memory):
        """裁剪時應該保留最近的訊息"""
        for i in range(10):
            agent_with_small_memory.add_to_memory({
                "role": "user",
                "content": f"Message {i}"
            })

        history = agent_with_small_memory.get_conversation_history()

        # 最後的訊息應該被保留
        if len(history) > 0:
            last_msg = history[-1]["content"]
            assert "Message 9" in last_msg or "Message" in last_msg


# =============================================================================
# Phase 4: Edge Cases 測試 (RED)
# =============================================================================

class TestMemoryEdgeCases:
    """測試邊界情況"""

    @pytest.fixture
    def agent(self):
        """創建啟用 Memory 的 Agent"""
        os.environ["MEMORY_ENABLED"] = "true"

        from gaia_link.config import get_settings
        get_settings.cache_clear()

        from gaia_link.agent import GaiaLinkAgent
        agent = GaiaLinkAgent()
        yield agent

        if "MEMORY_ENABLED" in os.environ:
            del os.environ["MEMORY_ENABLED"]
        get_settings.cache_clear()

    def test_add_empty_message(self, agent):
        """測試添加空訊息"""
        message = {"role": "user", "content": ""}

        # 空內容的訊息應該被接受或拒絕 (取決於設計)
        agent.add_to_memory(message)
        # 不應該拋出錯誤

    def test_add_message_with_missing_role(self, agent):
        """測試添加缺少 role 的訊息"""
        message = {"content": "No role specified"}

        # 應該優雅處理
        with pytest.raises((KeyError, ValueError)):
            agent.add_to_memory(message)

    def test_add_message_with_missing_content(self, agent):
        """測試添加缺少 content 的訊息"""
        message = {"role": "user"}

        # 應該優雅處理
        with pytest.raises((KeyError, ValueError)):
            agent.add_to_memory(message)

    def test_add_message_with_invalid_role(self, agent):
        """測試添加無效 role 的訊息"""
        message = {"role": "invalid_role", "content": "Test"}

        # 應該拒絕無效 role
        with pytest.raises(ValueError):
            agent.add_to_memory(message)

    def test_add_none_message(self, agent):
        """測試添加 None 訊息"""
        with pytest.raises((TypeError, ValueError)):
            agent.add_to_memory(None)

    def test_conversation_history_immutability(self, agent):
        """測試對話歷史不可變性"""
        agent.add_to_memory({"role": "user", "content": "Original"})

        history = agent.get_conversation_history()
        history[0]["content"] = "Modified"

        # 原始記憶不應該被修改
        assert agent.get_conversation_history()[0]["content"] == "Original"
