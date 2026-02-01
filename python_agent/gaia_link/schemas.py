"""
Gaia Link Agent 數據模型定義

定義所有工具的輸入輸出結構
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# ======================== 驗證危機工具 (verify_crisis) ========================

class PolymarketEvent(BaseModel):
    """Polymarket 預測市場事件"""
    event_id: str = Field(description="事件 ID")
    title: str = Field(description="事件標題")
    probability: float = Field(ge=0, le=1, description="事件發生機率 (0-1)")
    volume: float = Field(ge=0, description="交易量 (USD)")
    source_url: Optional[str] = Field(default=None, description="來源連結")


class VerifyCrisisInput(BaseModel):
    """verify_crisis 工具輸入"""
    lat: float = Field(ge=-90, le=90, description="緯度")
    long: float = Field(ge=-180, le=180, description="經度")


class VerifyCrisisOutput(BaseModel):
    """verify_crisis 工具輸出"""
    status: str = Field(description="驗證狀態: VERIFIED, SUSPICIOUS, SCAM")
    confidence: int = Field(ge=0, le=100, description="可信度分數 (0-100)")
    polymarket_events: list[PolymarketEvent] = Field(
        default_factory=list, description="相關的 Polymarket 事件"
    )
    risk_factors: list[str] = Field(default_factory=list, description="風險因素列表")
    recommendation: str = Field(description="建議說明")


# ======================== 情感分析工具 (analyze_sentiment) ========================

class SentimentContext(BaseModel):
    """情感分析上下文"""
    post_id: Optional[str] = Field(default=None, description="貼文 ID")
    author_history: Optional[int] = Field(default=None, description="作者歷史貼文數")
    account_age_days: Optional[int] = Field(default=None, description="帳號年齡（天）")


class AnalyzeSentimentInput(BaseModel):
    """analyze_sentiment 工具輸入"""
    text: str = Field(min_length=1, description="待分析的文本內容")
    context: Optional[SentimentContext] = Field(default=None, description="額外上下文")


class AnalyzeSentimentOutput(BaseModel):
    """analyze_sentiment 工具輸出"""
    urgency_level: str = Field(description="緊急程度: CRITICAL, HIGH, MEDIUM, LOW")
    authenticity_score: int = Field(ge=0, le=100, description="真實性分數 (0-100)")
    emotional_indicators: list[str] = Field(default_factory=list, description="情緒指標")
    red_flags: list[str] = Field(default_factory=list, description="可疑標記")
    summary: str = Field(description="分析摘要")


# ======================== 執行捐款工具 (execute_donation) ========================

class ExecuteDonationInput(BaseModel):
    """execute_donation 工具輸入"""
    amount: float = Field(gt=0, description="捐款金額")
    token: str = Field(description="代幣類型: USDC, USDT, ETH, DAI")
    recipient_address: str = Field(min_length=1, description="接收者地址")


class DonationDetails(BaseModel):
    """捐款交易詳情"""
    amount_sent: float = Field(description="發送金額")
    token: str = Field(description="代幣類型")
    gas_fee: float = Field(description="Gas 費用 (ETH)")
    total_cost_usd: float = Field(description="總成本 (USD)")


class ExecuteDonationOutput(BaseModel):
    """execute_donation 工具輸出"""
    success: bool = Field(description="交易是否成功")
    transaction_id: Optional[str] = Field(default=None, description="交易 ID")
    status: str = Field(description="交易狀態")
    details: Optional[DonationDetails] = Field(default=None, description="交易詳情")
    explorer_url: Optional[str] = Field(default=None, description="區塊鏈瀏覽器連結")
    error: Optional[str] = Field(default=None, description="錯誤訊息")


# ======================== Agent 回應格式 ========================

class Recommendation(BaseModel):
    """Agent 建議"""
    action: str = Field(description="建議動作: PROCEED, CAUTION, ABORT")
    confidence: int = Field(ge=0, le=100, description="信心分數")
    reason: str = Field(description="建議原因")


class UIBadge(BaseModel):
    """UI 徽章提示"""
    type: str = Field(description="徽章類型")
    text: str = Field(description="顯示文字")
    color: str = Field(description="顯示顏色")


class UIToast(BaseModel):
    """UI Toast 提示"""
    type: str = Field(description="提示類型: success, warning, error, info")
    title: str = Field(description="標題")
    message: str = Field(description="訊息內容")
    duration_ms: int = Field(default=5000, description="顯示時長（毫秒）")


class UIModal(BaseModel):
    """UI Modal 彈窗"""
    show: bool = Field(default=False, description="是否顯示")
    title: str = Field(description="標題")
    content: str = Field(description="內容")
    actions: list[dict] = Field(default_factory=list, description="操作按鈕")


class UIHints(BaseModel):
    """UI 提示集合"""
    badge: Optional[UIBadge] = Field(default=None, description="徽章提示")
    toast: Optional[UIToast] = Field(default=None, description="Toast 提示")
    modal: Optional[UIModal] = Field(default=None, description="Modal 彈窗")


class ToolResult(BaseModel):
    """單個工具執行結果"""
    tool_name: str = Field(description="工具名稱")
    status: str = Field(description="執行狀態: success, error")
    data: dict = Field(default_factory=dict, description="執行結果數據")
    execution_time_ms: int = Field(description="執行時間（毫秒）")


class AgentResponse(BaseModel):
    """Agent 標準回應格式 (前端友好的 JSON 結構)"""
    message: str = Field(description="回應訊息")
    action_taken: str = Field(description="執行的動作")
    tool_results: list[ToolResult] = Field(default_factory=list, description="工具執行結果")
    recommendation: Recommendation = Field(description="建議")
    ui_hints: UIHints = Field(default_factory=UIHints, description="UI 提示")

class ChatResponse(BaseModel):
    """Standardized Chat Response for Frontend (Source of Truth)"""
    message: str
    action_taken: str
    ui_hints: Dict[str, Any]
    transaction_payload: Optional[Dict[str, Any]] = None
    transaction_sequence: Optional[list[Dict[str, Any]]] = None
