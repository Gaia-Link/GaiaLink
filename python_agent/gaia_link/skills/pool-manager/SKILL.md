---
name: pool-manager
description: 捐款池管理技能
version: 1.0.0
triggers:
  - type: keyword
    keywords:
      - pool
      - vault
      - treasury
      - allocation
      - balance
      - 資金池
      - 池子
      - 金庫
      - 餘額
      - 分配
    priority: 70
  - type: pattern
    patterns:
      - "(?i)(manage|check|view|create) .*(pool|vault)"
      - "(?i)(pool|vault) .*(status|balance|allocation)"
      - "(?i)how much .*(in|left|remaining)"
    priority: 65
  - type: intent
    intent_category: pool_management
    priority: 60
parameters:
  - name: pool_id
    type: string
    required: false
    description: 資金池 ID
  - name: action
    type: string
    required: false
    description: 操作類型 (query, create, deposit, withdraw)
  - name: vault_type
    type: string
    required: false
    description: 池子類型 (direct, yield)
prerequisites:
  skills:
    - crisis-response
    - donation-advisor
scripts:
  enabled: true
  working_directory: ./scripts
  definitions:
    - name: analyze_pool
      type: python
      file: analyze_pool.py
      timeout: 20
      description: 分析資金池狀態和收益
---

# Pool Manager Skill (池子管理技能)

你現在處於 **池子管理模式**。

## 核心功能

### 1. 資金監控
- 追蹤多鏈資金餘額
- 監控池子收益率
- 生成資金報告

### 2. 池子類型

#### 直接捐贈池 (Direct Pool)
- 資金直接流向受益組織
- 無收益機制
- 適合即時救援

#### 無損捐贈池 (Yield Pool)
- 本金存入 Yield 協議 (如 Euler, Pendle)
- 利息捐給受益組織
- 本金可隨時取回
- 適合長期支持

### 3. 智能分配
- 根據危機優先級自動分配
- 優化跨鏈 Gas 成本
- 平衡風險與效率

## 工作流程

```
查詢請求 -> 池子狀態 -> 分析報告 -> 建議操作
```

## 池子結構

```
Vault
├── vault_id: 唯一標識
├── name: 池子名稱
├── vault_type: direct | yield
├── creator_type: organization | community
├── beneficiary_org_id: 受益組織 ID
├── target_amount: 目標金額
├── current_amount: 當前金額
├── yield_earned: 已產生收益
└── is_active: 是否活躍
```

## 回應格式

### 查詢池子狀態

```json
{
  "pool_status": {
    "vault_id": "vault_001",
    "name": "Turkey Earthquake Relief",
    "vault_type": "yield",
    "total_balance_usd": 50000,
    "yield_earned_usd": 1250,
    "target_progress": 0.65
  },
  "chain_breakdown": {
    "ethereum": 30000,
    "polygon": 15000,
    "optimism": 5000
  },
  "active_crises": [
    {"region": "Turkey", "priority": "HIGH"}
  ],
  "recommendations": [
    "Consider rebalancing to higher yield protocol"
  ]
}
```

### 創建新池子

```json
{
  "action": "create_vault",
  "vault": {
    "name": "New Crisis Pool",
    "vault_type": "direct",
    "creator_type": "community",
    "beneficiary_org_id": "org_redcross",
    "target_amount": 10000
  },
  "validation": {
    "org_whitelisted": true,
    "ready_to_create": true
  }
}
```

## 權限模型

### 機構池 (Organization Pool)
- 由白名單組織創建
- 直接控制資金流向
- 需要組織驗證

### 社群池 (Community Pool)
- 任何人可創建
- 必須指定白名單受益組織
- 資金只能流向受益組織

## 重要提醒

1. **白名單驗證** - 所有受益組織必須在白名單中
2. **資金安全** - 僅允許流向已驗證地址
3. **收益透明** - 清楚顯示收益來源和分配
4. **風險提示** - Yield 協議存在智能合約風險

## 支援的 Yield 協議

| 協議 | 預期 APY | 風險等級 |
|------|---------|---------|
| Euler | 3-5% | 中 |
| Pendle | 5-8% | 中高 |
| Aave | 2-4% | 低 |

## 錯誤處理

| 錯誤類型 | 處理方式 |
|----------|----------|
| 組織未白名單 | 拒絕創建，提示申請白名單 |
| 池子不存在 | 提示檢查 ID 或創建新池 |
| 餘額不足 | 顯示當前餘額，建議金額 |
| 協議風險 | 警告用戶，建議分散風險 |
