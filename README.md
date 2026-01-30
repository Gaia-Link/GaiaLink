# Gaia Link (蓋亞連結)

> 基於 3D 地球的「人道救援協作網絡」— 讓救援需求可視化，讓捐贈無損化

---

## 核心願景 (Vision)

**從「聽說哪裡有災情」到「看見哪裡缺資源」**

傳統的救援資訊往往是平面的文字報導，使用者難以直觀感受需求的緊急程度與規模。Gaia Link 透過 **3D 地球可視化**，用「光點」的密度與顏色來呈現捐款需求與緊急程度。

- **可視化 (Visualization):** 使用者能一眼看出哪些地區「點點特別多」（需求大、資源缺），哪些地區相對穩定，打破資訊不對稱。
- **無感協作 (Collaboration):** 透過 **SpoonOS** 實現意圖支付與智能調研，降低 Web3 使用門檻。

---

## 產品三大支柱

### 1. 視覺層：3D 需求地球 (The Living Globe)
將抽象的危機數據轉化為直觀的 3D 視覺體驗：
- **紅點聚落:** 代表緊急救援需求，點越密代表該區資源缺口越大。
- **直觀導航:** 旋轉地球查看全球災情，不再受限於單一新聞視角。
- **即時反饋:** 捐贈後的資金流向也會在地圖上呈現，讓愛心「看得見」。

### 2. 交互層：論壇與提案 (Geo-Forum & Proposals)
- **情境討論:** 每個災區都有專屬討論區，結合新聞與當地回報，讓社群判斷是否需要開啟新的捐贈池。
- **无需许可提案 (Permissionless):** 任何人都可以針對未被覆蓋的災情發起「募資提案」（Layer 2 機制）。

### 3. 智能層：SpoonOS Agent (大腦與金流)
利用 SpoonOS 強大的 Agent 能力，解決支付與信任問題：
- **意圖支付 (Intent Payment):** 使用者無需理解複雜鏈上操作，只需表達「我想捐款給土耳其」，Agent 自動處理穩定幣支付與路徑。
- **智能調研 (AI Research):** Agent 自動整理災情新聞、驗證真實性，幫助使用者決策「這個提案是否值得捐助」。
- **X402 標準:** 支援 X402 協議，實現 Agent 自主支付與授權。

---

## 資金池架構 (The Vaults)

我們設計了「雙層架構」與「兩種模式」，兼顧靈活性與安全性。

### 兩種捐贈模式
1. **直接捐贈 (Direct):** 資金直接進入機構帳戶，用於即時救援。
2. **無損捐贈 (No-Loss):** 資金存入 **Euler** 或 **Pendle** 的 Yield 模塊，僅將產生的利息捐贈給機構，本金保留給用戶。

### 雙層建立機制 (Layer 1 & Layer 2)

| 層級 | 發起人 | 機制 | 特點 |
|------|--------|------|------|
| **Layer 1 (機構層)** | 白名單機構 | **直接開池** | 機構經過驗證，可直接建立 Vault 接收捐款。適合大型已知組織 (如紅十字會)。 |
| **Layer 2 (社群層)** | 任何使用者 | **提案制 (Proposal)** | 使用者針對特定地區/事件發起提案 -> 資金存入過渡池 -> **達標後自動執行開 Vault** -> 資金流向指定機構。若未達標則退款。 |

> *註：本次黑客松中，機構與部分災情數據為 Mock 數據。*

---

## 團隊分工

| Role | 負責人 | 職責 |
|------|--------|------|
| Role 1 | Frontend Wizard | 視覺與互動 (Three.js, MapLibre, UI) |
| **Role 2** | **AI Engineer** | **SpoonOS Agent 核心邏輯 (本專案)** |
| Role 3 | Contract & Arch | 資金池合約 (Vaults) 與雙層架構設計 |
| Role 4 | PM & Design | 產品邏輯與敘事 |

---

## 技術棧

