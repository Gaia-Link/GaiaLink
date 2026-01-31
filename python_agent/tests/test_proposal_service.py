"""
ProposalService 測試

測試提案服務的 Mock 實作。
"""

import pytest
from datetime import datetime, timedelta

from gaia_link.services.proposal.models import (
    ProposalStatus,
    ProposalInfo,
    ContributionInfo,
)
from gaia_link.services.proposal.base import ProposalService


class TestMockProposalServiceCreation:
    """MockProposalService 創建提案測試"""

    @pytest.fixture
    def proposal_service(self):
        """創建提案服務實例"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        return MockProposalService(whitelist_service=whitelist)

    @pytest.fixture
    async def institution_address(self, proposal_service):
        """獲取白名單機構地址"""
        institutions = await proposal_service._whitelist_service.list_institutions()
        return institutions[0].address

    @pytest.mark.asyncio
    async def test_service_is_proposal_service(self, proposal_service):
        """服務應該是 ProposalService 的實例"""
        assert isinstance(proposal_service, ProposalService)

    @pytest.mark.asyncio
    async def test_create_proposal_success(self, proposal_service, institution_address):
        """成功創建提案"""
        proposal = await proposal_service.create_proposal(
            title="Earthquake Relief",
            description="Help victims of the earthquake",
            target_amount=10000.0,
            deadline_days=30,
            institution_address=institution_address,
            creator_address="0xCreator",
            region="Asia",
        )

        assert isinstance(proposal, ProposalInfo)
        assert proposal.title == "Earthquake Relief"
        assert proposal.target_amount == 10000.0
        assert proposal.status == ProposalStatus.FUNDING
        assert proposal.total_raised == 0.0

    @pytest.mark.asyncio
    async def test_create_proposal_generates_id(self, proposal_service, institution_address):
        """創建提案應生成唯一 ID"""
        proposal1 = await proposal_service.create_proposal(
            title="Proposal 1",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution_address,
            creator_address="0xCreator",
        )
        proposal2 = await proposal_service.create_proposal(
            title="Proposal 2",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution_address,
            creator_address="0xCreator",
        )

        assert proposal1.proposal_id != proposal2.proposal_id

    @pytest.mark.asyncio
    async def test_create_proposal_invalid_institution(self, proposal_service):
        """非白名單機構應失敗"""
        with pytest.raises(ValueError) as exc_info:
            await proposal_service.create_proposal(
                title="Test",
                description="Test",
                target_amount=1000.0,
                deadline_days=30,
                institution_address="0xNotWhitelisted",
                creator_address="0xCreator",
            )

        assert "whitelist" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_proposal_invalid_amount(self, proposal_service, institution_address):
        """無效金額應失敗"""
        with pytest.raises(ValueError):
            await proposal_service.create_proposal(
                title="Test",
                description="Test",
                target_amount=0,  # 無效
                deadline_days=30,
                institution_address=institution_address,
                creator_address="0xCreator",
            )

    @pytest.mark.asyncio
    async def test_create_proposal_invalid_deadline(self, proposal_service, institution_address):
        """無效期限應失敗"""
        with pytest.raises(ValueError):
            await proposal_service.create_proposal(
                title="Test",
                description="Test",
                target_amount=1000.0,
                deadline_days=0,  # 無效
                institution_address=institution_address,
                creator_address="0xCreator",
            )


class TestMockProposalServiceContribution:
    """MockProposalService 捐款測試"""

    @pytest.fixture
    async def service_with_proposal(self):
        """創建帶有提案的服務實例"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution_address = institutions[0].address

        proposal = await service.create_proposal(
            title="Test Proposal",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution_address,
            creator_address="0xCreator",
        )

        return service, proposal

    @pytest.mark.asyncio
    async def test_contribute_success(self, service_with_proposal):
        """成功捐款"""
        service, proposal = service_with_proposal

        contribution = await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor",
        )

        assert isinstance(contribution, ContributionInfo)
        assert contribution.amount == 100.0
        assert contribution.contributor == "0xDonor"

    @pytest.mark.asyncio
    async def test_contribute_updates_total(self, service_with_proposal):
        """捐款應更新總額"""
        service, proposal = service_with_proposal

        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor1",
        )
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=200.0,
            contributor_address="0xDonor2",
        )

        updated = await service.get_proposal(proposal.proposal_id)
        assert updated.total_raised == 300.0

    @pytest.mark.asyncio
    async def test_contribute_updates_count(self, service_with_proposal):
        """捐款應更新捐款人數"""
        service, proposal = service_with_proposal

        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor1",
        )
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=200.0,
            contributor_address="0xDonor2",
        )

        updated = await service.get_proposal(proposal.proposal_id)
        assert updated.contributors_count == 2

    @pytest.mark.asyncio
    async def test_contribute_triggers_funded_status(self, service_with_proposal):
        """達標應觸發 FUNDED 狀態"""
        service, proposal = service_with_proposal

        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,  # 達標
            contributor_address="0xDonor",
        )

        updated = await service.get_proposal(proposal.proposal_id)
        assert updated.status == ProposalStatus.FUNDED
        assert updated.funded_at is not None
        assert updated.activation_deadline is not None

    @pytest.mark.asyncio
    async def test_contribute_invalid_proposal(self, service_with_proposal):
        """不存在的提案應失敗"""
        service, _ = service_with_proposal

        with pytest.raises(ValueError) as exc_info:
            await service.contribute(
                proposal_id="invalid-id",
                amount=100.0,
                contributor_address="0xDonor",
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_contribute_invalid_amount(self, service_with_proposal):
        """無效金額應失敗"""
        service, proposal = service_with_proposal

        with pytest.raises(ValueError):
            await service.contribute(
                proposal_id=proposal.proposal_id,
                amount=0,  # 無效
                contributor_address="0xDonor",
            )

    @pytest.mark.asyncio
    async def test_contribute_to_funded_proposal(self, service_with_proposal):
        """已達標的提案不能再捐款"""
        service, proposal = service_with_proposal

        # 先達標
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        # 再捐款應失敗
        with pytest.raises(ValueError) as exc_info:
            await service.contribute(
                proposal_id=proposal.proposal_id,
                amount=100.0,
                contributor_address="0xDonor2",
            )

        assert "status" in str(exc_info.value).lower() or "funding" in str(exc_info.value).lower()


class TestMockProposalServiceActivation:
    """MockProposalService 激活測試"""

    @pytest.fixture
    async def service_with_funded_proposal(self):
        """創建帶有已達標提案的服務實例"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        proposal = await service.create_proposal(
            title="Test Proposal",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        # 達標
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        return service, proposal, institution

    @pytest.mark.asyncio
    async def test_activate_success(self, service_with_funded_proposal):
        """機構成功激活提案"""
        service, proposal, institution = service_with_funded_proposal

        result = await service.activate(
            proposal_id=proposal.proposal_id,
            institution_address=institution.address,
        )

        assert result.status == ProposalStatus.ACTIVATED

    @pytest.mark.asyncio
    async def test_activate_wrong_institution(self, service_with_funded_proposal):
        """非指定機構不能激活"""
        service, proposal, _ = service_with_funded_proposal

        with pytest.raises((ValueError, PermissionError)):
            await service.activate(
                proposal_id=proposal.proposal_id,
                institution_address="0xWrongInstitution",
            )

    @pytest.mark.asyncio
    async def test_activate_not_funded(self):
        """未達標的提案不能激活"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        proposal = await service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        with pytest.raises(ValueError) as exc_info:
            await service.activate(
                proposal_id=proposal.proposal_id,
                institution_address=institution.address,
            )

        assert "funded" in str(exc_info.value).lower() or "status" in str(exc_info.value).lower()


class TestMockProposalServiceRejection:
    """MockProposalService 拒絕測試"""

    @pytest.fixture
    async def service_with_funded_proposal(self):
        """創建帶有已達標提案的服務實例"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        proposal = await service.create_proposal(
            title="Test Proposal",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        # 達標
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        return service, proposal, institution

    @pytest.mark.asyncio
    async def test_reject_success(self, service_with_funded_proposal):
        """機構成功拒絕提案"""
        service, proposal, institution = service_with_funded_proposal

        result = await service.reject(
            proposal_id=proposal.proposal_id,
            institution_address=institution.address,
        )

        assert result.status == ProposalStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_reject_wrong_institution(self, service_with_funded_proposal):
        """非指定機構不能拒絕"""
        service, proposal, _ = service_with_funded_proposal

        with pytest.raises((ValueError, PermissionError)):
            await service.reject(
                proposal_id=proposal.proposal_id,
                institution_address="0xWrongInstitution",
            )


class TestMockProposalServiceWithdraw:
    """MockProposalService 退款測試"""

    @pytest.fixture
    async def service_with_cancelled_proposal(self):
        """創建帶有已取消提案的服務實例"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        proposal = await service.create_proposal(
            title="Test Proposal",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        # 捐款
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        # 拒絕 (變為 CANCELLED)
        await service.reject(
            proposal_id=proposal.proposal_id,
            institution_address=institution.address,
        )

        return service, proposal

    @pytest.mark.asyncio
    async def test_withdraw_success(self, service_with_cancelled_proposal):
        """成功退款"""
        service, proposal = service_with_cancelled_proposal

        contribution = await service.withdraw(
            proposal_id=proposal.proposal_id,
            contributor_address="0xDonor",
        )

        assert isinstance(contribution, ContributionInfo)
        assert contribution.amount == 1000.0

    @pytest.mark.asyncio
    async def test_withdraw_no_contribution(self, service_with_cancelled_proposal):
        """沒有捐款記錄不能退款"""
        service, proposal = service_with_cancelled_proposal

        with pytest.raises(ValueError) as exc_info:
            await service.withdraw(
                proposal_id=proposal.proposal_id,
                contributor_address="0xNotDonor",
            )

        assert "contribution" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_withdraw_funding_status_fails(self):
        """募資中的提案不能退款"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        proposal = await service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor",
        )

        with pytest.raises(ValueError) as exc_info:
            await service.withdraw(
                proposal_id=proposal.proposal_id,
                contributor_address="0xDonor",
            )

        assert "status" in str(exc_info.value).lower() or "withdraw" in str(exc_info.value).lower()


class TestMockProposalServiceQueries:
    """MockProposalService 查詢測試"""

    @pytest.fixture
    async def service_with_proposals(self):
        """創建帶有多個提案的服務實例"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        # 創建多個提案
        proposals = []
        for i in range(5):
            proposal = await service.create_proposal(
                title=f"Proposal {i}",
                description=f"Test proposal {i}",
                target_amount=1000.0 * (i + 1),
                deadline_days=30,
                institution_address=institution.address,
                creator_address="0xCreator",
                region="Asia" if i % 2 == 0 else "Europe",
            )
            proposals.append(proposal)

        return service, proposals, institution

    @pytest.mark.asyncio
    async def test_get_proposal_found(self, service_with_proposals):
        """獲取存在的提案"""
        service, proposals, _ = service_with_proposals

        result = await service.get_proposal(proposals[0].proposal_id)

        assert result is not None
        assert result.proposal_id == proposals[0].proposal_id

    @pytest.mark.asyncio
    async def test_get_proposal_not_found(self, service_with_proposals):
        """獲取不存在的提案"""
        service, _, _ = service_with_proposals

        result = await service.get_proposal("invalid-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_proposals_all(self, service_with_proposals):
        """列出所有提案"""
        service, proposals, _ = service_with_proposals

        result = await service.list_proposals()

        assert len(result) == len(proposals)

    @pytest.mark.asyncio
    async def test_list_proposals_by_status(self, service_with_proposals):
        """按狀態篩選"""
        service, _, _ = service_with_proposals

        result = await service.list_proposals(status=ProposalStatus.FUNDING)

        for proposal in result:
            assert proposal.status == ProposalStatus.FUNDING

    @pytest.mark.asyncio
    async def test_list_proposals_by_region(self, service_with_proposals):
        """按地區篩選"""
        service, _, _ = service_with_proposals

        result = await service.list_proposals(region="Asia")

        for proposal in result:
            assert proposal.region == "Asia"

    @pytest.mark.asyncio
    async def test_list_proposals_pagination(self, service_with_proposals):
        """分頁功能"""
        service, proposals, _ = service_with_proposals

        page1 = await service.list_proposals(limit=2, offset=0)
        page2 = await service.list_proposals(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].proposal_id != page2[0].proposal_id

    @pytest.mark.asyncio
    async def test_get_contributions(self, service_with_proposals):
        """獲取提案的捐款記錄"""
        service, proposals, _ = service_with_proposals
        proposal = proposals[0]

        # 添加捐款
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor1",
        )
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=200.0,
            contributor_address="0xDonor2",
        )

        contributions = await service.get_contributions(proposal.proposal_id)

        assert len(contributions) == 2

    @pytest.mark.asyncio
    async def test_get_contributions_by_contributor(self, service_with_proposals):
        """按捐款者篩選"""
        service, proposals, _ = service_with_proposals
        proposal = proposals[0]

        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor1",
        )
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=200.0,
            contributor_address="0xDonor2",
        )

        contributions = await service.get_contributions(
            proposal.proposal_id,
            contributor="0xDonor1",
        )

        assert len(contributions) == 1
        assert contributions[0].contributor == "0xDonor1"


