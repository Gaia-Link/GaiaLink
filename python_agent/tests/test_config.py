"""
配置管理單元測試
"""

import os
import pytest
from unittest.mock import patch

from gaia_link.config import (
    Settings,
    BlockchainNetwork,
    PolymarketMode,
    SentimentMode,
    get_settings,
    get_blockchain_service,
    get_polymarket_service,
    get_sentiment_service,
    get_rate_limiter,
    get_audit_logger,
)
from gaia_link.services import (
    MockBlockchainService,
    MockPolymarketService,
    MockSentimentService,
    InMemoryRateLimiter,
    InMemoryAuditLogger,
)


class TestBlockchainNetwork:
    """BlockchainNetwork 枚舉測試"""

    def test_mock_value(self):
        """MOCK 應有正確的值"""
        assert BlockchainNetwork.MOCK.value == "mock"

    def test_sepolia_value(self):
        """SEPOLIA 應有正確的值"""
        assert BlockchainNetwork.SEPOLIA.value == "sepolia"

    def test_mainnet_value(self):
        """MAINNET 應有正確的值"""
        assert BlockchainNetwork.MAINNET.value == "mainnet"


class TestSettings:
    """Settings 配置類測試"""

    def test_default_blockchain_network(self):
        """默認應使用 MOCK 網絡"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.blockchain_network == BlockchainNetwork.MOCK

    def test_default_log_level(self):
        """默認日誌級別應為 INFO"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.log_level == "INFO"

    def test_default_polymarket_api_url(self):
        """默認 Polymarket API URL"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "polymarket" in settings.polymarket_api_url.lower()

    def test_is_mock_true_for_mock_network(self):
        """is_mock 應在 MOCK 網絡時返回 True"""
        with patch.dict(os.environ, {"BLOCKCHAIN_NETWORK": "mock"}, clear=True):
            settings = Settings()
            assert settings.is_mock() is True
            assert settings.is_testnet() is False
            assert settings.is_production() is False

    def test_is_testnet_true_for_sepolia(self):
        """is_testnet 應在 SEPOLIA 網絡時返回 True"""
        with patch.dict(os.environ, {"BLOCKCHAIN_NETWORK": "sepolia"}, clear=True):
            settings = Settings()
            assert settings.is_testnet() is True
            assert settings.is_mock() is False

    def test_is_production_true_for_mainnet(self):
        """is_production 應在 MAINNET 網絡時返回 True"""
        with patch.dict(os.environ, {"BLOCKCHAIN_NETWORK": "mainnet"}, clear=True):
            settings = Settings()
            assert settings.is_production() is True
            assert settings.is_mock() is False

    def test_rate_limit_defaults(self):
        """Rate limiting 默認值"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.rate_limit_enabled is False
            assert settings.rate_limit_requests_per_minute == 60

    def test_audit_logging_default(self):
        """審計日誌默認關閉"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.audit_logging_enabled is False

    def test_env_override(self):
        """環境變數應能覆蓋默認值"""
        env = {
            "BLOCKCHAIN_NETWORK": "sepolia",
            "LOG_LEVEL": "DEBUG",
            "RATE_LIMIT_ENABLED": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.blockchain_network == BlockchainNetwork.SEPOLIA
            assert settings.log_level == "DEBUG"
            assert settings.rate_limit_enabled is True


class TestGetSettings:
    """get_settings 函數測試"""

    def test_returns_settings_instance(self):
        """應返回 Settings 實例"""
        # 清除緩存
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_returns_cached_instance(self):
        """應返回緩存的實例"""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestGetBlockchainService:
    """get_blockchain_service 函數測試"""

    def test_returns_mock_service_by_default(self):
        """默認應返回 MockBlockchainService"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"BLOCKCHAIN_NETWORK": "mock"}, clear=True):
            get_settings.cache_clear()
            service = get_blockchain_service()
            assert isinstance(service, MockBlockchainService)

    def test_raises_for_unsupported_network(self):
        """不支援的網絡應拋出錯誤"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"BLOCKCHAIN_NETWORK": "mainnet"}, clear=True):
            get_settings.cache_clear()
            with pytest.raises(NotImplementedError):
                get_blockchain_service()


class TestPolymarketMode:
    """PolymarketMode 枚舉測試"""

    def test_mock_value(self):
        """MOCK 應有正確的值"""
        assert PolymarketMode.MOCK.value == "mock"

    def test_real_value(self):
        """REAL 應有正確的值"""
        assert PolymarketMode.REAL.value == "real"


class TestPolymarketSettings:
    """Polymarket 配置測試"""

    def test_default_polymarket_mode(self):
        """明確設置 mock 模式應使用 MOCK 模式"""
        # 注意：Pydantic Settings 會讀取 .env 文件，所以我們需要明確設置環境變數
        with patch.dict(os.environ, {"POLYMARKET_MODE": "mock"}, clear=True):
            settings = Settings()
            assert settings.polymarket_mode == PolymarketMode.MOCK

    def test_default_polymarket_api_url(self):
        """默認 Polymarket API URL 應為 gamma-api"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "gamma-api.polymarket.com" in settings.polymarket_api_url

    def test_default_polymarket_timeout(self):
        """默認超時應為 30 秒"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.polymarket_timeout == 30

    def test_is_polymarket_mock(self):
        """is_polymarket_mock 應在 MOCK 模式時返回 True"""
        with patch.dict(os.environ, {"POLYMARKET_MODE": "mock"}, clear=True):
            settings = Settings()
            assert settings.is_polymarket_mock() is True
            assert settings.is_polymarket_real() is False

    def test_is_polymarket_real(self):
        """is_polymarket_real 應在 REAL 模式時返回 True"""
        with patch.dict(os.environ, {"POLYMARKET_MODE": "real"}, clear=True):
            settings = Settings()
            assert settings.is_polymarket_real() is True
            assert settings.is_polymarket_mock() is False

    def test_polymarket_env_override(self):
        """環境變數應能覆蓋 Polymarket 設置"""
        env = {
            "POLYMARKET_MODE": "real",
            "POLYMARKET_API_URL": "https://custom-api.example.com",
            "POLYMARKET_TIMEOUT": "60",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.polymarket_mode == PolymarketMode.REAL
            assert settings.polymarket_api_url == "https://custom-api.example.com"
            assert settings.polymarket_timeout == 60


class TestGetPolymarketService:
    """get_polymarket_service 函數測試"""

    def test_returns_mock_service_by_default(self):
        """默認應返回 MockPolymarketService"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"POLYMARKET_MODE": "mock"}, clear=True):
            get_settings.cache_clear()
            service = get_polymarket_service()
            assert isinstance(service, MockPolymarketService)

    def test_returns_mock_service_explicitly(self):
        """明確設置 mock 模式應返回 MockPolymarketService"""
        get_settings.cache_clear()
        env = {"POLYMARKET_MODE": "mock", "BLOCKCHAIN_NETWORK": "mock"}
        with patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            service = get_polymarket_service()
            assert isinstance(service, MockPolymarketService)
            assert service.service_name == "mock"


