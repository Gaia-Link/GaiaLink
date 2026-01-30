# SpoonOS Agent 交互接口文檔 (GaiaLink)

本文檔定義前端 (Frontend) 與 SpoonOS Agent (Python Backend) 之間的數據交互標準。

## 1. 系統與數據架構 (System & Data Architecture)

為了確保 Hackathon Demo 的一致性，Frontend 與 Agent 共用同一份數據源：**`backend_data/data.json`**。這確保了 Visualization (前端顯示) 與 Logic (Agent 認知) 的狀態是完全同步的。

### 1.1 核心組件與數據流
*   **Backend Data (`data.json`)**: **Single Source of Truth**。包含所有危機事件 (Crisis)、資金池 (Vaults) 與驗證資訊。
*   **Frontend (Next.js)**:
    *   **Access**: 透過 `/api/crises` (Internal API) 讀取數據。
    *   **Role**: **Visualization**。負責將 `data.json` 渲染到 3D 地球上，並根據 `severity` 與 `hasVault` 顯示不同顏色 ($/Need)。
*   **Agent (Python/SpoonOS)**:
    *   **Access**: 透過 `db_service.py` 直接載入數據。
    *   **Role**: **Logic & State**。負責 NLU 意圖解析、RAG 檢索 (例如用戶問 "哪裡有火災" 時查詢 DB)、以及模擬寫入 (In-Memory Proposal Creation)。

### 1.2 優勢
1.  **一致性 (Consistency)**: 用戶在地圖上看到的，就是 Agent 知道的。不會出現「地圖上有點，但 Agent 說不知道」的情況。
2.  **效能 (Performance)**: 前端不需要把整包數據傳給 Agent，只需傳送 Prompt，Agent 自己去查 DB。
3.  **開發速度 (Velocity)**: 修改 `data.json` 一次，前後端同時更新，極適合 Hackathon 迭代。

## 2. 前端發送給 Agent 的數據 (Request)

API Endpoint: `POST /api/agent/chat`

為了讓 Agent 介面更通用，前端只需發送 **單一 prompt 字串**。
如果是 "Context Mode" (例如用戶點選了土耳其)，前端可以自動將該資訊附加在 Prompt 中 (例如: "關於 Turkey-Syria Earthquake, ...")，或者完全依賴用戶在對話中提及。

```json
{
  "message": "這裡的情況如何？" // 若有選中點，前端可預處理為 "Tell me about Turkey-Syria Earthquake situations"
}
```

### Agent 處理邏輯
*   **NLU 解析**: Agent 使用 LLM 解析 `message`。
    *   若 Message 包含具體地點/事件 (e.g., "Turkey Earthquake") -> Agent 查詢 DB 中的該事件。
    *   若 Message 為模糊詢問 (e.g., "哪裡最嚴重？") -> Agent 進行全局檢索 (Global Search)。

---

# Current Mock Implementation

The frontend currently uses a **mock agent service** (`frontend/src/features/spoon-os/services/agentService.ts`) for development and testing.

## Mock Response Patterns

### Pattern 1: Crisis Verification (Turkey)
**Trigger**: User input contains "turkey" or "quake"

**Response**:
```typescript
{
  message: "I verified the Turkey-Syria Earthquake data...",
  action_taken: "verify_crisis",
  recommendation: { action: "PROCEED", confidence: 95, ... },
  ui_hints: {
    mode: "DECISION",
    display_data: { title: "Turkey-Syria Earthquake", badge_text: "Verified Crisis", ... },
    actions: [
      { label: "Direct Donate (USDC)", type: "donate_direct", icon: "coins" },
      { label: "Yield Donate (4.5% APY)", type: "donate_yield", icon: "trending_up" }
    ]
  }
}
```

### Pattern 2: Multi-Step Proposal Creation (Morocco)

#### Step 1: Ask Vault Type
**Trigger**: Input contains "morocco" or "proposal"