| 項目 | 技術 |
|------|------|
| **Frontend** | Next.js 15, React-Three-Fiber (3D Globe), MapLibre |
| **AI Agent** | **SpoonOS SDK**, LangChain, X402 Protocol |
| **Contracts** | Solidity, Euler/Pendle (Yield Integration) |
| **Data** | Polymarket (Mock/API), News API |

---

# SpoonOS AI Agent 子專案

> Role 2: AI Engineer - SpoonOS Agent 邏輯

---

## Agent 技術棧

| 項目 | 技術 |
|------|------|
| 語言 | Python 3.10+ |
| Agent 框架 | SpoonOS SDK (`spoon-ai-sdk>=0.3.6`) - React Agent |
| 數據驗證 | Pydantic |
| 配置管理 | pydantic-settings |
| 測試 | pytest（91.42% 覆蓋率，241 個測試） |

---

## 專案結構

```
python_agent/
├── gaia_link/
│   ├── agent.py           # GaiaLinkAgent (繼承 SpoonReactAI)
│   ├── schemas.py         # Pydantic 數據模型
│   ├── config.py          # 配置管理 (pydantic-settings)
│   ├── services/          # 服務層抽象
│   │   ├── base.py                  # BlockchainService 抽象基類
│   │   ├── mock_blockchain.py       # Mock 區塊鏈實作
│   │   ├── sepolia_blockchain.py    # Sepolia 測試網實作
│   │   ├── polymarket/              # Polymarket 服務
│   │   │   ├── base.py              # PolymarketService 抽象基類
│   │   │   ├── mock_polymarket.py   # Mock 實作
│   │   │   └── real_polymarket.py   # Gamma API 實作
│   │   ├── sentiment/               # Sentiment 服務
│   │   │   ├── base.py              # SentimentService 抽象基類
│   │   │   ├── mock_sentiment.py    # Mock 實作（規則基礎）
│   │   │   └── huggingface_sentiment.py  # HuggingFace ML 實作
│   │   ├── ratelimit/               # Rate Limiting 服務
│   │   │   ├── base.py              # RateLimiter 抽象基類
│   │   │   └── memory_ratelimit.py  # Token Bucket 實作
│   │   └── audit/                   # Audit Logging 服務
│   │       ├── base.py              # AuditLogger 抽象基類
│   │       └── memory_audit.py      # InMemory 實作
│   └── tools/
│       ├── verify_crisis.py         # 危機驗證工具
│       ├── analyze_sentiment.py     # 情感分析工具
│       └── execute_donation.py      # 捐款執行工具
├── tests/                 # 測試檔案 (241 tests)
├── main.py                # Demo 入口
└── pyproject.toml         # 專案配置
```

---

## 快速開始

```bash
cd python_agent

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安裝依賴
pip install -r requirements.txt

# 執行 Demo
python main.py

# 執行測試
pytest --cov=gaia_link
```

---

## 環境變數配置

```bash
# 區塊鏈服務 (默認: mock)
BLOCKCHAIN_NETWORK=mock           # mock | sepolia | mainnet
SEPOLIA_RPC_URL=https://...       # Sepolia 模式需要
WALLET_PRIVATE_KEY=...            # Sepolia 模式需要

# Polymarket 服務 (默認: mock)
POLYMARKET_MODE=mock              # mock | real
POLYMARKET_API_URL=https://gamma-api.polymarket.com
POLYMARKET_TIMEOUT=30

# Sentiment 服務 (默認: mock)
SENTIMENT_MODE=mock               # mock | huggingface
HUGGINGFACE_MODEL=distilbert-base-uncased-finetuned-sst-2-english
HUGGINGFACE_DEVICE=cpu            # cpu | cuda

# Rate Limiting (默認: 關閉)
RATE_LIMIT_ENABLED=false          # true | false
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Audit Logging (默認: 關閉)
AUDIT_LOGGING_ENABLED=false       # true | false
```

---

## 三個核心工具 API

### 1. `verify_crisis` - 驗證危機真實性

