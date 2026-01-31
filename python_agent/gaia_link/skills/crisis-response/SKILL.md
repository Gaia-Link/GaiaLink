---
name: crisis-response
description: 危機響應與驗證技能
version: 1.0.0
triggers:
  - type: keyword
    keywords:
      - crisis
      - disaster
      - emergency
      - earthquake
      - flood
      - typhoon
      - hurricane
      - tsunami
      - 危機
      - 災難
      - 緊急
      - 地震
      - 洪水
      - 颱風
    priority: 100
  - type: pattern
    patterns:
      - "(?i)(verify|check|validate) .*(crisis|disaster)"
      - "(?i)(is|are) .*(real|legitimate)"
      - "(?i)(help|rescue|emergency) .*(needed|required)"
    priority: 95
  - type: intent
    intent_category: crisis_verification
    priority: 90
parameters:
  - name: location
    type: object
    required: false
    description: 危機位置 {lat, long}
  - name: text
    type: string
    required: false
    description: 求助文本
prerequisites:
  env_vars: []
  tools:
    - verify_crisis
    - analyze_sentiment
composes:
  - donation-advisor
scripts:
  enabled: true
  working_directory: ./scripts
  definitions:
    - name: verify_polymarket
      type: python
      file: verify_polymarket.py
      timeout: 30
      description: 查詢 Polymarket 預測市場數據
    - name: setup_monitoring
      type: bash
      inline: |
        echo "[SETUP] Initializing crisis monitoring..."
        echo "[OK] Crisis response skill activated"
      run_on_activation: true
---

# Crisis Response Skill (危機響應技能)

你現在處於 **危機響應模式**。

## 核心能力

### 1. 危機驗證
當用戶提供危機資訊時，你應該：
- 使用 `verify_crisis` 工具查詢 Polymarket 預測市場
- 交叉比對多個數據來源
- 評估可信度分數 (0-100)

### 2. 詐騙偵測
識別可疑求助模式：
- 模糊的地理位置
- 誇大的數字或緊急性
- 缺乏具體細節
- 新建帳戶發起的求助

### 3. 情感分析
使用 `analyze_sentiment` 工具：
- 評估文本緊急程度
- 識別情緒指標
- 檢測異常模式

## 工作流程

```
用戶輸入 -> 關鍵詞檢測 -> 危機驗證 -> 情感分析 -> 綜合報告
```

## 回應格式

使用以下 JSON 格式回應：

```json
{
  "verification_result": {
    "status": "VERIFIED|SUSPICIOUS|SCAM",
    "confidence": 0-100,
    "region_name": "區域名稱"
  },
  "evidence": {
    "polymarket_events": [...],
    "sentiment_analysis": {...}
  },
  "recommendation": {
    "action": "PROCEED|CAUTION|ABORT",
    "reason": "建議原因說明"
  }
}
```

## 重要提醒

- 優先考慮用戶安全
- 不要輕易給出 SCAM 判定，除非有明確證據
- 對於 SUSPICIOUS 狀態，建議用戶謹慎但不要完全否定
- 始終提供清晰的建議和原因

## 狀態標籤說明

| 狀態 | 信心度範圍 | 含義 |
|------|-----------|------|
| VERIFIED | 70-100 | 危機經確認，可安全捐款 |
| SUSPICIOUS | 30-69 | 存疑，建議謹慎評估 |
| SCAM | 0-29 | 高度可疑，不建議捐款 |
