# SpoonOS Agent 交互接口文檔 (GaiaLink)

本文檔定義前端 (Frontend) 與 SpoonOS Agent (Python Backend) 之間的數據交互標準。

## 1. 前端發送給 Agent 的數據 (Request)

前端透過 API (如 POST `/api/agent/chat`) 發送用戶意圖與當前上下文。

```json
{
  "message": "用戶輸入的自然語言 (例如: '這看起來很嚴重，我想捐款')",
  "context": {
    "selected_point": {
      "id": "turkey_quake_2023",
      "lat": 37.166,
      "lng": 38.795,
      "label": "Turkey-Syria Earthquake",
      "type": "crisis",
      "description": "7.8 Magnitude Earthquake..."
    },
    "user_wallet_address": "0x123...abc", // 可選，若已連接錢包
    "current_view": {
        "lat": 37.166,
        "lng": 38.795,
        "zoom": 5
    }
  }
}
```

### 字段說明
*   **message**: 用戶在膠囊 (Capsule) 輸入的文字或語音轉文字結果。
*   **context**: 讓 Agent 理解用戶 "看在哪裡"。
    *   `selected_point`: 當前點選的地球危機點（這是 `VerifyCrisisTool` 的核心輸入）。
    *   `user_wallet_address`: 用於後續生成支付交易。

---

## 2. Agent 執行的邏輯 (Agent Logic)

Agent 收到請求後，會根據 `system_prompt` 分析意圖並調用工具：

1.  **意圖識別**:
    *   如果是「驗證/查詢」 (Verify) -> 調用 `VerifyCrisisTool`。
    *   如果是「捐款/支付」 (Donate) -> 調用 `ExecuteDonationTool`。
    *   如果是「情感/輿論分析」 -> 調用 `AnalyzeSentimentTool`。

2.  **工具執行 (Tools)**:
    *   **VerifyCrisisTool**: 使用 `lat/lng` 在 Polymarket 搜尋相關預測事件，並抓取新聞確認真實性。
    *   **ExecuteDonationTool**: 計算 Gas Fee，檢查餘額，生成交易數據 (Payload)。
    *   **AnalyzeSentimentTool**: 分析文本的緊急程度與情緒指標。

3.  **決策生成**:
    *   Agent 綜合工具結果，生成一段 "Human Readable" 的建議 (Message)。
    *   決定 UI 應該如何變化 (例如彈出決策卡片)。

---

## 3. Agent 回傳給前端的數據 (Response)

Agent 回傳標準化的 JSON 結構，驅動前端 "Dynamic Capsule" 的狀態變化。

```json
{
  "message": "已確認該地區為高風險危機區域。Polymarket 預測顯示事件真實性為 95%。建議立即援助。",
  
  "action_taken": "verify_and_suggest", // 標識 Agent 做了什麼
  
  "recommendation": { // 【決策核心】用於顯示在卡片上的醒目建議
    "action": "PROCEED", // PROCEED (綠) | CAUTION (黃) | ABORT (紅)
    "confidence": 95,    // 信心分數 (0-100)
    "reason": "多個消息來源與預測市場數據吻合，且當地有人道救援需求。"
  },

  "ui_hints": { // 【UI 指令】前端根據此字段改變膠囊狀態
    "mode": "DECISION", // 指示切換到決策卡片模式 (DECISION | PROCESSING | IDLE)
    "display_data": {   // 卡片內顯示的詳細數據
        "title": "Turkey-Syria Earthquake",
        "badge_text": "Verified Crisis",
        "badge_color": "green",
        "risk_level": "CRITICAL"
    },
    "actions": [ // 卡片下方的按鈕動態配置
        {
            "label": "Direct Donate",
            "type": "donate_direct",
            "icon": "coins"
        },
        {
            "label": "Yield Donate (APY 4.5%)",
            "type": "donate_yield",
            "icon": "trending_up"
        }
    ]
  },

  "tool_results": [ // (可選) 原始工具數據，用於開發調試或顯示詳細圖表
    {
      "tool_name": "verify_crisis",
      "status": "success",
      "data": {
        "polymarket_events": [...]
      }
    }
  ]
}
```

