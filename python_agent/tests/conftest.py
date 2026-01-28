"""
Pytest 配置和共用 fixtures
"""

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
