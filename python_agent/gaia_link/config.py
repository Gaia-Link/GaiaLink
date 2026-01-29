"""
Gaia Link 配置管理

使用 pydantic-settings 管理環境變數和配置
"""

import os
from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BlockchainNetwork(str, Enum):
    """支援的區塊鏈網絡"""
    MOCK = "mock"
    SEPOLIA = "sepolia"
    MAINNET = "mainnet"  # 未來支援


class Settings(BaseSettings):
    """
    應用程式配置

    可透過環境變數或 .env 文件設置
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 區塊鏈配置
    blockchain_network: BlockchainNetwork = Field(
        default=BlockchainNetwork.MOCK,
        description="使用的區塊鏈網絡 (mock, sepolia, mainnet)",
    )

    sepolia_rpc_url: Optional[str] = Field(
        default=None,
        description="Sepolia 測試網 RPC URL (如 Alchemy, Infura)",
    )

    wallet_private_key: Optional[str] = Field(
        default=None,
        description="錢包私鑰 (僅用於測試網)",
    )

    # API 配置
    polymarket_api_url: str = Field(
        default="https://clob.polymarket.com",
        description="Polymarket API URL",
    )

    # 日誌配置
    log_level: str = Field(
        default="INFO",
        description="日誌級別 (DEBUG, INFO, WARNING, ERROR)",
    )

    audit_logging_enabled: bool = Field(
        default=False,
        description="是否啟用審計日誌",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="是否啟用請求限制",
    )

    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="每分鐘最大請求數",
    )

    def is_production(self) -> bool:
        """檢查是否為生產環境"""
        return self.blockchain_network == BlockchainNetwork.MAINNET

    def is_testnet(self) -> bool:
        """檢查是否為測試網"""
        return self.blockchain_network == BlockchainNetwork.SEPOLIA

    def is_mock(self) -> bool:
        """檢查是否為 Mock 模式"""
        return self.blockchain_network == BlockchainNetwork.MOCK


@lru_cache
def get_settings() -> Settings:
    """
    獲取配置單例

    使用 lru_cache 確保只創建一次
    """
    return Settings()


def get_blockchain_service():
    """
    根據配置獲取對應的區塊鏈服務

    Returns:
        BlockchainService: 區塊鏈服務實例
    """
    settings = get_settings()

    if settings.is_mock():
        from gaia_link.services import MockBlockchainService
        return MockBlockchainService()

    elif settings.is_testnet():
        from gaia_link.services import get_sepolia_service
        return get_sepolia_service(
            rpc_url=settings.sepolia_rpc_url,
            private_key=settings.wallet_private_key,
        )

    else:
        raise NotImplementedError(
            f"Network {settings.blockchain_network} is not yet supported"
        )
