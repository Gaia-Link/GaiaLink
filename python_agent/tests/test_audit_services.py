"""
Audit Logging 服務單元測試

測試 AuditLogger 抽象基類和 InMemoryAuditLogger 實作
"""

from datetime import datetime, timedelta

import pytest

from gaia_link.services.audit import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    AuditLevel,
    AuditQuery,
)


class TestAuditEventType:
    """AuditEventType 枚舉測試"""

    def test_tool_call_value(self):
        """TOOL_CALL 應有正確的值"""
        assert AuditEventType.TOOL_CALL.value == "TOOL_CALL"

    def test_tool_success_value(self):
        """TOOL_SUCCESS 應有正確的值"""
        assert AuditEventType.TOOL_SUCCESS.value == "TOOL_SUCCESS"

    def test_tool_error_value(self):
        """TOOL_ERROR 應有正確的值"""
        assert AuditEventType.TOOL_ERROR.value == "TOOL_ERROR"

    def test_rate_limited_value(self):
        """RATE_LIMITED 應有正確的值"""
        assert AuditEventType.RATE_LIMITED.value == "RATE_LIMITED"


class TestAuditLevel:
    """AuditLevel 枚舉測試"""

    def test_all_levels_exist(self):
        """所有級別應存在"""
        assert AuditLevel.DEBUG.value == "DEBUG"
        assert AuditLevel.INFO.value == "INFO"
        assert AuditLevel.WARNING.value == "WARNING"
        assert AuditLevel.ERROR.value == "ERROR"
        assert AuditLevel.CRITICAL.value == "CRITICAL"


class TestAuditEntry:
    """AuditEntry 資料類測試"""

    def test_create_basic_entry(self):
        """應能建立基本條目"""
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            tool_name="verify_crisis",
        )
        assert entry.event_type == AuditEventType.TOOL_CALL
        assert entry.tool_name == "verify_crisis"
        assert entry.entry_id is not None

    def test_create_full_entry(self):
        """應能建立完整條目"""
        now = datetime.utcnow()
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_SUCCESS,
            timestamp=now,
            tool_name="execute_donation",
            user_id="user_123",
            session_id="session_456",
            parameters={"amount": 100, "token": "USDC"},
            result={"success": True, "tx_id": "0x123"},
            duration_ms=150.5,
            level=AuditLevel.INFO,
            metadata={"network": "sepolia"},
        )
        assert entry.event_type == AuditEventType.TOOL_SUCCESS
        assert entry.user_id == "user_123"
        assert entry.parameters["amount"] == 100
        assert entry.result["success"] is True
        assert entry.duration_ms == 150.5

    def test_to_dict(self):
        """to_dict 應返回正確的字典"""
        now = datetime.utcnow()
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=now,
            tool_name="analyze_sentiment",
            parameters={"text": "help!"},
        )
        result = entry.to_dict()

        assert result["event_type"] == "TOOL_CALL"
        assert result["timestamp"] == now.isoformat()
        assert result["tool_name"] == "analyze_sentiment"
        assert result["parameters"]["text"] == "help!"
        assert result["entry_id"] == entry.entry_id

    def test_from_dict(self):
        """from_dict 應能從字典建立"""
        now = datetime.utcnow()
        data = {
            "entry_id": "test-id-123",
            "event_type": "TOOL_ERROR",
            "timestamp": now.isoformat(),
            "tool_name": "verify_crisis",
            "error": "Connection timeout",
            "level": "ERROR",
        }
        entry = AuditEntry.from_dict(data)

        assert entry.entry_id == "test-id-123"
        assert entry.event_type == AuditEventType.TOOL_ERROR
        assert entry.tool_name == "verify_crisis"
        assert entry.error == "Connection timeout"
        assert entry.level == AuditLevel.ERROR

    def test_entry_has_unique_id(self):
        """每個條目應有唯一 ID"""
        entry1 = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
        )
        entry2 = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
        )
        assert entry1.entry_id != entry2.entry_id


