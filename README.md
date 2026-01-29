# Gaia Link (蓋亞連結)

> 基於 3D 地球的「人道救援協作網絡」

---

## 核心願景

**一句話介紹：**

Gaia Link 是一個基於 3D 地球的**「人道救援協作網絡」**。我們將宏觀的危機數據 (Polymarket) 與微觀的現場聲音 (Geo-Forum) 結合，並由 **SpoonOS AI Agent** 負責驗證資訊真實性與執行無感支付。

**核心邏輯：**

- **看見 (Visualize):** 用 3D 地球打破資訊孤島，直觀展示哪裡「紅了」（有危機）。
- **連結 (Connect):** 點擊紅區進入「地圖論壇」，看到當地人的真實求救與照片。
- **行動 (Action):** SpoonOS Agent 實時驗證貼文真偽，並協助用戶一鍵跨鏈捐贈。

---

## 產品三大支柱

### A. 視覺層：The Living Globe (前端核心)

- **上帝視角：** 使用 `Three.js` / `react-globe.gl`
- **數據分層：**
  - Red Zones (熱區): 來自 Polymarket 的災難預測數據
  - Blue Bubbles (聲音): 論壇貼文的聚合氣泡
  - Green Nodes (組織): 經過驗證的救援 DAO 或公益錢包

### B. 交互層：The Geo-Forum (論壇與社群)

- **形式：** 覆蓋在地球上的 Overlay（側邊欄或懸浮窗）
- **內容：** 「現場照片」、「需求清單」、「情況更新」
- **體驗：** 就像在 Google Maps 上看餐廳評論，但這裡是看災區需求

### C. 智能層：SpoonOS Agent (大腦與手腳) - **本子專案**

- **角色 1 - 審計師 (Auditor):** 自動掃描 Polymarket 和新聞源，給出「資訊可信」或「疑似詐騙」的標籤
- **角色 2 - 支付官 (Payer):** 負責後端的 Swap、Gas 費計算和轉帳，用戶只需確認意圖

---

## 團隊分工

| Role | 負責人 | 職責 |
|------|--------|------|
| Role 1 | Frontend Wizard | 視覺與互動 (react-globe.gl, 論壇 UI) |
| **Role 2** | **AI Engineer** | **SpoonOS Agent 邏輯 (本專案)** |
| Role 3 | Data & Backend | 數據流與模擬 (Polymarket API) |
| Role 4 | PM & Storyteller | 簡報與流程 |

---

## 技術棧

| 項目 | 技術 |
|------|------|
| Frontend | Next.js, Three.js (react-globe.gl), Tailwind CSS |
| AI Agent | SpoonOS SDK (LangChain/ReAct pattern) |
| Data Source | Polymarket API (CLOB/Gamma), GDELT (Optional) |
| Storage | JSON (MVP) / Arweave (Bonus) |

---

# SpoonOS AI Agent 子專案

> Role 2: AI Engineer - SpoonOS Agent 邏輯

---

## Agent 技術棧

| 項目 | 技術 |
|------|------|
| 語言 | Python 3.10+ |
| Agent 框架 | SpoonOS SDK (`spoon-ai`) - React Agent |
| 數據驗證 | Pydantic |
| 測試 | pytest（93%+ 覆蓋率，134 個測試） |

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
│   │   └── polymarket/              # Polymarket 服務
│   │       ├── base.py              # PolymarketService 抽象基類
│   │       ├── mock_polymarket.py   # Mock 實作
│   │       └── real_polymarket.py   # 真實 API 實作
│   └── tools/
│       ├── verify_crisis.py         # 危機驗證工具
│       ├── analyze_sentiment.py     # 情感分析工具
│       └── execute_donation.py      # 捐款執行工具
├── tests/                 # 測試檔案
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

### Phase 3: ML 情感分析模型 - PENDING

- Hugging Face Transformers 整合
- 本地推理 / API 模式切換

### Phase 4: Rate Limiting + Audit Logging - PENDING

- 請求限流機制
- 審計日誌系統

---

## 測試結果

```
============================= 134 passed ==============================
Coverage: 93.07%
```

---

## 授權

MIT License
