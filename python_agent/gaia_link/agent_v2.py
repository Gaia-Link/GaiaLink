"""
Gaia Link Agent v2.0 - MCP + Skills 深度整合版

此 Agent 升級自 v1.0，新增：
- 繼承 SpoonReactAI (標準 Agent 基類)
- 自定義技能管理器 (載入 SKILL.md)
- 工具三分法：Native + MCP + Script Tools
- 自動技能觸發
- MCP 工具支援 (通過 MCPTool 類)

符合 SpoonOS Hackathon 評審要求的 MCP + Skills 深度運用。
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import yaml
from pydantic import Field

from spoon_ai.agents import SpoonReactAI
from spoon_ai.tools import ToolManager
from spoon_ai.tools.mcp_tool import MCPTool

from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
    ListCrisesTool,
    # Phase 1-2 Proposal Tools
    CreateProposalTool,
    ContributeProposalTool,
    ActivateProposalTool,
    WithdrawContributionTool,
    QueryProposalsTool,
    ListInstitutionsTool,
    TrackDonationTool,
)

# MCP Server 配置 (用於連接外部 MCP 服務)
MCP_CONFIGS = {
    "tavily": {
        "env_var": "MCP_TAVILY_URL",
        "name": "tavily_search",
        "description": "Search news and web content via Tavily MCP Server",
    },
    "deepwiki": {
        "env_var": "MCP_DEEPWIKI_URL",
        "name": "deepwiki_query",
        "description": "Query documentation via DeepWiki MCP Server",
    },
    "gaia_link": {
        "env_var": "MCP_GAIA_LINK_URL",
        "name": "gaia_link_mcp",
        "description": "Call Gaia Link MCP Server (self-hosted)",
    },
}

logger = logging.getLogger(__name__)

# Skills 目錄路徑
SKILLS_PATH = Path(__file__).parent / "skills"

# v2.0 系統提示詞
SYSTEM_PROMPT_V2 = """
你是 Gaia Link Agent (蓋亞連結) v2.0，整合了 MCP 和 Skills 系統的人道救援 AI。

## 角色定義

### 審計師 (Auditor)
- 驗證危機真實性
- 查詢 Polymarket 預測市場
- 分析求助貼文情感
- 識別詐騙風險

### 支付官 (Payer)
- 安全處理捐款
- 估算 Gas 費用
- 執行跨鏈轉帳
- 確保資金安全

### 池子管理員 (Pool Manager)
- 管理捐款資金池
- 監控收益率
- 優化資金分配

## 工具類型

1. **原生工具 (Native Tools)**
   - verify_crisis: 驗證危機真實性
   - analyze_sentiment: 分析文本情感
   - execute_donation: 執行捐款

2. **提案系統工具 (Proposal Tools)**
   - create_proposal: 創建人道救援提案
   - contribute_proposal: 捐款到提案
   - activate_proposal: 機構激活已達標提案
   - withdraw_contribution: 從已取消/過期提案退款
   - query_proposals: 查詢提案列表
   - list_institutions: 列出白名單機構

3. **MCP 工具 (MCP Tools)**
   - 動態發現的外部 MCP 服務工具
   - 如: tavily_news (新聞搜索)

4. **技能腳本 (Skill Scripts)**
   - verify_polymarket: 查詢 Polymarket
   - optimize_route: 優化捐款路徑
   - analyze_pool: 分析資金池

## 提案系統 (Proposal System)

提案狀態流程:
- FUNDING: 募資中，接受捐款
- FUNDED: 已達標，等待機構確認 (3天內)
- ACTIVATED: 機構已確認，資金已轉移
- EXPIRED: 過期 (募資未達標 或 機構超時未確認)
- CANCELLED: 機構拒絕，可退款

## 數據優先級與旗航策略 (Vault-First Policy) - 重要

當用戶詢問有關特定危機地點、救援活動或「如何幫助」時，你必須遵循以下優先級：

