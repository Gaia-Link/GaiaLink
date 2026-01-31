# Gaia Link - SpoonOS AI Agent 專案規範

## 專案定位

**Gaia Link** 是一個基於 **SpoonOS Agent** 和 Web3 技術的人道救援協作網絡，參加 **SpoonOS Hackathon**。將危機驗證、捐款執行和情感分析整合為一體，展示 Agent 在人道救援領域的實際應用。

---

## 強制要求 (Hackathon 合規)

### SpoonOS 最低技術使用要求

1. **必須基於 SpoonOS 構建**
   - 使用 `spoon-ai-sdk>=0.3.6`
   - Agent 繼承 `SpoonReactAI` 類別
   - 工具繼承 `BaseTool` 類別

2. **必須使用 React Agent 體系**
   - `from spoon_ai.agents import SpoonReactAI`
   - `class GaiaLinkAgent(SpoonReactAI)`

3. **Agent 承擔核心功能**
   - 危機驗證、情感分析、捐款執行
   - 非 Demo 展示，執行真實業務邏輯

---

## 三層架構設計

```
┌─────────────────────────────────────────────────────────────────┐
│                    Single Source of Truth                        │
│                  backend_data/data.json                          │
│          (所有危機事件、機構、提案、狀態信息)                    │
└─────────────┬───────────────────────────────────┬───────────────┘
              │                                   │
     ┌────────▼──────────┐              ┌────────▼──────────┐
     │   Frontend        │              │  Python Agent      │
     │  (Next.js 15)     │              │  (SpoonOS)         │
     ├──────────────────┤              ├──────────────────┤
     │ - Visualization  │              │ - Logic & State  │
     │ - 3D 地球渲染   │              │ - NLU 意圖解析  │
     │ - UI 交互        │              │ - 工具執行       │
     │ - 錢包連接       │              │ - 決策生成       │
     └────────┬──────────┘              └────────┬──────────┘
              │                                   │
              └───────────────┬───────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Smart Contracts │
                    │   (Sepolia)       │
                    └───────────────────┘
```

---

## 三大核心功能支柱

### 1. 視覺層：3D 需求地球 (The Living Globe)
- **MapLibre GL** + **react-map-gl** 渲染互動地球
- 紅點聚落代表緊急救援需求，點密度反映資源缺口
- 根據 `severity` (CRITICAL/HIGH/MODERATE) 和 `hasVault` 動態著色
- 支援旋轉、縮放、點擊交互

### 2. 交互層：論壇與提案 (Geo-Forum & Proposals)
- 每個災區專屬討論區，結合新聞與當地回報
- **無需許可提案 (Permissionless)**: 任何人可發起捐款提案
- Agent 通過 `AnalyzeSentimentTool` 分析貼文真實性和緊急程度
- 詐騙檢測：識別紅旗標記（新帳號、關鍵字異常、要求直轉）

### 3. 智能層：SpoonOS Agent (大腦與金流)
- **意圖支付**: 用戶說「捐 100 USDC 到土耳其」，Agent 自動處理
- **智能調研**: 查詢 Polymarket 驗證危機真實性
- **X402 標準**: HTTP 402 協議的自主支付授權

---

## Agent 工具清單

| 工具 | 功能 | 文件位置 |
|------|------|----------|
| `verify_crisis` | 危機驗證 (Polymarket) | `tools/verify_crisis.py` |
| `analyze_sentiment` | 情感分析 | `tools/analyze_sentiment.py` |
| `execute_donation` | 捐款執行 | `tools/execute_donation.py` |
| `list_crises` | 列出活躍危機 | `tools/list_crises.py` |
| `create_proposal` | 建立募資提案 | `tools/create_proposal.py` |
| `contribute_proposal` | 貢獻提案 | `tools/contribute_proposal.py` |
| `activate_proposal` | 激活提案 | `tools/activate_proposal.py` |
| `withdraw_contribution` | 撤回貢獻 | `tools/withdraw_contribution.py` |
| `query_proposals` | 查詢提案 | `tools/query_proposals.py` |
| `list_institutions` | 列出白名單機構 | `tools/list_institutions.py` |
| `x402_payment` | X402 支付工具集 | `tools/x402_payment.py` |

---

## 資金池雙層架構

### Layer 1 (機構層)
- **發起人**: 白名單機構 (Red Cross 等)
- **機制**: 直接開池
- **合約**: `GaiaCharityRegistry.sol`

### Layer 2 (社群層)
- **發起人**: 任何用戶
- **機制**: 提案制，達標後自動部署 Vault
- **合約**: `GaiaProposalManager.sol`

### 捐贈模式
| 模式 | 說明 | 合約 |
|------|------|------|
| **Direct Vault** | 資金直接進入機構帳戶 | `DirectVault.sol` |
| **No-Loss Vault** | 本金保留，利息捐贈 (DeFi 策略) | `NoLossVault.sol` |

---

## 服務層架構 (Mock/Real 切換)

