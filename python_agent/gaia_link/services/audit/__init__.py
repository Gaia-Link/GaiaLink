"""
Audit Logging 服務

提供審計日誌記錄功能
"""

from gaia_link.services.audit.base import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditLevel,
    AuditQuery,
)
from gaia_link.services.audit.memory_audit import InMemoryAuditLogger

__all__ = [
    "AuditLogger",
    "AuditEntry",
    "AuditEventType",
    "AuditLevel",
    "AuditQuery",
    "InMemoryAuditLogger",
    "get_in_memory_audit_logger",
]


def get_in_memory_audit_logger(*args, **kwargs):
    """工廠函數：創建 InMemoryAuditLogger 實例"""
    return InMemoryAuditLogger(*args, **kwargs)
