# GaiaLink

**去中心化人道主義援助平台** - 讓救援需求可視化，讓捐贈無損化

---

## 核心功能

### 3D 地球災難可視化
透過互動式 3D 地球呈現全球災情，紅點密度反映資源缺口，一眼看出哪些地區最需要援助。

### 雙模式 USDC 捐款
| 模式 | 說明 |
|------|------|
| **直接捐款** | 資金即時進入救援機構帳戶 |
| **無損收益捐款** | 本金保留，僅將 DeFi 利息捐贈 |

### 社群提案系統
任何人可針對未被覆蓋的災情發起募資提案，達標後自動部署資金池。

---

## 技術棧

| 層級 | 技術 |
|------|------|
| **Frontend** | Next.js 16, React 19, MapLibre GL, Wagmi, RainbowKit |
| **Smart Contracts** | Solidity, Foundry, OpenZeppelin |
| **Network** | Ethereum Sepolia (USDC) |

---

## 智能合約

| 合約 | 功能 |
|------|------|
| `GaiaCharityRegistry` | 白名單機構註冊與管理 |
| `GaiaProposalManager` | 社群提案與投票機制 |
| `DirectVault` | 直接捐款資金池 |
| `NoLossVault` | 無損收益捐款資金池 |

---

## 快速開始

### 環境需求
- Node.js 20+
- pnpm (推薦) 或 npm
- Foundry (合約開發)

### 前端啟動

```bash
cd frontend
pnpm install
pnpm dev
```

開啟 http://localhost:3000

### 合約編譯

```bash
cd contracts
forge build
```

### 環境變數

複製 `.env.example` 為 `.env` 並填入：

```bash
# RPC & 錢包
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_project_id

# 合約地址 (Sepolia)
NEXT_PUBLIC_CHARITY_REGISTRY_ADDRESS=0x...
NEXT_PUBLIC_PROPOSAL_MANAGER_ADDRESS=0x...
```

---

## SpoonOS Agent

GaiaLink 整合 SpoonOS AI Agent，提供智能化的捐款協助和危機驗證。

### MCP Server (Model Context Protocol)

Agent 透過 FastMCP 框架暴露以下服務供其他 Agent 調用：

| MCP Tool | 功能 |
|----------|------|
| `verify_crisis` | 驗證危機真實性（整合 Polymarket 預測市場） |
| `analyze_crisis_sentiment` | 分析求助文本的情感與緊急程度 |
| `estimate_donation` | 估算捐款總成本（含 Gas 費用） |
| `get_donation_history` | 查詢用戶歷史捐款記錄 |
| `get_transaction_status` | 追蹤單筆交易狀態 |

**啟動 MCP Server：**
```bash
cd python_agent
python -m gaia_link.mcp_server        # stdio 模式
python -m gaia_link.mcp_server --sse  # SSE 模式 (HTTP)
```

### Agent Skills

Agent 內建 4 個技能模組，根據用戶意圖自動觸發：

| 技能 | 觸發關鍵字 | 功能 |
|------|-----------|------|
| **crisis-response** | 危機、災難、地震、洪水 | 驗證危機真實性、詐騙偵測、情感分析 |
| **donation-advisor** | 捐款、捐贈、幫助 | 費用優化、安全檢查、捐款建議 |
| **donation-tracker** | 追蹤、狀態、歷史 | 交易追蹤、歷史查詢、狀態報告 |
| **pool-manager** | 資金池、金庫、餘額 | 池子監控、收益分析、智能分配 |

### Agent Tools

| 工具 | 功能 |
|------|------|
| `VerifyCrisisTool` | 查詢 Polymarket 驗證危機 |
| `AnalyzeSentimentTool` | HuggingFace 情感分析 |
| `ExecuteDonationTool` | 執行鏈上捐款 |
| `CreateProposalTool` | 創建社群提案 |
| `ContributeProposalTool` | 向提案貢獻資金 |
| `ActivateProposalTool` | 激活達標提案 |
| `QueryProposalsTool` | 查詢提案狀態 |
| `X402PaymentTool` | HTTP 402 微支付 |

### Agent Services

| 服務 | 說明 |
|------|------|
| `PolymarketService` | 預測市場數據查詢 |
| `SentimentService` | 文本情感分析 (HuggingFace) |
| `BlockchainService` | 鏈上交易執行 |
| `DonationHistoryService` | 捐款記錄管理 |
| `PoolService` | 資金池狀態管理 |
| `RateLimitService` | API 速率限制 |
| `AuditService` | 操作審計日誌 |

---

## 項目結構

```
GaiaLink_Original/
├── frontend/              # Next.js 前端應用
│   └── src/
│       ├── app/           # App Router 頁面
│       ├── features/      # 功能模塊 (地球、捐款、提案)
│       └── providers/     # Web3 Provider
│
├── contracts/             # Solidity 智能合約
│   └── src/
│       ├── vaults/        # DirectVault, NoLossVault
│       ├── proposals/     # GaiaProposalManager
│       └── access/        # GaiaCharityRegistry
│
├── python_agent/          # SpoonOS AI Agent
│   └── gaia_link/
│       ├── mcp_server.py  # MCP 服務入口
│       ├── agent.py       # Agent 主類
│       ├── tools/         # 13 個 Agent 工具
│       ├── skills/        # 4 個技能模組
│       └── services/      # 7 個後端服務
│
└── backend_data/          # Mock 數據 (Hackathon Demo)
```

---

## 授權

MIT License