查詢 Polymarket 預測市場數據，比對地理位置判斷求助的可信度。

```python
result = await tool.execute(lat=37.5, long=37.0)

# 返回:
{
    "status": "VERIFIED" | "SUSPICIOUS" | "SCAM",
    "confidence": 0-100,
    "polymarket_events": [...],
    "risk_factors": [...],
    "recommendation": "..."
}
```

**支援的危機區域 (Mock)：**

| 區域 | 緯度範圍 | 經度範圍 |
|------|----------|----------|
| 土耳其-敘利亞地震 | 36-39 | 35-42 |
| 菲律賓颱風 | 5-20 | 117-127 |
| 烏克蘭衝突 | 44-52 | 22-40 |
| 加薩人道危機 | 31-32 | 34-35 |
| 日本地震 | 32-42 | 130-145 |

---

### 2. `analyze_sentiment` - 分析貼文情感

分析求助貼文的緊急程度、情緒指標，並檢測詐騙紅旗。

```python
result = await tool.execute(
    text="Help! Earthquake destroyed our home!",
    context={"account_age_days": 30}
)

# 返回:
{
    "urgency_level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
    "authenticity_score": 0-100,
    "emotional_indicators": ["fear", "desperation"],
    "red_flags": [...],
    "summary": "..."
}
```

---

### 3. `execute_donation` - 執行捐款

執行區塊鏈捐款交易，支援 USDC、USDT、ETH、DAI。

```python
result = await tool.execute(
    amount=100,
    token="USDC",
    recipient_address="0x..."
)

# 返回:
{
    "success": true,
    "transaction_id": "0x...",
    "status": "confirmed",
    "details": {
        "amount_sent": 100,
        "token": "USDC",
        "gas_fee": 0.003,
        "total_cost_usd": 107.50
    },
    "explorer_url": "https://etherscan.io/tx/..."
}
```

---

## SpoonOS 合規性

| 要求 | 狀態 | 證據 |
|------|------|------|
| 基於 SpoonOS 構建 | OK | `from spoon_ai.agents import SpoonReactAI` |
| 使用 React Agent 體系 | OK | `class GaiaLinkAgent(SpoonReactAI)` |
| Agent 承擔實際功能 | OK | 三個核心工具，非 Demo 展示 |
| 工具繼承 BaseTool | OK | `from spoon_ai.tools.base import BaseTool` |

---

## 開發路線圖

### Phase 1: 區塊鏈服務層 - DONE

- BlockchainService 抽象基類
- MockBlockchainService（Mock 模式）
- SepoliaBlockchainService（測試網模式）
- 依賴注入與配置管理

### Phase 2: Polymarket API 整合 - DONE

- PolymarketService 抽象基類
- MockPolymarketService（5 個危機區域）
- RealPolymarketService（gamma-api 整合）
- VerifyCrisisTool 重構

### Phase 3: ML 情感分析模型 - DONE

- SentimentService 抽象基類
- MockSentimentService（規則基礎分析）
- HuggingFaceSentimentService（transformers 整合）
- AnalyzeSentimentTool 重構

### Phase 4: Rate Limiting + Audit Logging - DONE

- RateLimiter 抽象基類（Token Bucket 算法）
- InMemoryRateLimiter（內存實作）
- AuditLogger 抽象基類（結構化日誌）
- InMemoryAuditLogger（內存實作）

---

## 服務層 Mock vs Real

| 服務 | Mock 模式 | Real 模式 | 切換變數 |
|------|-----------|-----------|----------|
| Blockchain | MockBlockchainService | SepoliaBlockchainService | `BLOCKCHAIN_NETWORK` |
| Polymarket | MockPolymarketService | RealPolymarketService | `POLYMARKET_MODE` |
| Sentiment | MockSentimentService | HuggingFaceSentimentService | `SENTIMENT_MODE` |

---

## 測試結果

```
============================= 241 passed ==============================
Coverage: 91.42%
```

---

## 授權

MIT License