class TestAuditQuery:
    """AuditQuery 資料類測試"""

    def test_default_query(self):
        """預設查詢應有正確的值"""
        query = AuditQuery()
        assert query.limit == 100
        assert query.offset == 0
        assert query.start_time is None
        assert query.end_time is None

    def test_custom_query(self):
        """自定義查詢應正確"""
        now = datetime.utcnow()
        query = AuditQuery(
            start_time=now - timedelta(hours=1),
            end_time=now,
            event_types=[AuditEventType.TOOL_CALL, AuditEventType.TOOL_SUCCESS],
            tool_names=["verify_crisis"],
            user_id="user_123",
            limit=50,
            offset=10,
        )
        assert query.start_time is not None
        assert len(query.event_types) == 2
        assert query.tool_names == ["verify_crisis"]
        assert query.limit == 50


class TestInMemoryAuditLogger:
    """InMemoryAuditLogger 實作測試"""

    @pytest.fixture
    def logger(self):
        """建立 logger 實例"""
        from gaia_link.services.audit.memory_audit import InMemoryAuditLogger

        return InMemoryAuditLogger()

    def test_service_name(self, logger):
        """應有正確的服務名稱"""
        assert logger.service_name == "in_memory_audit_logger"

    @pytest.mark.asyncio
    async def test_log_entry(self, logger):
        """應能記錄條目"""
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            tool_name="verify_crisis",
        )
        entry_id = await logger.log(entry)

        assert entry_id == entry.entry_id

    @pytest.mark.asyncio
    async def test_get_by_id(self, logger):
        """應能根據 ID 獲取條目"""
        entry = AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            tool_name="analyze_sentiment",
        )
        await logger.log(entry)

        retrieved = await logger.get_by_id(entry.entry_id)
        assert retrieved is not None
        assert retrieved.tool_name == "analyze_sentiment"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, logger):
        """不存在的 ID 應返回 None"""
        retrieved = await logger.get_by_id("nonexistent-id")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_query_all(self, logger):
        """應能查詢所有條目"""
        # 記錄多個條目
        for i in range(5):
            entry = AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.utcnow(),
                tool_name=f"tool_{i}",
            )
            await logger.log(entry)

        results = await logger.query(AuditQuery())
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_query_by_event_type(self, logger):
        """應能按事件類型查詢"""
        # 記錄不同類型的條目
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.utcnow(),
                tool_name="tool_1",
            )
        )
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_SUCCESS,
                timestamp=datetime.utcnow(),
                tool_name="tool_1",
            )
        )
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_ERROR,
                timestamp=datetime.utcnow(),
                tool_name="tool_2",
            )
        )

        query = AuditQuery(event_types=[AuditEventType.TOOL_CALL])
        results = await logger.query(query)
        assert len(results) == 1
        assert results[0].event_type == AuditEventType.TOOL_CALL

    @pytest.mark.asyncio
    async def test_query_by_tool_name(self, logger):
        """應能按工具名稱查詢"""
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.utcnow(),
                tool_name="verify_crisis",
            )
        )
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.utcnow(),
                tool_name="execute_donation",
            )
        )

        query = AuditQuery(tool_names=["verify_crisis"])
        results = await logger.query(query)
        assert len(results) == 1
        assert results[0].tool_name == "verify_crisis"

    @pytest.mark.asyncio
    async def test_query_by_user_id(self, logger):
        """應能按用戶 ID 查詢"""
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.utcnow(),
                user_id="user_1",
            )
        )
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=datetime.utcnow(),
                user_id="user_2",
            )
        )

        query = AuditQuery(user_id="user_1")
        results = await logger.query(query)
        assert len(results) == 1
        assert results[0].user_id == "user_1"

    @pytest.mark.asyncio
    async def test_query_by_time_range(self, logger):
        """應能按時間範圍查詢"""
        now = datetime.utcnow()
        old_time = now - timedelta(hours=2)
        recent_time = now - timedelta(minutes=30)

        # 舊條目
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=old_time,
                tool_name="old_tool",
            )
        )
        # 新條目
        await logger.log(
            AuditEntry(
                event_type=AuditEventType.TOOL_CALL,
                timestamp=recent_time,
                tool_name="recent_tool",
            )
        )

        query = AuditQuery(start_time=now - timedelta(hours=1))
        results = await logger.query(query)
        assert len(results) == 1
        assert results[0].tool_name == "recent_tool"

    @pytest.mark.asyncio
    async def test_query_with_limit(self, logger):
        """應能限制返回數量"""
        for i in range(10):
            await logger.log(
                AuditEntry(
                    event_type=AuditEventType.TOOL_CALL,
                    timestamp=datetime.utcnow(),
                    tool_name=f"tool_{i}",
                )
            )

        query = AuditQuery(limit=5)
        results = await logger.query(query)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_query_with_offset(self, logger):
        """應能跳過指定數量"""
        for i in range(10):
            await logger.log(
                AuditEntry(
                    event_type=AuditEventType.TOOL_CALL,
                    timestamp=datetime.utcnow(),
                    tool_name=f"tool_{i}",
                )
            )

        query = AuditQuery(limit=5, offset=5)
        results = await logger.query(query)
        assert len(results) == 5


