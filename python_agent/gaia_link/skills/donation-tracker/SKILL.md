---
name: donation-tracker
description: 捐款追蹤與狀態查詢技能
version: 1.0.0
triggers:
  - type: keyword
    keywords:
      - track
      - status
      - history
      - transaction
      - 追蹤
      - 狀態
      - 歷史
      - 交易
    priority: 80
  - type: pattern
    patterns:
      - "(?i)(check|view|get) .*(donation|transaction|status)"
      - "(?i)(my|our) .*(donations|history)"
    priority: 75
parameters:
  - name: transaction_id
    type: string
    required: false
    description: 交易 ID 或哈希
  - name: wallet_address
    type: string
    required: false
    description: 錢包地址
prerequisites:
  skills:
    - donation-advisor
scripts:
  enabled: true
  working_directory: ./scripts
  definitions:
    - name: track_donation
      type: python
      file: track_donation.py
      timeout: 15
      description: 追蹤捐款交易狀態或查詢歷史
---

# Donation Tracker Skill (捐款追蹤技能)

你現在處於 **捐款追蹤模式**。

## 核心能力

### 1. 交易追蹤
當用戶提供交易哈希時，你可以：
- 查詢交易狀態 (pending/confirmed/failed)
- 獲取區塊確認數
- 提供區塊鏈瀏覽器連結

### 2. 歷史查詢
當用戶提供錢包地址時，你可以：
- 列出所有捐款記錄
- 按時間範圍篩選
- 統計總捐款金額

### 3. 狀態報告
提供捐款活動的綜合報告：
- 總捐款次數
- 總捐款金額 (USD)
- 平均捐款金額
- 最近捐款時間

## 工作流程

```
用戶輸入 -> 參數解析 -> 追蹤/查詢 -> 格式化結果 -> 回應
```

## 輸入格式

### 追蹤單筆交易
```json
{
  "tx_hash": "0x..."
}
```

### 查詢捐款歷史
```json
{
  "wallet_address": "0x...",
  "time_range": "30d"  // 可選，默認 all
}
```

## 輸出格式

### 交易追蹤結果
```json
{
  "success": true,
  "transaction": {
    "tx_hash": "0x...",
    "status": "confirmed",
    "block_number": 12345678,
    "timestamp": "2024-01-15T10:30:00Z",
    "amount": 100,
    "token": "USDC",
    "recipient": "0x...",
    "gas_used": 21000
  },
  "explorer_url": "https://etherscan.io/tx/0x..."
}
```

### 歷史查詢結果
```json
{
  "success": true,
  "donations": [
    {
      "tx_hash": "0x...",
      "timestamp": "2024-01-15T10:30:00Z",
      "amount": 100,
      "token": "USDC",
      "recipient": "Red Cross",
      "status": "confirmed"
    }
  ],
  "summary": {
    "total_donations": 5,
    "total_amount_usd": 500.00,
    "average_amount_usd": 100.00,
    "first_donation": "2024-01-01T00:00:00Z",
    "last_donation": "2024-01-15T10:30:00Z"
  }
}
```

## 時間範圍格式

| 格式 | 含義 |
|------|------|
| `7d` | 過去 7 天 |
| `30d` | 過去 30 天 |
| `90d` | 過去 90 天 |
| `1y` | 過去 1 年 |
| `all` | 所有記錄 |

## 錯誤處理

| 錯誤類型 | 處理方式 |
|----------|----------|
| 無效交易哈希 | 返回錯誤提示，說明正確格式 |
| 無效錢包地址 | 返回錯誤提示，說明正確格式 |
| 交易未找到 | 返回 pending 狀態，建議稍後重試 |
| 無捐款記錄 | 返回空列表，說明無歷史記錄 |

## 重要提醒

- 交易狀態可能延遲更新，建議等待區塊確認
- 歷史記錄僅包含通過 GaiaLink 執行的捐款
- 大額交易可能需要更多區塊確認
