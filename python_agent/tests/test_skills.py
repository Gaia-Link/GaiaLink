"""
Skills 系統測試

TDD RED Phase: 先撰寫測試，確保測試失敗
"""

import pytest
from pathlib import Path
import yaml


# Skills 目錄路徑
SKILLS_DIR = Path(__file__).parent.parent / "gaia_link" / "skills"


class TestSkillsDirectoryStructure:
    """Skills 目錄結構測試"""

    def test_skills_directory_exists(self):
        """skills 目錄應該存在"""
        assert SKILLS_DIR.exists(), f"Skills directory not found: {SKILLS_DIR}"
        assert SKILLS_DIR.is_dir()

    def test_crisis_response_skill_exists(self):
        """crisis-response 技能目錄應該存在"""
        skill_dir = SKILLS_DIR / "crisis-response"
        assert skill_dir.exists(), f"crisis-response skill not found: {skill_dir}"
        assert skill_dir.is_dir()

    def test_donation_advisor_skill_exists(self):
        """donation-advisor 技能目錄應該存在"""
        skill_dir = SKILLS_DIR / "donation-advisor"
        assert skill_dir.exists(), f"donation-advisor skill not found: {skill_dir}"
        assert skill_dir.is_dir()

    def test_pool_manager_skill_exists(self):
        """pool-manager 技能目錄應該存在"""
        skill_dir = SKILLS_DIR / "pool-manager"
        assert skill_dir.exists(), f"pool-manager skill not found: {skill_dir}"
        assert skill_dir.is_dir()


class TestSkillMdFiles:
    """SKILL.md 文件測試"""

    def test_crisis_response_skill_md_exists(self):
        """crisis-response/SKILL.md 應該存在"""
        skill_md = SKILLS_DIR / "crisis-response" / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found: {skill_md}"

    def test_donation_advisor_skill_md_exists(self):
        """donation-advisor/SKILL.md 應該存在"""
        skill_md = SKILLS_DIR / "donation-advisor" / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found: {skill_md}"

    def test_pool_manager_skill_md_exists(self):
        """pool-manager/SKILL.md 應該存在"""
        skill_md = SKILLS_DIR / "pool-manager" / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found: {skill_md}"


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


class TestCrisisResponseSkill:
    """crisis-response 技能內容測試"""

    @pytest.fixture
    def metadata(self):
        return parse_skill_frontmatter("crisis-response")

    def test_has_name(self, metadata):
        """應有 name 字段"""
        assert "name" in metadata
        assert metadata["name"] == "crisis-response"

    def test_has_description(self, metadata):
        """應有 description 字段"""
        assert "description" in metadata
        assert len(metadata["description"]) > 0

    def test_has_version(self, metadata):
        """應有 version 字段"""
        assert "version" in metadata

    def test_has_triggers(self, metadata):
        """應有 triggers 字段"""
        assert "triggers" in metadata
        assert isinstance(metadata["triggers"], list)
        assert len(metadata["triggers"]) > 0

    def test_triggers_include_keyword_type(self, metadata):
        """triggers 應包含 keyword 類型"""
        trigger_types = [t.get("type") for t in metadata["triggers"]]
        assert "keyword" in trigger_types

    def test_keyword_triggers_include_crisis_terms(self, metadata):
        """keyword triggers 應包含危機相關關鍵詞"""
        for trigger in metadata["triggers"]:
            if trigger.get("type") == "keyword":
                keywords = trigger.get("keywords", [])
                # Should include crisis-related keywords
                crisis_keywords = {"crisis", "disaster", "emergency", "earthquake", "危機", "災難", "緊急"}
                assert any(k in crisis_keywords for k in keywords), \
                    f"Missing crisis keywords in: {keywords}"

    def test_has_prerequisites(self, metadata):
        """應有 prerequisites 字段"""
        assert "prerequisites" in metadata

    def test_prerequisites_include_tools(self, metadata):
        """prerequisites 應包含必要工具"""
        prereqs = metadata.get("prerequisites", {})
        tools = prereqs.get("tools", [])
        assert "verify_crisis" in tools or "analyze_sentiment" in tools

    def test_has_scripts_section(self, metadata):
        """應有 scripts 字段"""
        assert "scripts" in metadata

    def test_scripts_enabled(self, metadata):
        """scripts 應該啟用"""
        scripts = metadata.get("scripts", {})
        assert scripts.get("enabled", False) is True

    def test_composes_donation_advisor(self, metadata):
        """應該 compose donation-advisor 技能"""
        composes = metadata.get("composes", [])
        assert "donation-advisor" in composes


