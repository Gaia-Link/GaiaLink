# Gaia Link - SpoonOS AI Agent

> 人道救援協作網絡的 AI 智能層子專案

---

## 簡介

這是 Gaia Link 專案中的 **SpoonOS Agent 子專案**（Role 2: AI Engineer），負責實作 AI 智能層功能。

**Agent 扮演兩個角色：**
- **審計師 (Auditor):** 驗證危機求助貼文的真實性，比對 Polymarket 預測市場數據
- **支付官 (Payer):** 執行安全的區塊鏈捐款交易，計算 Gas 費用

---

## 技術棧

| 項目 | 技術 |
|------|------|
| 語言 | Python 3.10+ |
| Agent 框架 | SpoonOS SDK (`spoon-ai`) - React Agent |
| 數據驗證 | Pydantic |
| 測試 | pytest（97%+ 覆蓋率，50 個測試） |

---

## 專案結構

```
python_agent/
├── gaia_link/
│   ├── agent.py           # GaiaLinkAgent (繼承 SpoonReactAI)
│   ├── schemas.py         # Pydantic 數據模型
│   └── tools/
│       ├── verify_crisis.py      # 危機驗證工具
│       ├── analyze_sentiment.py  # 情感分析工具
│       └── execute_donation.py   # 捐款執行工具
├── tests/                 # 測試檔案
├── main.py                # Demo 入口
├── pyproject.toml         # 專案配置
└── requirements.txt       # 依賴清單
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

**內建 Mock 危機區域：**

| 區域 | 緯度範圍 | 經度範圍 |
|------|----------|----------|
| 土耳其地震 | 36-39 | 35-42 |
| 菲律賓颱風 | 5-20 | 117-127 |
| 烏克蘭衝突 | 44-52 | 22-40 |
| 加薩人道危機 | 31-32 | 34-35 |

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

模擬區塊鏈捐款交易，支援 USDC、USDT、ETH、DAI。

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
| 基於 SpoonOS 構建 | ✅ | `from spoon_ai.agents import SpoonReactAI` |
| 使用 React Agent 體系 | ✅ | `class GaiaLinkAgent(SpoonReactAI)` |
| Agent 承擔實際功能 | ✅ | 三個核心工具，非 Demo 展示 |
| 工具繼承 BaseTool | ✅ | `from spoon_ai.tools.base import BaseTool` |

**程式碼片段：**

```python
# gaia_link/agent.py
from spoon_ai.agents import SpoonReactAI
from spoon_ai.tools import ToolManager

class GaiaLinkAgent(SpoonReactAI):
    name = "gaia_link_agent"
    available_tools = ToolManager([
        VerifyCrisisTool(),
        AnalyzeSentimentTool(),
        ExecuteDonationTool(),
    ])

# gaia_link/tools/verify_crisis.py
from spoon_ai.tools.base import BaseTool

class VerifyCrisisTool(BaseTool):
    name = "verify_crisis"
    async def execute(self, lat, long): ...
```

---

## 測試結果

```
============================= 50 passed in 58.97s ==============================
Coverage: 97.12%
```

---

## 授權

MIT License