| 服務 | 環境變數 | Mock 實現 | Real 實現 |
|------|----------|-----------|-----------|
| 區塊鏈 | `BLOCKCHAIN_NETWORK` | MockBlockchainService | SepoliaBlockchainService |
| Polymarket | `POLYMARKET_MODE` | MockPolymarketService | RealPolymarketService |
| 情感分析 | `SENTIMENT_MODE` | MockSentimentService | HuggingFaceSentimentService |
| 限流 | `RATE_LIMIT_ENABLED` | InMemoryRateLimiter | - |
| 審計 | `AUDIT_LOGGING_ENABLED` | InMemoryAuditLogger | - |

---

## 目錄結構

```
GaiaLink_Original/
├── frontend/                 # Next.js 15 前端
│   ├── src/app/             # App Router
│   ├── src/features/        # 功能模塊 (globe, forum, donation)
│   └── src/providers/       # Web3Provider (Wagmi/RainbowKit)
│
├── python_agent/            # SpoonOS Agent 核心
│   ├── gaia_link/
│   │   ├── agent.py         # GaiaLinkAgent (SpoonReactAI)
│   │   ├── agent_v2.py      # V2 版本
│   │   ├── config.py        # 配置管理 (pydantic-settings)
│   │   ├── schemas.py       # Pydantic I/O 模型
│   │   ├── tools/           # 13 個工具
│   │   ├── services/        # 7 個服務層
│   │   └── skills/          # 3 個技能定義
│   └── tests/               # 測試 (91.42% 覆蓋率)
│
├── contracts/               # Solidity 智能合約 (Foundry)
│   ├── src/vaults/          # DirectVault, NoLossVault
│   ├── src/proposals/       # GaiaProposalManager
│   └── src/access/          # GaiaCharityRegistry
│
├── backend_data/            # JSON 數據源
│   ├── data.json            # Single Source of Truth
│   └── db_service.py        # 數據服務
│
└── 文檔
    ├── AGENT_API.md         # Agent 交互接口文檔
    ├── AGENT_TASKS.md       # Agent 開發清單
    └── README.md            # 項目簡介
```

---

## 技術棧

### Frontend
- Next.js 16.1.6 / React 19.2.3
- Wagmi 2.14.0 + RainbowKit 2.2.10
- MapLibre GL 5.17.0 + react-map-gl 8.1.0
- TanStack Query 5.90.20
- Tailwind CSS 4

### Agent
- Python 3.10+ / SpoonOS SDK >=0.3.6
- Pydantic 2.10+ / pydantic-settings 2.0+
- aiohttp 3.9+ / web3.py 6.0+
- transformers 4.30+ (可選，ML 情感分析)

### Contracts
- Solidity ^0.8.20 / Foundry
- OpenZeppelin 4.x (ERC20, Ownable)
- 測試網: Ethereum Sepolia

---

## Agent 標準回應格式

```python
{
  "message": "Human-readable response (繁體中文)",
  "action_taken": "verify_crisis|execute_donation|create_proposal|...",
  "ui_hints": {
    "mode": "IDLE|DECISION|SIGNATURE|PROCESSING",
    "display_data": {
      "title": "...",
      "badge_text": "...",
      "badge_color": "green|yellow|red",
      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"
    },
    "actions": [
      { "label": "Direct Donate", "type": "donate_direct", "icon": "coins" }
    ]
  },
  "transaction_payload": {  # 若有簽名需求
    "to": "0x...",
    "value": "0",
    "data": "0x...",
    "chainId": 11155111,
    "gas": "65000"
  }
}
```

---

## 開發規範

### 代碼風格
- 所有 Agent 邏輯使用 `spoon-ai-sdk`
- 工具繼承 `BaseTool` 類別
- Agent 繼承 `SpoonReactAI` 類別
- 測試覆蓋率目標: 80%+
- 不可變性原則 (Immutability)
- 文件 < 800 行，函數 < 50 行

### 安全要求
- 無硬編碼密鑰
- 所有用戶輸入驗證
- SQL 注入防護
- XSS 防護

### Git 規範
- Commit 格式: `<type>: <description>`
- Types: feat, fix, refactor, docs, test, chore, perf, ci
- 不標記 AI 為 co-author

---

## 開發階段完成狀態

| Phase | 狀態 | 內容 |
|-------|------|------|
| 1 | ✅ | 區塊鏈服務層 (Mock/Sepolia) |
| 2 | ✅ | Polymarket API 整合 |
| 3 | ✅ | ML 情感分析服務 |
| 4 | ✅ | Rate Limiting + Audit |
| 5 | ✅ | 提案系統 (V2) |
| 6 | ✅ | X402 支付協議 (V2) |

---

## SpoonOS 官方資源

- GitHub: [XSpoonAi/spoon-core](https://github.com/XSpoonAi/spoon-core)
- GitHub: [XSpoonAi/spoon-toolkit](https://github.com/XSpoonAi/spoon-toolkit)
- GitHub: [XSpoonAi/spoon-starter](https://github.com/XSpoonAi/spoon-starter)

---

## 數據一致性原則

**核心**: 前後端共用 `backend_data/data.json` 作為 Single Source of Truth

- 前端: 透過 `/api/crises` 讀取
- Agent: 透過 `db_service.py` 直接載入
- **用戶在地圖上看到的 = Agent 知道的**
