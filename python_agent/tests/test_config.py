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
    get_settings,
    get_blockchain_service,
    get_polymarket_service,
)
from gaia_link.services import MockBlockchainService, MockPolymarketService


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
        """默認應使用 MOCK 模式"""
        with patch.dict(os.environ, {}, clear=True):
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
