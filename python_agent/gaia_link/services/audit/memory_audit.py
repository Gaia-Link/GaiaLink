"""
InMemory Audit Logger 實作

內存審計日誌實作，適用於測試和開發環境
"""

from typing import Optional

from gaia_link.services.audit.base import (
    AuditLogger,
    AuditEntry,
    AuditQuery,
)


class InMemoryAuditLogger(AuditLogger):
    """
    內存 Audit Logger 實作

    將審計日誌存儲在內存中，適用於測試和開發環境
    """

    def __init__(self, max_entries: int = 10000):
        """
        初始化 Audit Logger

        Args:
            max_entries: 最大存儲條目數
        """
        self._entries: dict[str, AuditEntry] = {}
        self._entries_list: list[str] = []  # 按時間順序存儲 entry_id
        self._max_entries = max_entries

    @property
    def service_name(self) -> str:
        """服務名稱"""
        return "in_memory_audit_logger"

    def _cleanup_if_needed(self) -> None:
        """如果超過最大條目數則清理舊條目"""
        while len(self._entries_list) > self._max_entries:
            old_id = self._entries_list.pop(0)
            del self._entries[old_id]

    async def log(self, entry: AuditEntry) -> str:
        """
        記錄審計條目

        Args:
            entry: 審計條目

        Returns:
            str: 條目 ID
        """
        self._entries[entry.entry_id] = entry
        self._entries_list.append(entry.entry_id)
        self._cleanup_if_needed()
        return entry.entry_id

    async def query(self, query: AuditQuery) -> list[AuditEntry]:
        """
        查詢審計日誌

        Args:
            query: 查詢條件

        Returns:
            list[AuditEntry]: 符合條件的條目
        """
        results: list[AuditEntry] = []

        for entry_id in self._entries_list:
            entry = self._entries[entry_id]

            # 按時間範圍過濾
            if query.start_time and entry.timestamp < query.start_time:
                continue
            if query.end_time and entry.timestamp > query.end_time:
                continue

            # 按事件類型過濾
            if query.event_types and entry.event_type not in query.event_types:
                continue

            # 按工具名稱過濾
            if query.tool_names and entry.tool_name not in query.tool_names:
                continue

            # 按用戶 ID 過濾
            if query.user_id and entry.user_id != query.user_id:
                continue

            # 按會話 ID 過濾
            if query.session_id and entry.session_id != query.session_id:
                continue

            # 按級別過濾
            if query.level and entry.level != query.level:
                continue

            results.append(entry)

        # 應用分頁
        start = query.offset
        end = query.offset + query.limit
        return results[start:end]

    async def get_by_id(self, entry_id: str) -> Optional[AuditEntry]:
        """
        根據 ID 獲取條目

        Args:
            entry_id: 條目 ID

        Returns:
            Optional[AuditEntry]: 條目或 None
        """
        return self._entries.get(entry_id)

    def clear(self) -> None:
        """清空所有條目"""
        self._entries.clear()
        self._entries_list.clear()

    def get_all(self) -> list[AuditEntry]:
        """獲取所有條目（同步方法，用於測試）"""
        return [self._entries[entry_id] for entry_id in self._entries_list]