class TestDonationAdvisorSkill:
    """donation-advisor 技能內容測試"""

    @pytest.fixture
    def metadata(self):
        return parse_skill_frontmatter("donation-advisor")

    def test_has_name(self, metadata):
        """應有 name 字段"""
        assert "name" in metadata
        assert metadata["name"] == "donation-advisor"

    def test_has_description(self, metadata):
        """應有 description 字段"""
        assert "description" in metadata
        assert len(metadata["description"]) > 0

    def test_has_triggers(self, metadata):
        """應有 triggers 字段"""
        assert "triggers" in metadata
        assert isinstance(metadata["triggers"], list)

    def test_keyword_triggers_include_donation_terms(self, metadata):
        """keyword triggers 應包含捐款相關關鍵詞"""
        for trigger in metadata["triggers"]:
            if trigger.get("type") == "keyword":
                keywords = trigger.get("keywords", [])
                donation_keywords = {"donate", "donation", "contribute", "fund", "捐款", "捐贈"}
                assert any(k in donation_keywords for k in keywords), \
                    f"Missing donation keywords in: {keywords}"

    def test_has_parameters(self, metadata):
        """應有 parameters 字段"""
        assert "parameters" in metadata
        params = metadata["parameters"]
        param_names = [p.get("name") for p in params]
        # Should have amount and token parameters
        assert "amount" in param_names or "token" in param_names

    def test_prerequisites_include_crisis_response(self, metadata):
        """prerequisites 應包含 crisis-response 技能"""
        prereqs = metadata.get("prerequisites", {})
        skills = prereqs.get("skills", [])
        assert "crisis-response" in skills


class TestPoolManagerSkill:
    """pool-manager 技能內容測試"""

    @pytest.fixture
    def metadata(self):
        return parse_skill_frontmatter("pool-manager")

    def test_has_name(self, metadata):
        """應有 name 字段"""
        assert "name" in metadata
        assert metadata["name"] == "pool-manager"

    def test_has_description(self, metadata):
        """應有 description 字段"""
        assert "description" in metadata
        assert len(metadata["description"]) > 0

    def test_has_triggers(self, metadata):
        """應有 triggers 字段"""
        assert "triggers" in metadata
        assert isinstance(metadata["triggers"], list)

    def test_keyword_triggers_include_pool_terms(self, metadata):
        """keyword triggers 應包含資金池相關關鍵詞"""
        for trigger in metadata["triggers"]:
            if trigger.get("type") == "keyword":
                keywords = trigger.get("keywords", [])
                pool_keywords = {"pool", "vault", "treasury", "allocation", "資金池", "池子"}
                assert any(k in pool_keywords for k in keywords), \
                    f"Missing pool keywords in: {keywords}"

    def test_prerequisites_include_required_skills(self, metadata):
        """prerequisites 應包含必要技能"""
        prereqs = metadata.get("prerequisites", {})
        skills = prereqs.get("skills", [])
        # Should require crisis-response and donation-advisor
        assert "crisis-response" in skills or "donation-advisor" in skills


class TestSkillScriptsDirectory:
    """技能腳本目錄測試"""

    def test_crisis_response_scripts_dir_exists(self):
        """crisis-response/scripts 目錄應該存在"""
        scripts_dir = SKILLS_DIR / "crisis-response" / "scripts"
        assert scripts_dir.exists(), f"Scripts directory not found: {scripts_dir}"

    def test_verify_polymarket_script_exists(self):
        """verify_polymarket.py 腳本應該存在"""
        script = SKILLS_DIR / "crisis-response" / "scripts" / "verify_polymarket.py"
        assert script.exists(), f"Script not found: {script}"


class TestSkillLoading:
    """技能載入測試 - 使用自定義 SimpleSkillManager"""

    def test_skills_can_be_discovered(self):
        """技能應該可以被發現"""
        from gaia_link.agent_v2 import SimpleSkillManager

        manager = SimpleSkillManager(skill_paths=[str(SKILLS_DIR)])
        skills = manager.list_available()
        skill_names = [s.name for s in skills]

        assert "crisis-response" in skill_names
        assert "donation-advisor" in skill_names
        assert "pool-manager" in skill_names

    def test_crisis_response_skill_can_be_loaded(self):
        """crisis-response 技能應該可以載入"""
        from gaia_link.agent_v2 import SimpleSkillManager

        manager = SimpleSkillManager(skill_paths=[str(SKILLS_DIR)])
        skill = manager.get_skill("crisis-response")

        assert skill is not None
        assert skill.name == "crisis-response"
