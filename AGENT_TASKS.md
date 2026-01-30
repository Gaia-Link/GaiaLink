# SpoonOS Agent Implementation Checklist

這份清單列出了 Python Agent 需要完成的關鍵開發項目，與 Frontend 和 Mock DB 進行對接。

## 1. 服務端架構 (Server Setup)
- [ ] **建立 FastAPI Server**:
    - 需要一個 `server.py` 作為入口。
    - 實作 `POST /api/agent/chat` 接口，接收 `{ message: str, context?: object }`。
    - 設定 CORS 以允許前端 (localhost:3000) 呼叫。

## 2. 數據庫整合 (DB Integration)
- [ ] **整合 `db_service.py`**:
    - Agent 初始化時載入 `MockDatabaseService`。
    - 確保 Agent 可以呼叫 `db.search_crises(query)` 來獲取 `data.json` 中的資訊。

## 3. 工具實作 (Agent Tools)
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