class TestSentimentMode:
    """SentimentMode 枚舉測試"""

    def test_mock_value(self):
        """MOCK 應有正確的值"""
        assert SentimentMode.MOCK.value == "mock"

    def test_huggingface_value(self):
        """HUGGINGFACE 應有正確的值"""
        assert SentimentMode.HUGGINGFACE.value == "huggingface"


class TestSentimentSettings:
    """Sentiment 配置測試"""

    def test_default_sentiment_mode(self):
        """明確設置 mock 模式應使用 MOCK 模式"""
        # 注意：Pydantic Settings 會讀取 .env 文件，所以我們需要明確設置環境變數
        with patch.dict(os.environ, {"SENTIMENT_MODE": "mock"}, clear=True):
            settings = Settings()
            assert settings.sentiment_mode == SentimentMode.MOCK

    def test_default_huggingface_model(self):
        """默認 HuggingFace 模型應為 distilbert"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "distilbert" in settings.huggingface_model

    def test_default_huggingface_device(self):
        """默認設備應為 cpu"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.huggingface_device == "cpu"

    def test_is_sentiment_mock(self):
        """is_sentiment_mock 應在 MOCK 模式時返回 True"""
        with patch.dict(os.environ, {"SENTIMENT_MODE": "mock"}, clear=True):
            settings = Settings()
            assert settings.is_sentiment_mock() is True
            assert settings.is_sentiment_huggingface() is False

    def test_is_sentiment_huggingface(self):
        """is_sentiment_huggingface 應在 HUGGINGFACE 模式時返回 True"""
        with patch.dict(os.environ, {"SENTIMENT_MODE": "huggingface"}, clear=True):
            settings = Settings()
            assert settings.is_sentiment_huggingface() is True
            assert settings.is_sentiment_mock() is False

    def test_sentiment_env_override(self):
        """環境變數應能覆蓋 Sentiment 設置"""
        env = {
            "SENTIMENT_MODE": "huggingface",
            "HUGGINGFACE_MODEL": "bert-base-uncased",
            "HUGGINGFACE_DEVICE": "cuda",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.sentiment_mode == SentimentMode.HUGGINGFACE
            assert settings.huggingface_model == "bert-base-uncased"
            assert settings.huggingface_device == "cuda"


class TestGetSentimentService:
    """get_sentiment_service 函數測試"""

    def test_returns_mock_service_by_default(self):
        """默認應返回 MockSentimentService"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"SENTIMENT_MODE": "mock"}, clear=True):
            get_settings.cache_clear()
            service = get_sentiment_service()
            assert isinstance(service, MockSentimentService)

    def test_returns_mock_service_explicitly(self):
        """明確設置 mock 模式應返回 MockSentimentService"""
        get_settings.cache_clear()
        env = {"SENTIMENT_MODE": "mock", "BLOCKCHAIN_NETWORK": "mock"}
        with patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            service = get_sentiment_service()
            assert isinstance(service, MockSentimentService)
            assert service.service_name == "mock"


class TestRateLimitSettings:
    """Rate Limit 配置測試"""

    def test_default_rate_limit_disabled(self):
        """默認應禁用 Rate Limit"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.rate_limit_enabled is False

    def test_default_requests_per_minute(self):
        """默認每分鐘請求數應為 60"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.rate_limit_requests_per_minute == 60

    def test_rate_limit_env_override(self):
        """環境變數應能覆蓋 Rate Limit 設置"""
        env = {
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_REQUESTS_PER_MINUTE": "100",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.rate_limit_enabled is True
            assert settings.rate_limit_requests_per_minute == 100


class TestGetRateLimiter:
    """get_rate_limiter 函數測試"""

    def test_returns_none_when_disabled(self):
        """禁用時應返回 None"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "false"}, clear=True):
            get_settings.cache_clear()
            limiter = get_rate_limiter()
            assert limiter is None

    def test_returns_limiter_when_enabled(self):
        """啟用時應返回 InMemoryRateLimiter"""
        get_settings.cache_clear()
        env = {"RATE_LIMIT_ENABLED": "true", "RATE_LIMIT_REQUESTS_PER_MINUTE": "30"}
        with patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            limiter = get_rate_limiter()
            assert isinstance(limiter, InMemoryRateLimiter)
            assert limiter.service_name == "in_memory_rate_limiter"


class TestAuditLogSettings:
    """Audit Log 配置測試"""

    def test_default_audit_log_disabled(self):
        """默認應禁用 Audit Log"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.audit_logging_enabled is False

    def test_audit_log_env_override(self):
        """環境變數應能覆蓋 Audit Log 設置"""
        env = {"AUDIT_LOGGING_ENABLED": "true"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.audit_logging_enabled is True


class TestGetAuditLogger:
    """get_audit_logger 函數測試"""

    def test_returns_none_when_disabled(self):
        """禁用時應返回 None"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"AUDIT_LOGGING_ENABLED": "false"}, clear=True):
            get_settings.cache_clear()
            logger = get_audit_logger()
            assert logger is None

    def test_returns_logger_when_enabled(self):
        """啟用時應返回 InMemoryAuditLogger"""
        get_settings.cache_clear()
        env = {"AUDIT_LOGGING_ENABLED": "true"}
        with patch.dict(os.environ, env, clear=True):
            get_settings.cache_clear()
            logger = get_audit_logger()
            assert isinstance(logger, InMemoryAuditLogger)
            assert logger.service_name == "in_memory_audit_logger"
