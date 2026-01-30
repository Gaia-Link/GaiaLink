"""
Audit Logging 服務抽象基類

提供審計日誌的抽象介面，支援 InMemory 和 File 實作切換
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class AuditEventType(str, Enum):
    """審計事件類型"""

    TOOL_CALL = "TOOL_CALL"
    TOOL_SUCCESS = "TOOL_SUCCESS"
    TOOL_ERROR = "TOOL_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"


class AuditLevel(str, Enum):
    """審計日誌級別"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEntry:
    """審計日誌條目"""

    event_type: AuditEventType
    timestamp: datetime
    tool_name: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parameters: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    level: AuditLevel = AuditLevel.INFO
    metadata: dict = field(default_factory=dict)
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tool_name": self.tool_name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "level": self.level.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        """從字典建立"""
        return cls(
            entry_id=data.get("entry_id", str(uuid.uuid4())),
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tool_name=data.get("tool_name"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            parameters=data.get("parameters"),
            result=data.get("result"),
            error=data.get("error"),
            duration_ms=data.get("duration_ms"),
            level=AuditLevel(data.get("level", "INFO")),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AuditQuery:
    """審計日誌查詢條件"""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[list[AuditEventType]] = None
    tool_names: Optional[list[str]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    level: Optional[AuditLevel] = None
    limit: int = 100
    offset: int = 0


class AuditLogger(ABC):
    """
    Audit Logger 抽象基類

    記錄所有工具調用和系統事件
    """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """服務名稱"""
        pass

    @abstractmethod
    async def log(self, entry: AuditEntry) -> str:
        """
        記錄審計條目

        Args:
            entry: 審計條目

        Returns:
            str: 條目 ID
        """
        pass

    @abstractmethod
    async def query(self, query: AuditQuery) -> list[AuditEntry]:
        """
        查詢審計日誌

        Args:
            query: 查詢條件

        Returns:
            list[AuditEntry]: 符合條件的條目
        """
        pass

    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[AuditEntry]:
        """
        根據 ID 獲取條目

        Args:
            entry_id: 條目 ID

        Returns:
            Optional[AuditEntry]: 條目或 None
        """
        pass

    async def log_tool_call(
        self,
        tool_name: str,
        parameters: dict,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        記錄工具調用

        Args:
            tool_name: 工具名稱
            parameters: 調用參數
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據

        Returns:
            str: 條目 ID
        """
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            parameters=parameters,
            user_id=user_id,
            session_id=session_id,
            level=AuditLevel.INFO,
            metadata=metadata or {},
        )
        return await self.log(entry)

    async def log_tool_success(
        self,
        tool_name: str,
        parameters: dict,
        result: dict,
        duration_ms: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        記錄工具成功執行

        Args:
            tool_name: 工具名稱
            parameters: 調用參數
            result: 執行結果
            duration_ms: 執行時間（毫秒）
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據

        Returns:
            str: 條目 ID
        """
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_SUCCESS,
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            duration_ms=duration_ms,
            user_id=user_id,
            session_id=session_id,
            level=AuditLevel.INFO,
            metadata=metadata or {},
        )
        return await self.log(entry)

    async def log_tool_error(
        self,
        tool_name: str,
        parameters: dict,
        error: str,
        duration_ms: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        記錄工具執行錯誤

        Args:
            tool_name: 工具名稱
            parameters: 調用參數
            error: 錯誤訊息
            duration_ms: 執行時間（毫秒）
            user_id: 用戶 ID
            session_id: 會話 ID
            metadata: 額外元數據

        Returns:
            str: 條目 ID
        """
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_ERROR,
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            parameters=parameters,
            error=error,
            duration_ms=duration_ms,
            user_id=user_id,
            session_id=session_id,
            level=AuditLevel.ERROR,
            metadata=metadata or {},
        )
        return await self.log(entry)

    async def log_rate_limited(
        self,
        tool_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        retry_after: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        記錄速率限制事件

        Args:
            tool_name: 工具名稱
            user_id: 用戶 ID
            session_id: 會話 ID
            retry_after: 重試等待時間（秒）
            metadata: 額外元數據

        Returns:
            str: 條目 ID
        """
        entry = AuditEntry(
            event_type=AuditEventType.RATE_LIMITED,
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            user_id=user_id,
            session_id=session_id,
            level=AuditLevel.WARNING,
            metadata={**(metadata or {}), "retry_after": retry_after},
        )
        return await self.log(entry)
