"""
Donation Tracker Skill 測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import yaml


# Skills 目錄路徑
SKILLS_DIR = Path(__file__).parent.parent / "gaia_link" / "skills"
DONATION_TRACKER_DIR = SKILLS_DIR / "donation-tracker"


class TestDonationTrackerDirectoryStructure:
    """donation-tracker 目錄結構測試"""

    def test_donation_tracker_skill_directory_exists(self):
        """donation-tracker 技能目錄應該存在"""
        assert DONATION_TRACKER_DIR.exists(), (
            f"donation-tracker skill directory not found: {DONATION_TRACKER_DIR}"
        )
        assert DONATION_TRACKER_DIR.is_dir()

    def test_skill_md_file_exists(self):
        """SKILL.md 文件應該存在"""
        skill_md = DONATION_TRACKER_DIR / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found: {skill_md}"

    def test_scripts_directory_exists(self):
        """scripts 目錄應該存在"""
        scripts_dir = DONATION_TRACKER_DIR / "scripts"
        assert scripts_dir.exists(), f"scripts directory not found: {scripts_dir}"
        assert scripts_dir.is_dir()

    def test_track_donation_script_exists(self):
        """track_donation.py 腳本應該存在"""
        script = DONATION_TRACKER_DIR / "scripts" / "track_donation.py"
        assert script.exists(), f"track_donation.py not found: {script}"


def parse_skill_frontmatter(skill_name: str) -> dict:
    """解析 SKILL.md 的 YAML frontmatter"""
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    content = skill_md.read_text(encoding='utf-8')

    # Extract frontmatter between --- markers
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            return yaml.safe_load(frontmatter)
    return {}


class TestDonationTrackerSkillMd:
    """SKILL.md 內容測試"""

    @pytest.fixture
    def metadata(self):
        return parse_skill_frontmatter("donation-tracker")

    def test_has_name(self, metadata):
        """應有 name 字段"""
        assert "name" in metadata
        assert metadata["name"] == "donation-tracker"

    def test_has_description(self, metadata):
        """應有 description 字段"""
        assert "description" in metadata
        assert len(metadata["description"]) > 0

    def test_has_version(self, metadata):
        """應有 version 字段"""
        assert "version" in metadata
        assert metadata["version"] == "1.0.0"

    def test_has_triggers(self, metadata):
        """應有 triggers 字段"""
        assert "triggers" in metadata
        assert isinstance(metadata["triggers"], list)
        assert len(metadata["triggers"]) > 0

    def test_triggers_include_keyword_type(self, metadata):
        """triggers 應包含 keyword 類型"""
        trigger_types = [t.get("type") for t in metadata["triggers"]]
        assert "keyword" in trigger_types

    def test_keyword_triggers_include_tracking_terms(self, metadata):
        """keyword triggers 應包含追蹤相關關鍵詞"""
        for trigger in metadata["triggers"]:
            if trigger.get("type") == "keyword":
                keywords = trigger.get("keywords", [])
                tracking_keywords = {"track", "status", "history", "transaction", "追蹤", "狀態", "歷史", "交易"}
                assert any(k in tracking_keywords for k in keywords), (
                    f"Missing tracking keywords in: {keywords}"
                )

    def test_triggers_include_pattern_type(self, metadata):
        """triggers 應包含 pattern 類型"""
        trigger_types = [t.get("type") for t in metadata["triggers"]]
        assert "pattern" in trigger_types

    def test_pattern_triggers_have_valid_patterns(self, metadata):
        """pattern triggers 應有有效的正則表達式"""
        import re
        for trigger in metadata["triggers"]:
            if trigger.get("type") == "pattern":
                patterns = trigger.get("patterns", [])
                assert len(patterns) > 0, "Pattern trigger should have patterns"
                for pattern in patterns:
                    # 確保正則表達式可以編譯
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        pytest.fail(f"Invalid regex pattern '{pattern}': {e}")

    def test_has_parameters(self, metadata):
        """應有 parameters 字段"""
        assert "parameters" in metadata
        params = metadata["parameters"]
        param_names = [p.get("name") for p in params]
        # 應該有 transaction_id 和 wallet_address 參數
        assert "transaction_id" in param_names
        assert "wallet_address" in param_names

    def test_parameters_have_descriptions(self, metadata):
        """每個參數應有描述"""
        for param in metadata["parameters"]:
            assert "description" in param, f"Parameter {param.get('name')} missing description"
            assert len(param["description"]) > 0

    def test_prerequisites_include_donation_advisor(self, metadata):
        """prerequisites 應包含 donation-advisor 技能"""
        prereqs = metadata.get("prerequisites", {})
        skills = prereqs.get("skills", [])
        assert "donation-advisor" in skills

    def test_has_scripts_section(self, metadata):
        """應有 scripts 字段"""
        assert "scripts" in metadata

    def test_scripts_enabled(self, metadata):
        """scripts 應該啟用"""
        scripts = metadata.get("scripts", {})
        assert scripts.get("enabled", False) is True

    def test_scripts_has_track_donation_definition(self, metadata):
        """scripts 應包含 track_donation 定義"""
        scripts = metadata.get("scripts", {})
        definitions = scripts.get("definitions", [])
        script_names = [d.get("name") for d in definitions]
        assert "track_donation" in script_names


class TestTrackDonationScript:
    """track_donation.py 腳本測試"""

    @pytest.fixture
    def script_path(self):
        return DONATION_TRACKER_DIR / "scripts" / "track_donation.py"

    def test_script_is_executable_python(self, script_path):
        """腳本應該是有效的 Python 文件"""
        content = script_path.read_text(encoding='utf-8')
        # 嘗試編譯 Python 代碼
        try:
            compile(content, script_path, 'exec')
        except SyntaxError as e:
            pytest.fail(f"Script has syntax error: {e}")

    def test_script_handles_empty_input(self, script_path):
        """腳本應該處理空輸入"""
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input="",
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        assert "error" in output
        assert result.returncode != 0

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

    def test_track_by_tx_hash_success(self, script_path):
        """根據 tx_hash 追蹤應該返回交易狀態"""
        input_data = json.dumps({
            "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        })
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        assert output.get("success") is True
        assert "transaction" in output
        assert "explorer_url" in output
        assert result.returncode == 0

    def test_track_by_tx_hash_invalid_format(self, script_path):
        """無效的 tx_hash 格式應該返回錯誤"""
        input_data = json.dumps({
            "tx_hash": "invalid-hash"
        })
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

    def test_query_history_by_wallet_address(self, script_path):
        """根據 wallet_address 查詢歷史應該返回捐款列表"""
        input_data = json.dumps({
            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f8e888"
        })
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        assert output.get("success") is True
        assert "donations" in output
        assert isinstance(output["donations"], list)
        assert "summary" in output
        assert result.returncode == 0

    def test_query_history_with_time_range(self, script_path):
        """查詢歷史時可以指定時間範圍"""
        input_data = json.dumps({
            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f8e888",
            "time_range": "30d"
        })
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        assert output.get("success") is True
        assert "donations" in output
        assert result.returncode == 0

    def test_query_history_invalid_wallet_address(self, script_path):
        """無效的 wallet_address 應該返回錯誤"""
        input_data = json.dumps({
            "wallet_address": "invalid-address"
        })
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

    def test_no_tx_hash_and_no_wallet_address(self, script_path):
        """沒有提供 tx_hash 或 wallet_address 應該返回錯誤"""
        input_data = json.dumps({})
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


class TestTrackDonationOutput:
    """track_donation.py 輸出格式測試"""

    @pytest.fixture
    def script_path(self):
        return DONATION_TRACKER_DIR / "scripts" / "track_donation.py"

    def test_transaction_output_has_required_fields(self, script_path):
        """追蹤交易輸出應該包含必要字段"""
        input_data = json.dumps({
            "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        })
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        # 檢查交易對象
        tx = output.get("transaction", {})
        assert "tx_hash" in tx
        assert "status" in tx
        assert "timestamp" in tx

    def test_history_output_has_summary(self, script_path):
        """查詢歷史輸出應該包含摘要"""
        input_data = json.dumps({
            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f8e888"
        })
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)

        # 檢查摘要
        summary = output.get("summary", {})
        assert "total_donations" in summary
        assert "total_amount_usd" in summary


class TestDonationTrackerSkillLoading:
    """技能載入測試"""

    def test_donation_tracker_skill_can_be_discovered(self):
        """donation-tracker 技能應該可以被發現"""
        from gaia_link.agent_v2 import SimpleSkillManager

        manager = SimpleSkillManager(skill_paths=[str(SKILLS_DIR)])
        skills = manager.list_available()
        skill_names = [s.name for s in skills]

        assert "donation-tracker" in skill_names

    def test_donation_tracker_skill_can_be_loaded(self):
        """donation-tracker 技能應該可以載入"""
        from gaia_link.agent_v2 import SimpleSkillManager

        manager = SimpleSkillManager(skill_paths=[str(SKILLS_DIR)])
        skill = manager.get_skill("donation-tracker")

        assert skill is not None
        assert skill.name == "donation-tracker"
