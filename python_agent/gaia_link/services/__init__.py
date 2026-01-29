"""
Gaia Link Services - 外部服務抽象層

提供可替換的服務實作，支援 Mock 和真實服務切換
"""

from gaia_link.services.base import BlockchainService, TransactionResult
from gaia_link.services.mock_blockchain import MockBlockchainService

# SepoliaBlockchainService 需要 web3 依賴，延遲導入
def get_sepolia_service(*args, **kwargs):
    """工廠函數：創建 SepoliaBlockchainService 實例"""
    from gaia_link.services.sepolia_blockchain import SepoliaBlockchainService
    return SepoliaBlockchainService(*args, **kwargs)

__all__ = [
    "BlockchainService",
    "TransactionResult",
    "MockBlockchainService",
    "get_sepolia_service",
]