**Response**:
```typescript
{
  message: "I see no active vaults for Morocco. To create a new Proposal, please select the Vault implementation type.",
  action_taken: "ask_vault_type",
  ui_hints: {
    mode: "DECISION",
    actions: [
      { label: "Yield Vault (Aave V3 Strategy)", type: "select_vault_yield", icon: "trending_up" },
      { label: "Direct Vault (Standard)", type: "select_vault_direct", icon: "wallet" }
    ]
  }
}
```

#### Step 2: Ready to Sign
**Trigger**: Input contains "yield" or "direct"

**Response**:
```typescript
{
  message: "I've prepared the transaction for a Yield Vault (4.5% APY). Please review and sign to deploy the Proposal.",
  action_taken: "create_proposal",
  ui_hints: {
    mode: "SIGNATURE",
    actions: [
      { label: "Sign & Deploy", type: "sign_proposal", icon: "pen-tool" }
    ]
  },
  transaction_payload: {
    to: "0xFactory...",
    data: "0xCreateProposal(Morocco, Yield)..."
  }
}
```

## Frontend Action Handling

The `page.tsx` component handles actions via `handleSpoonAction`:

```typescript
const handleSpoonAction = (action: string, data?: any) => {
  if (action === 'sign_proposal') {
    // Mock: Show alert simulating transaction signature
    alert('✅ Transaction signed! (Mock)');
  }
  else if (action === 'donate_direct' || action === 'donate_yield') {
    // Open donation modal
    setIsDonationOpen(true);
  }
};
```

## RPC Configuration

**Sepolia Testnet**:
- Endpoint: `https://1rpc.io/sepolia`
- Transport config: `{ batch: false }` (to avoid multicall issues with public RPCs)

**WalletConnect**:
- Project ID: Configured via environment variable or hardcoded
- Supported networks: Mainnet, Polygon, Optimism, Arbitrum, Base, Sepolia

---

# Future: Production Agent Integration
## 3. Agent 執行的邏輯 (Agent Logic)

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

---

## 5. 智能合約架構 (Smart Contract Architecture)

為了兼顧安全性與無需許可 (Permissionless) 的參與，GaiaLink 設計了雙層 Vault 機制。Agent 需根據此邏輯引導用戶。

### Layer 1: 機構主池 (Institution Vaults)
*   **權限**：僅限白名單機構 (Whitelisted Orgs) 創建。
*   **功能**：資金的最終接收方。
*   **類型**：支援 `Direct` (直接) 與 `Yield` (生息) 兩種模式。

### Layer 2: 用戶提案池 (User Proposals)
*   **權限**：無需許可 (Permissionless)，任何人都可創建。
*   **邏輯**：
    1.  用戶發起提案 (e.g., "為加薩建立醫療補給專案")，綁定一個 Layer 1 的機構地址。
    2.  設定 **募資目標 (Target Amount)**。
    3.  **達標 (Target Met)**：資金解鎖，自動流入 Layer 1 機構錢包。
    4.  **未達標 (Failed)**：資金退回原捐贈者 (Refund)。
*   **Agent 角色**：協助用戶檢查是否有現成提案，或協助發起新提案。

### 新增 Agent 意圖：創建提案 (CREATE_PROPOSAL)

當用戶說："我想發起一個為土耳其募款的活動"：

**Request:**
前端只需發送自然語言，Agent 負責從對話中提取 "土耳其" (Target Region) 和 "5000 USDC" (Amount)。

```json
{
  "message": "我想發起一個為土耳其賑災的提案，目標 5000 USDC"
}
```

**Response (Agent):**
```json
{
  "intent": "CREATE_PROPOSAL",
  "transaction_payload": {
    "to": "0xFactoryAddress...",
    "data": "0xCreateProposal(TurkeyRegion, 5000, USDC)",
    "description": "即將創建 'Turkey Relief Proposal'，目標 5000 USDC。若未達標將退款。"
  }
}
```
