"""
analyze_pool.py 腳本測試

TDD: RED -> GREEN -> REFACTOR
測試 pool-manager Skill 的 analyze_pool 腳本。
使用 subprocess 方式運行腳本，符合 Skill 系統的設計。
"""

import json
import subprocess
import sys
import pytest
from pathlib import Path

from gaia_link.services.pool import (
    PoolInfo,
    PoolListResult,
    PoolRecommendation,
    VaultType,
    CreatorType,
    RecommendationPriority,
    MockPoolService,
    reset_pool_service,
    set_pool_service,
)


# Skills 目錄路徑
SKILLS_DIR = Path(__file__).parent.parent / "gaia_link" / "skills"
POOL_MANAGER_DIR = SKILLS_DIR / "pool-manager"


# =============================================================================
# Directory Structure Tests
# =============================================================================


class TestPoolManagerDirectoryStructure:
    """pool-manager 目錄結構測試"""

    def test_pool_manager_skill_directory_exists(self):
        """pool-manager 技能目錄應該存在"""
        assert POOL_MANAGER_DIR.exists(), (
            f"pool-manager skill directory not found: {POOL_MANAGER_DIR}"
        )
        assert POOL_MANAGER_DIR.is_dir()

    def test_skill_md_file_exists(self):
        """SKILL.md 文件應該存在"""
        skill_md = POOL_MANAGER_DIR / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found: {skill_md}"

    def test_scripts_directory_exists(self):
        """scripts 目錄應該存在"""
        scripts_dir = POOL_MANAGER_DIR / "scripts"
        assert scripts_dir.exists(), f"scripts directory not found: {scripts_dir}"
        assert scripts_dir.is_dir()

    def test_analyze_pool_script_exists(self):
        """analyze_pool.py 腳本應該存在"""
        script = POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"
        assert script.exists(), f"analyze_pool.py not found: {script}"


# =============================================================================
# Script Execution Tests
# =============================================================================


class TestAnalyzePoolScript:
    """analyze_pool.py 腳本測試"""

    @pytest.fixture
    def script_path(self):
        return POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"

    def test_script_is_executable_python(self, script_path):
        """腳本應該是有效的 Python 文件"""
        content = script_path.read_text(encoding='utf-8')
        try:
            compile(content, script_path, 'exec')
        except SyntaxError as e:
            pytest.fail(f"Script has syntax error: {e}")

    def test_script_handles_empty_input(self, script_path):
        """腳本應該處理空輸入 - 默認列出所有池子"""
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input="",
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        # 空輸入應該默認列出所有池子
        assert output.get("success") is True
        assert "pools" in output
        assert result.returncode == 0

    def test_script_handles_invalid_json(self, script_path):
        """腳本應該處理無效 JSON"""
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        assert "error" in output
        assert "Invalid JSON" in output["error"]
        assert result.returncode != 0