class TestMockProposalServiceExpiry:
    """MockProposalService 過期測試"""

    @pytest.mark.asyncio
    async def test_check_expiry_funding_deadline(self):
        """募資截止未達標應變為 EXPIRED"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        # 創建一個已過期的提案 (模擬)
        proposal = await service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=1,  # 1 天
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        # 手動設置過期時間 (測試用)
        service._proposals[proposal.proposal_id].deadline = datetime.now() - timedelta(days=1)

        result = await service.check_and_update_status(proposal.proposal_id)

        assert result.status == ProposalStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_check_expiry_activation_deadline(self):
        """機構確認超時應變為 EXPIRED"""
        from gaia_link.services.proposal.mock_proposal import MockProposalService
        from gaia_link.services.proposal.mock_whitelist import MockWhitelistService
        whitelist = MockWhitelistService()
        service = MockProposalService(whitelist_service=whitelist)

        institutions = await whitelist.list_institutions()
        institution = institutions[0]

        proposal = await service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        # 達標
        await service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        # 手動設置確認截止時間已過 (測試用)
        service._proposals[proposal.proposal_id].activation_deadline = datetime.now() - timedelta(days=1)

        result = await service.check_and_update_status(proposal.proposal_id)

        assert result.status == ProposalStatus.EXPIRED
