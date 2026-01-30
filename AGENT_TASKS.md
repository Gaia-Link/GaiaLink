# SpoonOS Agent Implementation Checklist

這份清單列出了 Python Agent 需要完成的關鍵開發項目，與 Frontend 和 Mock DB 進行對接。

## Phase 1: Frontend Agent Integration ✅ COMPLETE

### 1.1 Connect SpoonOSInterface to Mock Agent ✅
- [x] Implement `agentService.ts` with mock responses
- [x] Create `MockAgentResponses` for Turkey (verify) and Morocco (proposal)
- [x] Connect SpoonOSInterface to call `sendMessageToAgent`
- [x] Test UI mode transitions (LISTENING → PROCESSING → DECISION/SIGNATURE)

**Status**: ✅ Complete - SpoonOS successfully integrates with mock agent responses.

### 1.2 Implement Multi-Step Conversation Flow ✅
- [x] Modify `agentService.ts` to support 2-step proposal creation
  - Step 1: Ask for Vault Type (Yield vs Direct)
  - Step 2: Confirm & Sign transaction
- [x] Update UI to center SIGNATURE mode modal
- [x] Handle `select_vault_*` action types in SpoonOSInterface
- [x] Implement conversational handoff between steps

**Status**: ✅ Complete - Multi-step vault creation flow working.

### 1.3 Wire Up Action Handlers ✅
- [x] Implement `handleSpoonAction` in `page.tsx`
- [x] Handle `sign_proposal` action (mock signature)
- [x] Handle `donate_direct` and `donate_yield` actions
- [x] Connect actions to DonationModal

**Status**: ✅ Complete - All SpoonOS actions properly handled.

---

## Phase 2: RPC & Wallet Configuration ✅ RESOLVED

### 2.1 Wallet Connection Setup ✅
- [x] Configure WalletConnect Project ID
- [x] Add Sepolia testnet to supported chains
- [x] Install missing `@metamask/sdk` dependency
- [x] Configure explicit RPC transports for reliability

**Status**: ✅ Complete - Wallet connects successfully.

### 2.2 Balance Display Issue ⚠️ WORKAROUND
- [x] Debug "NaN ETH" balance display issue
- [x] Create `RpcTester` component to verify RPC connectivity
- [x] Identify root cause: RainbowKit/Wagmi version incompatibility
- [x] Apply workaround: `showBalance={false}` on ConnectButton
- [ ] Long-term fix: Upgrade to fully compatible versions (deferred)

**Status**: ⚠️ Resolved with workaround - Balance hidden, shown in RpcTester instead.

**RPC Configuration**:
- Sepolia: `https://1rpc.io/sepolia` with `batch: false`
- This ensures compatibility with public RPC rate limits

---

## Phase 3: Python Agent Backend (Next Priority)

### 3.1 Setup FastAPI Server
- [ ] Create `python_agent/main.py` with FastAPI app
- [ ] Add `/chat` endpoint for agent messages
- [ ] Configure CORS for frontend communication
- [ ] Add health check endpoint

### 3.2 DB Integration
- [ ] **整合 `db_service.py`**:
    - Agent 初始化時載入 `MockDatabaseService`。
    - 確保 Agent 可以呼叫 `db.search_crises(query)` 來獲取 `data.json` 中的資訊。

### 3.3 Implement Agent Tools
Agent 需要透過 Tool 來執行具體邏輯。

### A. `VerifyCrisisTool` (核心查詢)
- [ ] **Logic**:
    - 接收 `query` (地點/事件名)。
    - 呼叫 `db_service.search_crises(query)`。
    - **Mock Verification**: 如果在 DB 找到，直接回傳 DB 裡的 `verification` 欄位 (不再真去打 Polymarket API，為了 Demo 穩定性)。
    - 如果 DB 沒找到，回傳 "Unknown event"。

### B. `ExecuteDonationTool` (捐款交易)
- [ ] **Logic**:
    - 接收 `amount`, `token` (USDC/USDT), `vault_address` (從 DB 獲取)。
    - 判斷是 `DIRECT` 還是 `YIELD`。
    - **Output**: 回傳 `transaction_payload` JSON，讓前端去喚起錢包。

### C. `CreateProposalTool` (新增提案 - Layer 2)
- [ ] **Logic**:
    - 接收 `target_region`, `target_amount`.
    - **In-Memory Write**: 呼叫 `db_service.create_proposal(...)`。
    - **Output**: 回傳成功訊息，並提示前端 "已建立提案，請簽名確認"。

## 4. 智能對話與狀態機 (Brain & Workflow)
- [ ] **System Prompt 優化**:
    - 教導 Agent 根據搜尋結果，決定是要進入 `Verify Mode` (紅/綠燈卡片) 還是 `Action Mode` (捐款按鈕)。
    - 確保 Agent 的回傳格式符合 `AGENT_API.md` 定義的 JSON Interface (`ui_hints`, `recommendation`).

## 5. 測試驗證 (Verification)
- [ ] **情境測試**:
    - User: "Turkey earthquake news?" -> Agent 查 DB -> 回傳 Turkey 資料 + 顯示 Donate 按鈕。
    - User: "Create a proposal for Morocco." -> 
        1. Agent 回傳 `transaction_payload` (模擬調用 L2 Factory 合約)。
        2. Agent 同步執行 `db_write` (樂觀寫入 In-Memory DB)。
        3. User 簽名後，再問 "Morocco status?" -> Agent 答 "Active Proposal Found"。
