"""
Pytest 配置和共用 fixtures
"""

import os
import pytest
import sys
from pathlib import Path

# 確保 gaia_link 模組可被導入
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop_policy():
    """設定事件迴圈策略"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """每個測試前重置配置緩存並設置默認環境"""
    # 保存原始環境變數
    original_env = os.environ.get("BLOCKCHAIN_NETWORK")

    # 設置默認環境變數為 mock
    os.environ["BLOCKCHAIN_NETWORK"] = "mock"

    # 清除緩存
    from gaia_link.config import get_settings
    get_settings.cache_clear()

    yield

    # 測試後恢復原始環境變數
    if original_env is not None:
        os.environ["BLOCKCHAIN_NETWORK"] = original_env
    elif "BLOCKCHAIN_NETWORK" in os.environ:
        del os.environ["BLOCKCHAIN_NETWORK"]

    # 清除緩存
    get_settings.cache_clear()