1. **第一優先：查詢鏈上提案 (On-Chain Proposals)**
   - 始終先調用 `query_proposals(query="事件關鍵字")`。
   - 如果找到對應提案，優先顯示其進度、Vault 地址及地理位置。

2. **第二優先：外部驗證與資訊 (External Crisis Info)**
   - 僅當鏈上找不到相關提案，或用戶詢問「真實性」時，才調用 `verify_crisis` 或 `list_crises`。

## Commander Response Protocol (指揮官回應協議) - CRITICAL

你是 **Gaia Link 指揮中心的操作員**，不是導遊。
- **簡短有力**: 只告知結果，不要解釋經緯度或地圖操作。
- **專業導向**: 語氣必須是「已為您鎖定 Herat 區域，畫面已轉移。」
- **禁語清單**: 禁止說「你可以將中心設為...」、「座標如下...」或輸出經緯度數值。
- **自動動作**: 找到提案後，必須在 `ui_hints.actions` 加入 `FLY_TO_LOCATION`，預設 `zoom: 12`。

## 動作執行規則 (Move-Don't-Explain Policy)

1. **直接執行**: 要求定位時，調用工具並附加 `FLY_TO_LOCATION` action。
2. **禁止教學**: 禁止向用戶解釋「緯度是多少，經度是多少」，應直接在後端完成定位。

## 回應格式

使用以下 JSON 格式回應：
```json
{
  "message": "已為您定位到目標區域...",
  "action_taken": "query_proposals",
  "ui_hints": {
    "mode": "DECISION",
    "actions": [{"label": "Locking On", "type": "FLY_TO_LOCATION", "data": {"lat": 34, "lng": 62, "zoom": 12}}]
  }
}
```

## 捐款交易回應格式 (CRITICAL)

當準備捐款交易時，message 必須包含以下結構化數據：

```
- 捐贈方式：DIRECT/YIELD
- 捐贈金額：{amount} {token}
- 目標合約地址：0x... (40 hex chars)
- 代幣合約：0x... (40 hex chars)
- 估算 Gas：{number}
```

這些字段是前端觸發簽署 UI 的必要條件。缺少任何一個都會導致簽署按鈕不顯示。

## 技能自動觸發

