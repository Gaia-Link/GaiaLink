# Gaia Link - SpoonOS AI Agent 專案

## 強制要求

### SpoonOS 最低技術使用要求 (Hackathon)

為符合 SpoonOS 相關獎金發放條件，本專案**必須**滿足以下要求：

1. **必須基於 SpoonOS 構建**
   - 專案需實際集成並使用 SpoonOS 作為核心系統、運行環境或關鍵能力層
   - 不接受僅概念性提及或未實際調用 SpoonOS 的項目

2. **必須使用以下 Agent 體系之一**
   - ✅ **React Agent**（用於任務執行、交互式決策或流程編排）
   - Graph Agent（用於多節點關係建模、狀態流轉或複雜推理結構）

3. **Agent 使用需與項目核心功能強相關**
   - Agent 需在項目中承擔實際功能角色
   - 不接受僅做 Demo 展示或邊緣調用的形式化使用

## 專案角色定位

本專案負責 **Role 2: AI Engineer (SpoonOS Agent 邏輯)**：

### 目標
讓 Agent 顯得「聰明」且「有用」

### 必須完成的任務

1. **Prompt Engineering**
   - 定義 Agent 的角色（人道救援分析師）
   - 審計師 (Auditor) 角色
   - 支付官 (Payer) 角色

2. **Tool Construction** - 三個核心工具
   - `verify_crisis(lat, long)`: 查 Polymarket 數據比對
   - `analyze_sentiment(text)`: 分析貼文是否緊急
   - `execute_donation(amount, token)`: 模擬支付

3. **Output Formatting**
   - 確保 Agent 回傳的數據前端好渲染（JSON 格式）

## 技術棧

- **語言**: Python 3.10+
- **Agent 框架**: SpoonOS SDK (spoon-core)
- **Agent 類型**: SpoonReactAI (React Agent)
- **工具基類**: BaseTool

## SpoonOS 官方資源

- GitHub: [XSpoonAi/spoon-core](https://github.com/XSpoonAi/spoon-core)
- GitHub: [XSpoonAi/spoon-toolkit](https://github.com/XSpoonAi/spoon-toolkit)
- GitHub: [XSpoonAi/spoon-starter](https://github.com/XSpoonAi/spoon-starter)

## 開發規範

- 所有 Agent 邏輯必須使用 `spoon-core` SDK
- 工具必須繼承 `BaseTool` 類別
- Agent 必須使用 `SpoonReactAI` 類別
- 測試覆蓋率目標: 80%+