class TestAnalyzePoolQueryPool:
    """根據 pool_id 查詢池子測試"""

    @pytest.fixture
    def script_path(self):
        return POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"

    def test_query_pool_success(self, script_path):
        """成功查詢池子狀態"""
        input_data = json.dumps({"pool_id": "vault_001"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        assert "pool_status" in output
        assert "yield_info" in output
        assert "recommendation" in output
        assert output["pool_status"]["vault_id"] == "vault_001"
        assert result.returncode == 0

    def test_query_pool_not_found(self, script_path):
        """查詢不存在的池子"""
        input_data = json.dumps({"pool_id": "nonexistent_pool"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is False
        assert "error" in output
        assert "not found" in output["error"].lower()

    def test_query_pool_has_progress_percent(self, script_path):
        """查詢結果應包含進度百分比"""
        input_data = json.dumps({"pool_id": "vault_001"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        pool_status = output["pool_status"]
        assert "progress_percent" in pool_status
        assert pool_status["progress_percent"] == 65.0

    def test_query_pool_has_remaining_amount(self, script_path):
        """查詢結果應包含剩餘金額"""
        input_data = json.dumps({"pool_id": "vault_001"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        pool_status = output["pool_status"]
        assert "remaining_amount" in pool_status
        assert pool_status["remaining_amount"] == 35000.0


class TestAnalyzePoolYieldInfo:
    """yield_info 測試"""

    @pytest.fixture
    def script_path(self):
        return POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"

    def test_yield_pool_has_protocol(self, script_path):
        """yield 池應該有協議信息"""
        input_data = json.dumps({"pool_id": "vault_001"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        yield_info = output["yield_info"]
        assert yield_info["earned_usd"] == 1250.0
        assert yield_info["apy_estimate"] == 4.5
        assert yield_info["protocol"] == "Euler"

    def test_direct_pool_no_protocol(self, script_path):
        """direct 池應該沒有協議"""
        input_data = json.dumps({"pool_id": "vault_002"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        yield_info = output["yield_info"]
        assert yield_info["apy_estimate"] == 0
        assert yield_info["protocol"] is None


class TestAnalyzePoolListPools:
    """列出所有池子測試"""

    @pytest.fixture
    def script_path(self):
        return POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"

    def test_list_action(self, script_path):
        """使用 action=list 列出池子"""
        input_data = json.dumps({"action": "list"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        assert "pools" in output
        assert "summary" in output
        assert len(output["pools"]) == 3
        assert result.returncode == 0

    def test_list_pools_has_summary(self, script_path):
        """列表結果應包含摘要"""
        input_data = json.dumps({"action": "list"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        summary = output.get("summary", {})
        assert "total_pools" in summary
        assert "total_value_usd" in summary
        assert "total_yield_earned_usd" in summary
        assert "timestamp" in summary

    def test_list_pools_contains_required_fields(self, script_path):
        """池子列表應包含必要字段"""
        input_data = json.dumps({"action": "list"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        for pool in output["pools"]:
            assert "vault_id" in pool
            assert "name" in pool
            assert "vault_type" in pool
            assert "current_amount" in pool
            assert "progress_percent" in pool


class TestAnalyzePoolRecommendation:
    """建議測試"""

    @pytest.fixture
    def script_path(self):
        return POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"

    def test_high_progress_low_priority(self, script_path):
        """高進度池應該是 LOW 優先級"""
        # vault_003 進度 90%，應該是 LOW 優先級
        input_data = json.dumps({"pool_id": "vault_003"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        recommendation = output["recommendation"]
        assert recommendation["priority"] == "LOW"

    def test_normal_progress_normal_priority(self, script_path):
        """正常進度池應該是 NORMAL 優先級"""
        # vault_001 進度 65%，應該是 NORMAL 優先級
        input_data = json.dumps({"pool_id": "vault_001"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        recommendation = output["recommendation"]
        assert recommendation["priority"] == "NORMAL"

    def test_yield_pool_has_distribution_advice(self, script_path):
        """yield 池有收益時應該建議分配"""
        input_data = json.dumps({"pool_id": "vault_001"})
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        assert output.get("success") is True
        recommendation = output["recommendation"]
        items = recommendation.get("items", [])
        # 應該包含收益分配建議
        has_yield_advice = any(
            "yield" in item.lower() or "distribute" in item.lower()
            for item in items
        )
        assert has_yield_advice


# =============================================================================
# Integration Tests
# =============================================================================


class TestAnalyzePoolIntegration:
    """整合測試"""

    @pytest.fixture
    def script_path(self):
        return POOL_MANAGER_DIR / "scripts" / "analyze_pool.py"

    def test_full_workflow(self, script_path):
        """測試完整工作流程"""
        # 1. 列出所有池子
        list_input = json.dumps({"action": "list"})
        list_result = subprocess.run(
            [sys.executable, str(script_path)],
            input=list_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        list_output = json.loads(list_result.stdout)
        assert list_output.get("success") is True
        assert len(list_output["pools"]) > 0

        # 2. 選擇第一個池子查詢詳情
        first_pool_id = list_output["pools"][0]["vault_id"]
        query_input = json.dumps({"pool_id": first_pool_id})
        query_result = subprocess.run(
            [sys.executable, str(script_path)],
            input=query_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        query_output = json.loads(query_result.stdout)
        assert query_output.get("success") is True
        assert query_output["pool_status"]["vault_id"] == first_pool_id

    def test_uses_service_layer(self, script_path):
        """驗證腳本使用 Service 層"""
        content = script_path.read_text(encoding='utf-8')
        # 應該導入 service 層
        assert "from gaia_link.services.pool import" in content or \
               "get_pool_service" in content, \
               "Script should use the pool service layer"