### 字段說明
*   **message**: Agent 的自然語言回覆，顯示在卡片的主文本區。
*   **recommendation**: 結構化的決策建議，前端可用來渲染顏色 (綠/紅) 和信心指數。
*   **ui_hints**: **最重要**。這直接控制前端 `SpoonOSInterface.tsx` 的狀態機。
    *   `mode`: 告訴前端變形成什麼樣子 (例如變形成大卡片 `DECISION`)。
    *   `actions`: 告訴前端顯示哪些按鈕 (例如推薦 Yield Donate)。

---

## 4. 交易與 Vault 機制 (Transaction & Vaults)

GaiaLink 的核心是讓用戶能選擇將資金投入不同類型的 **Vault (資金池)**。Agent 負責根據用戶意圖生成對應的區塊鏈交易數據。

### 兩種 Vault 類型
1.  **Direct Give Vault (直接捐贈池)**:
    *   資金直接轉移到受助機構或地區的多簽錢包。
    *   特點：即時到帳，無收益。
2.  **Yield Give Vault (無損/收益捐贈池)**:
    *   資金存入 Euler / Pendle 等 DeFi 協議。
    *   本金保留，產生的 **Yield (收益)** 自動捐贈給目標。
    *   特點：長期支持，本金可贖回。

### 交易請求流程 (Transaction Flow)

GaiaLink 提供兩種捐款模式：
1.  **手動模式 (Manual Mode)**: 用戶直接在 UI 點擊 "Direct Donate" 或 "Yield Donate"，前端直接與合約交互 (Standard dApp Flow)。
2.  **Agent 意圖模式 (Agent Intent Mode)**: 用戶透過對話說出意圖 (例如："幫我把 100 USDC 存入土耳其的生息池")，Agent 負責組裝交易。

以下描述的是 **Agent 意圖模式** 的交互：

**Request (Frontend -> Agent):**
前端 **不需要** 預先判斷意圖或組裝 JSON，只需將用戶的自然語言 (語音轉文字或輸入) 原樣發送。

```json
{
  "message": "我要捐款 100 USDC 到土耳其的生息池 (Yield Vault)",
  "context": {
    "selected_point_id": "turkey_quake_2023"
  }
}
```

**Agent 內部處理 (NLU & Intent Parsing):**
Agent 收到訊息後，分析語意並提取關鍵參數：
*   Intent: `EXECUTE_TRANSACTION`
*   Amount: `100`
*   Token: `USDC`
*   Vault Type: `YIELD` (識別出 "生息池" / "Yield")

**Response (Agent -> Frontend):**
Agent 回傳構造好的交易 Payload，前端直接喚起簽名：

```json
{
  "status": "ready_to_sign",
  "transaction_payload": {
    "to": "0xYieldVaultAddress...", // Agent 自動路由到正確的 Euler/Pendle Vault
    "data": "0x...",               // 編碼後的合約調用數據
    "value": "0",
    "chain_id": 11155111
  },
  "explanation": "即將將 100 USDC 存入土耳其賑災基金的 Yield Vault (Euler 協議)。預計年化收益 4.5% 將持續捐贈。"
}
```

---

## 總結流程

1.  **用戶** 按下 Space -> 輸入 "Help Turkey"。
2.  **前端** 發送 `message: "Help Turkey"`, `context: {Turkey Point}`。
3.  **Agent** 調用 `VerifyCrisisTool` -> 確認真實性。
4.  **Agent** 回傳 `ui_hints.mode = "DECISION"` 和 `recommendation.action = "PROCEED"`。
5.  **前端** 膠囊變形為大卡片，顯示 "Direct Donate" 和 "Yield Donate" 按鈕。
6.  **用戶** 點擊 "Yield Donate"。
7.  **前端** 請求 Agent 生成 Yield Vault 的交易數據。
8.  **Agent** 回傳 `transaction_payload`。
9.  **前端** 喚起 MetaMask / RainbowKit 讓用戶簽名。