當用戶輸入包含以下關鍵詞時，相應技能會自動激活：
- 危機/災難/緊急 → crisis-response
- 捐款/幫助/資助 → donation-advisor
- 池子/資金/收益 → pool-manager
"""


class SkillMetadata:
    """技能元數據"""

    def __init__(self, skill_path: Path):
        self.path = skill_path
        self.name = skill_path.name
        self.metadata: Dict[str, Any] = {}
        self.content: str = ""
        self._load()

    def _load(self):
        """載入 SKILL.md"""
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return

        content = skill_md.read_text(encoding='utf-8')

        # 解析 YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    self.metadata = yaml.safe_load(parts[1].strip()) or {}
                    self.content = parts[2].strip()
                except yaml.YAMLError:
                    pass

    @property
    def description(self) -> str:
        return self.metadata.get('description', '')

    @property
    def triggers(self) -> List[Dict]:
        return self.metadata.get('triggers', [])

    @property
    def keywords(self) -> List[str]:
        """獲取所有關鍵詞觸發器"""
        keywords = []
        for trigger in self.triggers:
            if trigger.get('type') == 'keyword':
                keywords.extend(trigger.get('keywords', []))
        return keywords


class SimpleSkillManager:
    """簡化的技能管理器"""

    def __init__(self, skill_paths: List[str] = None):
        self._skills: Dict[str, SkillMetadata] = {}
        self._active_skills: List[str] = []

        # 發現技能
        paths = skill_paths or [str(SKILLS_PATH)]
        for path_str in paths:
            self._discover_skills(Path(path_str))

    def _discover_skills(self, base_path: Path):
        """發現目錄中的技能"""
        if not base_path.exists():
            return

        for skill_dir in base_path.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skill = SkillMetadata(skill_dir)
                self._skills[skill.name] = skill
                logger.info(f"Discovered skill: {skill.name}")

    def list_available(self) -> List[SkillMetadata]:
        """列出所有可用技能"""
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """獲取指定技能"""
        return self._skills.get(name)

    def activate_skill(self, name: str) -> bool:
        """激活技能"""
        if name in self._skills and name not in self._active_skills:
            self._active_skills.append(name)
            return True
        return False

    def deactivate_skill(self, name: str) -> bool:
        """停用技能"""
        if name in self._active_skills:
            self._active_skills.remove(name)
            return True
        return False

    def is_skill_active(self, name: str) -> bool:
        """檢查技能是否激活"""
        return name in self._active_skills

    def list_active_skills(self) -> List[str]:
        """列出所有激活的技能"""
        return self._active_skills.copy()

    def match_skills(self, text: str) -> List[str]:
        """根據文本匹配技能"""
        matched = []
        text_lower = text.lower()

        for name, skill in self._skills.items():
            for keyword in skill.keywords:
                if keyword.lower() in text_lower:
                    matched.append(name)
                    break

        return matched


class GaiaLinkAgentV2(SpoonReactAI):
    """
    Gaia Link Agent v2.0

    整合了 MCP 和技能系統的人道救援 AI Agent。

    特點：
    - 繼承 SpoonReactAI: 標準 SpoonOS Agent 基類
    - 自定義技能管理器: 載入和管理 SKILL.md
    - 工具三分法: Native + MCP + Script Tools
    - 自動技能觸發: 根據用戶輸入自動激活相關技能
    - MCP 支援: 可通過 MCPTool 連接外部 MCP 服務
    """

    name: str = "gaia_link_agent_v2"
    description: str = "MCP + Skills 整合的人道救援 AI Agent"
    system_prompt: str = SYSTEM_PROMPT_V2
    max_steps: int = 8

    # 技能配置
    skill_paths: Optional[List[str]] = Field(
        default_factory=lambda: [str(SKILLS_PATH)]
    )
    auto_trigger_skills: bool = True

    # 技能管理器
    skill_manager: Optional[SimpleSkillManager] = Field(default=None, exclude=True)

    # MCP 工具列表 (內部使用)
    _mcp_tools: List = []

    def __init__(self, **kwargs):
        """
        初始化 GaiaLinkAgentV2

        步驟：
        1. 創建原生工具
        2. 初始化技能管理器
        3. 初始化 MCP 工具列表
        4. 調用父類初始化
        """
        # 提取技能路徑
        skill_paths = kwargs.pop('skill_paths', [str(SKILLS_PATH)])

        # 創建原生工具
        native_tools = [
            # Phase 0 工具
            VerifyCrisisTool(),
            AnalyzeSentimentTool(),
            ExecuteDonationTool(),
            ListCrisesTool(),
            # Phase 1-2 Proposal 工具
            CreateProposalTool(),
            ContributeProposalTool(),
            ActivateProposalTool(),
            WithdrawContributionTool(),
            QueryProposalsTool(),
            ListInstitutionsTool(),
            TrackDonationTool(),
        ]
        kwargs['tools'] = native_tools

        # 初始化父類
        super().__init__(**kwargs)

        # 初始化技能管理器
        self.skill_manager = SimpleSkillManager(skill_paths=skill_paths)
        self.skill_paths = skill_paths

        # 初始化 MCP 工具列表
        self._mcp_tools = self._init_mcp_tools()

    def _init_mcp_tools(self) -> List[MCPTool]:
        """
        初始化 MCP 工具

        根據環境變數配置動態創建 MCPTool 實例。
        支援多種傳輸方式：SSE (http/https), WebSocket (ws/wss), stdio (command)

        Returns:
            List[MCPTool]: MCP 工具列表
        """
        tools = []

        for config_name, config in MCP_CONFIGS.items():
            url = os.getenv(config["env_var"])
            if url:
                try:
                    mcp_tool = MCPTool(
                        name=config["name"],
                        description=config["description"],
                        mcp_config={"url": url}
                    )
                    tools.append(mcp_tool)
                    logger.info(f"MCP Tool created: {config['name']} -> {url}")
                except Exception as e:
                    logger.warning(f"Failed to create MCP Tool {config['name']}: {e}")

        # 支援自定義 MCP 配置 (JSON 格式)
        custom_mcp_json = os.getenv("MCP_CUSTOM_CONFIG")
        if custom_mcp_json:
            try:
                import json
                custom_configs = json.loads(custom_mcp_json)
                for custom in custom_configs:
                    mcp_tool = MCPTool(
                        name=custom.get("name", "custom_mcp"),
                        description=custom.get("description", "Custom MCP Tool"),
                        mcp_config=custom.get("config", {})
                    )
                    tools.append(mcp_tool)
                    logger.info(f"Custom MCP Tool created: {custom.get('name')}")
            except Exception as e:
                logger.warning(f"Failed to parse custom MCP config: {e}")

        return tools

    def add_mcp_tool(self, name: str, url: str, description: str = "") -> bool:
        """
        動態添加 MCP 工具

        Args:
            name: 工具名稱
            url: MCP Server URL (http/https/ws/wss)
            description: 工具描述

        Returns:
            bool: 是否成功添加
        """
        try:
            mcp_tool = MCPTool(
                name=name,
                description=description or f"MCP Tool: {name}",
                mcp_config={"url": url}
            )
            self._mcp_tools.append(mcp_tool)

            # 添加到 available_tools
            if hasattr(self, 'available_tools') and hasattr(self.available_tools, 'add_tool'):
                self.available_tools.add_tool(mcp_tool)

            logger.info(f"Dynamically added MCP Tool: {name} -> {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to add MCP Tool {name}: {e}")
            return False

    def add_mcp_tool_stdio(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        description: str = ""
    ) -> bool:
        """
        動態添加 stdio 模式的 MCP 工具

        Args:
            name: 工具名稱
            command: 執行命令 (python, npx, uvx 等)
            args: 命令參數
            env: 環境變數
            description: 工具描述

        Returns:
            bool: 是否成功添加
        """
        try:
            mcp_config = {
                "command": command,
                "args": args or [],
                "env": env or {}
            }
            mcp_tool = MCPTool(
                name=name,
                description=description or f"MCP Tool (stdio): {name}",
                mcp_config=mcp_config
            )
            self._mcp_tools.append(mcp_tool)

            # 添加到 available_tools
            if hasattr(self, 'available_tools') and hasattr(self.available_tools, 'add_tool'):
                self.available_tools.add_tool(mcp_tool)

            logger.info(f"Dynamically added MCP Tool (stdio): {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add MCP Tool {name}: {e}")
            return False

    async def list_mcp_server_tools(self, tool_name: str) -> List[Dict]:
        """
        列出指定 MCP Server 上可用的工具

        Args:
            tool_name: MCP 工具名稱

        Returns:
            List[Dict]: 可用工具列表
        """
        for mcp_tool in self._mcp_tools:
            if mcp_tool.name == tool_name:
                try:
                    return await mcp_tool.list_available_tools()
                except Exception as e:
                    logger.error(f"Failed to list tools from {tool_name}: {e}")
                    return []
        return []

    async def call_mcp_tool(self, tool_name: str, **kwargs) -> Any:
        """
        調用指定的 MCP 工具

        Args:
            tool_name: MCP 工具名稱
            **kwargs: 工具參數

        Returns:
            工具執行結果
        """
        for mcp_tool in self._mcp_tools:
            if mcp_tool.name == tool_name:
                try:
                    return await mcp_tool.execute(**kwargs)
                except Exception as e:
                    logger.error(f"MCP Tool {tool_name} execution failed: {e}")
                    raise
        raise ValueError(f"MCP Tool not found: {tool_name}")

    async def activate_skill(self, name: str) -> bool:
        """激活技能"""
        if self.skill_manager:
            return self.skill_manager.activate_skill(name)
        return False

    async def deactivate_skill(self, name: str) -> bool:
        """停用技能"""
        if self.skill_manager:
            return self.skill_manager.deactivate_skill(name)
        return False

    def is_skill_active(self, name: str) -> bool:
        """檢查技能是否激活"""
        if self.skill_manager:
            return self.skill_manager.is_skill_active(name)
        return False

    def list_skills(self) -> List[str]:
        """列出所有可用技能"""
        if self.skill_manager:
            return [s.name for s in self.skill_manager.list_available()]
        return []

    async def auto_activate_skills(self, text: str) -> List[str]:
        """根據文本自動激活技能"""
        if not self.auto_trigger_skills or not self.skill_manager:
            return []

        matched = self.skill_manager.match_skills(text)
        activated = []

        for skill_name in matched:
            if await self.activate_skill(skill_name):
                activated.append(skill_name)
                logger.info(f"Auto-activated skill: {skill_name}")

        return activated

    async def verify_and_advise(
        self,
        lat: float,
        long: float,
        post_text: Optional[str] = None
    ) -> str:
        """
        便捷方法：驗證危機並提供建議

        Args:
            lat: 緯度
            long: 經度
            post_text: 可選的求助貼文

        Returns:
            Agent 的回應
        """
        # 激活 crisis-response 技能
        if not self.is_skill_active("crisis-response"):
            await self.activate_skill("crisis-response")

        # 構建查詢
        query = f"Verify crisis at location ({lat}, {long})."
        if post_text:
            query += f"\n\nRelated post: {post_text}"

        # 執行 Agent
        return await self.run(query)

    def get_info(self) -> dict:
        """
        獲取 Agent 資訊

        Returns:
            包含 Agent 詳細資訊的字典
        """
        # 獲取技能列表
        skills_list = self.list_skills()

        # 獲取原生工具列表
        native_tools = [t.name for t in self.available_tools]

        # 獲取 MCP 工具詳細資訊
        mcp_tools_info = []
        for mcp_tool in self._mcp_tools:
            mcp_info = {
                "name": getattr(mcp_tool, 'name', str(mcp_tool)),
                "description": getattr(mcp_tool, 'description', ''),
            }
            if hasattr(mcp_tool, 'mcp_config'):
                config = mcp_tool.mcp_config
                if 'url' in config:
                    mcp_info["transport"] = "sse" if config['url'].startswith('http') else "ws"
                    mcp_info["url"] = config['url']
                elif 'command' in config:
                    mcp_info["transport"] = "stdio"
                    mcp_info["command"] = config['command']
            mcp_tools_info.append(mcp_info)

        return {
            "name": self.name,
            "version": "2.0.0",
            "description": self.description,
            "native_tools": native_tools,
            "mcp_tools": mcp_tools_info,
            "mcp_tools_count": len(self._mcp_tools),
            "skills": skills_list,
            "auto_trigger_skills": self.auto_trigger_skills,
            "max_steps": self.max_steps,
            "capabilities": {
                "mcp_server": True,  # 可作為 MCP Server
                "mcp_client": len(self._mcp_tools) > 0,  # 可作為 MCP Client
                "skills": len(skills_list) > 0,
            }
        }


def create_gaia_link_agent(**kwargs) -> GaiaLinkAgentV2:
    """
    工廠函數：創建 GaiaLinkAgentV2 實例

    Args:
        **kwargs: 傳遞給 Agent 的參數

    Returns:
        GaiaLinkAgentV2 實例
    """
    return GaiaLinkAgentV2(**kwargs)