class TestAuditLoggerConvenienceMethods:
    """AuditLogger 便利方法測試"""

    @pytest.fixture
    def logger(self):
        """建立 logger 實例"""
        from gaia_link.services.audit.memory_audit import InMemoryAuditLogger

        return InMemoryAuditLogger()

    @pytest.mark.asyncio
    async def test_log_tool_call(self, logger):
        """log_tool_call 應記錄工具調用"""
        entry_id = await logger.log_tool_call(
            tool_name="verify_crisis",
            parameters={"lat": 37.5, "long": 36.9},
            user_id="user_123",
        )

        entry = await logger.get_by_id(entry_id)
        assert entry is not None
        assert entry.event_type == AuditEventType.TOOL_CALL
        assert entry.tool_name == "verify_crisis"
        assert entry.parameters["lat"] == 37.5
        assert entry.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_log_tool_success(self, logger):
        """log_tool_success 應記錄成功執行"""
        entry_id = await logger.log_tool_success(
            tool_name="execute_donation",
            parameters={"amount": 100, "token": "USDC"},
            result={"success": True, "tx_id": "0x123"},
            duration_ms=250.5,
            user_id="user_123",
        )

        entry = await logger.get_by_id(entry_id)
        assert entry is not None
        assert entry.event_type == AuditEventType.TOOL_SUCCESS
        assert entry.result["tx_id"] == "0x123"
        assert entry.duration_ms == 250.5
        assert entry.level == AuditLevel.INFO

    @pytest.mark.asyncio
    async def test_log_tool_error(self, logger):
        """log_tool_error 應記錄錯誤"""
        entry_id = await logger.log_tool_error(
            tool_name="verify_crisis",
            parameters={"lat": 999, "long": 999},
            error="Invalid coordinates",
            duration_ms=10.0,
        )

        entry = await logger.get_by_id(entry_id)
        assert entry is not None
        assert entry.event_type == AuditEventType.TOOL_ERROR
        assert entry.error == "Invalid coordinates"
        assert entry.level == AuditLevel.ERROR

    @pytest.mark.asyncio
    async def test_log_rate_limited(self, logger):
        """log_rate_limited 應記錄速率限制"""
        entry_id = await logger.log_rate_limited(
            tool_name="execute_donation",
            user_id="user_123",
            retry_after=30.0,
        )

        entry = await logger.get_by_id(entry_id)
        assert entry is not None
        assert entry.event_type == AuditEventType.RATE_LIMITED
        assert entry.level == AuditLevel.WARNING
        assert entry.metadata["retry_after"] == 30.0


class TestAuditLoggerFactory:
    """Audit Logger 工廠函數測試"""

    def test_get_in_memory_audit_logger(self):
        """應能通過工廠創建 InMemoryAuditLogger"""
        from gaia_link.services.audit import get_in_memory_audit_logger

        logger = get_in_memory_audit_logger()
        assert logger.service_name == "in_memory_audit_logger"
