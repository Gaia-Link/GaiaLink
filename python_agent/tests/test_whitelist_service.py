"""
WhitelistService 測試

測試白名單服務的 Mock 實作。
"""

import pytest

from gaia_link.services.proposal.models import InstitutionInfo
from gaia_link.services.proposal.base import WhitelistService


class TestMockWhitelistService:
    """MockWhitelistService 測試"""

    @pytest.fixture
    def whitelist_service(self):
        """創建白名單服務實例"""
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        return MockWhitelistService()

    @pytest.mark.asyncio
    async def test_service_is_whitelist_service(self, whitelist_service):
        """服務應該是 WhitelistService 的實例"""
        assert isinstance(whitelist_service, WhitelistService)

    @pytest.mark.asyncio
    async def test_default_institutions_exist(self, whitelist_service):
        """應該有預設的白名單機構"""
        institutions = await whitelist_service.list_institutions()
        assert len(institutions) > 0

    @pytest.mark.asyncio
    async def test_is_whitelisted_true(self, whitelist_service):
        """已知機構應在白名單中"""
        # 獲取第一個機構的地址
        institutions = await whitelist_service.list_institutions()
        first_address = institutions[0].address
        result = await whitelist_service.is_whitelisted(first_address)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_whitelisted_false(self, whitelist_service):
        """未知地址不在白名單中"""
        result = await whitelist_service.is_whitelisted("0xUnknown")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_institution_found(self, whitelist_service):
        """應能獲取已知機構資訊"""
        institutions = await whitelist_service.list_institutions()
        first_address = institutions[0].address

        institution = await whitelist_service.get_institution(first_address)

        assert institution is not None
        assert isinstance(institution, InstitutionInfo)
        assert institution.address == first_address

    @pytest.mark.asyncio
    async def test_get_institution_not_found(self, whitelist_service):
        """未知機構應返回 None"""
        institution = await whitelist_service.get_institution("0xNotExist")
        assert institution is None

    @pytest.mark.asyncio
    async def test_list_institutions_all(self, whitelist_service):
        """列出所有機構"""
        institutions = await whitelist_service.list_institutions()
        assert isinstance(institutions, list)
        for inst in institutions:
            assert isinstance(inst, InstitutionInfo)

    @pytest.mark.asyncio
    async def test_list_institutions_by_region(self, whitelist_service):
        """按地區篩選機構"""
        # 添加不同地區的機構
        await whitelist_service.add_institution(
            address="0xAsiaOrg",
            name="Asia Relief",
            region="Asia",
        )
        await whitelist_service.add_institution(
            address="0xEuropeOrg",
            name="Europe Aid",
            region="Europe",
        )

        asia_institutions = await whitelist_service.list_institutions(region="Asia")

        for inst in asia_institutions:
            assert inst.region == "Asia"

    @pytest.mark.asyncio
    async def test_list_institutions_active_only(self, whitelist_service):
        """只列出活躍機構"""
        # 添加一個非活躍機構
        await whitelist_service.add_institution(
            address="0xInactiveOrg",
            name="Inactive Org",
            region="Test",
        )
        await whitelist_service.update_institution(
            address="0xInactiveOrg",
            is_active=False,
        )

        active_institutions = await whitelist_service.list_institutions(active_only=True)

        for inst in active_institutions:
            assert inst.is_active is True

    @pytest.mark.asyncio
    async def test_list_institutions_pagination(self, whitelist_service):
        """分頁功能"""
        # 確保有足夠的機構
        for i in range(5):
            await whitelist_service.add_institution(
                address=f"0xOrg{i}",
                name=f"Organization {i}",
                region="Test",
            )

        page1 = await whitelist_service.list_institutions(limit=3, offset=0)
        page2 = await whitelist_service.list_institutions(limit=3, offset=3)

        assert len(page1) == 3
        # page2 可能少於 3 個，取決於總數

    @pytest.mark.asyncio
    async def test_add_institution_success(self, whitelist_service):
        """成功添加機構"""
        result = await whitelist_service.add_institution(
            address="0xNewOrg",
            name="New Organization",
            region="Global",
            website="https://neworg.com",
            description="A new humanitarian organization",
        )

        assert isinstance(result, InstitutionInfo)
        assert result.address == "0xNewOrg"
        assert result.name == "New Organization"
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_add_institution_duplicate_fails(self, whitelist_service):
        """添加重複地址應失敗"""
        await whitelist_service.add_institution(
            address="0xDuplicateOrg",
            name="First",
            region="Test",
        )

        with pytest.raises(ValueError) as exc_info:
            await whitelist_service.add_institution(
                address="0xDuplicateOrg",
                name="Second",
                region="Test",
            )

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_institution_active_status(self, whitelist_service):
        """更新機構活躍狀態"""
        await whitelist_service.add_institution(
            address="0xUpdateOrg",
            name="Update Test",
            region="Test",
        )

        result = await whitelist_service.update_institution(
            address="0xUpdateOrg",
            is_active=False,
        )

        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_update_institution_name(self, whitelist_service):
        """更新機構名稱"""
        await whitelist_service.add_institution(
            address="0xRenameOrg",
            name="Old Name",
            region="Test",
        )

        result = await whitelist_service.update_institution(
            address="0xRenameOrg",
            name="New Name",
        )

        assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_institution_not_found(self, whitelist_service):
        """更新不存在的機構應失敗"""
        with pytest.raises(ValueError) as exc_info:
            await whitelist_service.update_institution(
                address="0xNotExist",
                is_active=False,
            )

        assert "not found" in str(exc_info.value).lower()


class TestMockWhitelistServicePresetInstitutions:
    """預設機構測試"""

    @pytest.fixture
    def whitelist_service(self):
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        return MockWhitelistService()

    @pytest.mark.asyncio
    async def test_has_red_cross(self, whitelist_service):
        """應包含紅十字會"""
        institutions = await whitelist_service.list_institutions()
        names = [i.name for i in institutions]
        assert any("Red Cross" in name or "紅十字" in name for name in names)

    @pytest.mark.asyncio
    async def test_has_unicef(self, whitelist_service):
        """應包含 UNICEF"""
        institutions = await whitelist_service.list_institutions()
        names = [i.name for i in institutions]
        assert any("UNICEF" in name for name in names)

    @pytest.mark.asyncio
    async def test_has_multiple_regions(self, whitelist_service):
        """應包含多個地區"""
        institutions = await whitelist_service.list_institutions()
        regions = set(i.region for i in institutions)
        assert len(regions) >= 2
