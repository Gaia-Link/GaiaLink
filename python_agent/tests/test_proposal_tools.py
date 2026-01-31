"""
Proposal Tools 測試

測試 6 個提案相關工具的功能。
"""

import pytest

from gaia_link.services.proposal import (
    reset_services,
    set_proposal_service,
    set_whitelist_service,
    MockProposalService,
    MockWhitelistService,
    ProposalStatus,
)


@pytest.fixture(autouse=True)
def reset_global_services():
    """每個測試前重置全局服務"""
    reset_services()
    yield
    reset_services()


@pytest.fixture
def whitelist_service():
    """創建白名單服務"""
    service = MockWhitelistService()
    set_whitelist_service(service)
    return service


@pytest.fixture
def proposal_service(whitelist_service):
    """創建提案服務"""
    service = MockProposalService(whitelist_service=whitelist_service)
    set_proposal_service(service)
    return service


class TestCreateProposalTool:
    """CreateProposalTool 測試"""

    @pytest.mark.asyncio
    async def test_create_proposal_success(self, proposal_service, whitelist_service):
        """成功創建提案"""
        from gaia_link.tools.create_proposal import CreateProposalTool

        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        tool = CreateProposalTool()
        result = await tool.execute(
            title="Earthquake Relief",
            description="Help victims",
            target_amount=10000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        assert result["success"] is True
        assert "proposal" in result
        assert result["proposal"]["title"] == "Earthquake Relief"

    @pytest.mark.asyncio
    async def test_create_proposal_invalid_institution(self, proposal_service):
        """非白名單機構應失敗"""
        from gaia_link.tools.create_proposal import CreateProposalTool

        tool = CreateProposalTool()
        result = await tool.execute(
            title="Test",
            description="Test",
            target_amount=10000.0,
            deadline_days=30,
            institution_address="0xNotWhitelisted",
            creator_address="0xCreator",
        )

        assert result["success"] is False
        assert "whitelist" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_proposal_invalid_deadline(self, proposal_service, whitelist_service):
        """無效期限應失敗"""
        from gaia_link.tools.create_proposal import CreateProposalTool

        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        tool = CreateProposalTool()
        result = await tool.execute(
            title="Test",
            description="Test",
            target_amount=10000.0,
            deadline_days=3,  # 太短
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        assert result["success"] is False
        assert "deadline" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_proposal_invalid_amount(self, proposal_service, whitelist_service):
        """金額太低應失敗"""
        from gaia_link.tools.create_proposal import CreateProposalTool

        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        tool = CreateProposalTool()
        result = await tool.execute(
            title="Test",
            description="Test",
            target_amount=50.0,  # 太低
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        assert result["success"] is False
        assert "amount" in result["error"].lower()


class TestContributeProposalTool:
    """ContributeProposalTool 測試"""

    @pytest.fixture
    async def proposal(self, proposal_service, whitelist_service):
        """創建測試提案"""
        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        return await proposal_service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

    @pytest.mark.asyncio
    async def test_contribute_success(self, proposal_service, proposal):
        """成功捐款"""
        from gaia_link.tools.contribute_proposal import ContributeProposalTool

        tool = ContributeProposalTool()
        result = await tool.execute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor",
        )

        assert result["success"] is True
        assert "contribution" in result

    @pytest.mark.asyncio
    async def test_contribute_invalid_proposal(self, proposal_service):
        """不存在的提案應失敗"""
        from gaia_link.tools.contribute_proposal import ContributeProposalTool

        tool = ContributeProposalTool()
        result = await tool.execute(
            proposal_id="invalid-id",
            amount=100.0,
            contributor_address="0xDonor",
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_contribute_to_funded_proposal(self, proposal_service, proposal):
        """已達標的提案不能再捐款"""
        from gaia_link.tools.contribute_proposal import ContributeProposalTool

        # 先達標
        await proposal_service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor1",
        )

        tool = ContributeProposalTool()
        result = await tool.execute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor2",
        )

        assert result["success"] is False


class TestActivateProposalTool:
    """ActivateProposalTool 測試"""

    @pytest.fixture
    async def funded_proposal(self, proposal_service, whitelist_service):
        """創建已達標的測試提案"""
        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        proposal = await proposal_service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        await proposal_service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        return proposal, institution

    @pytest.mark.asyncio
    async def test_activate_success(self, proposal_service, funded_proposal):
        """機構成功激活"""
        from gaia_link.tools.activate_proposal import ActivateProposalTool

        proposal, institution = funded_proposal

        tool = ActivateProposalTool()
        result = await tool.execute(
            proposal_id=proposal.proposal_id,
            institution_address=institution.address,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_activate_not_funded(self, proposal_service, whitelist_service):
        """未達標的提案不能激活"""
        from gaia_link.tools.activate_proposal import ActivateProposalTool

        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        proposal = await proposal_service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        tool = ActivateProposalTool()
        result = await tool.execute(
            proposal_id=proposal.proposal_id,
            institution_address=institution.address,
        )

        assert result["success"] is False


class TestWithdrawContributionTool:
    """WithdrawContributionTool 測試"""

    @pytest.fixture
    async def cancelled_proposal(self, proposal_service, whitelist_service):
        """創建已取消的測試提案"""
        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        proposal = await proposal_service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        await proposal_service.contribute(
            proposal_id=proposal.proposal_id,
            amount=1000.0,
            contributor_address="0xDonor",
        )

        await proposal_service.reject(
            proposal_id=proposal.proposal_id,
            institution_address=institution.address,
        )

        return proposal

    @pytest.mark.asyncio
    async def test_withdraw_success(self, proposal_service, cancelled_proposal):
        """成功退款"""
        from gaia_link.tools.withdraw_contribution import WithdrawContributionTool

        tool = WithdrawContributionTool()
        result = await tool.execute(
            proposal_id=cancelled_proposal.proposal_id,
            contributor_address="0xDonor",
        )

        assert result["success"] is True
        assert "withdrawal" in result

    @pytest.mark.asyncio
    async def test_withdraw_from_funding_proposal(self, proposal_service, whitelist_service):
        """募資中的提案不能退款"""
        from gaia_link.tools.withdraw_contribution import WithdrawContributionTool

        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        proposal = await proposal_service.create_proposal(
            title="Test",
            description="Test",
            target_amount=1000.0,
            deadline_days=30,
            institution_address=institution.address,
            creator_address="0xCreator",
        )

        await proposal_service.contribute(
            proposal_id=proposal.proposal_id,
            amount=100.0,
            contributor_address="0xDonor",
        )

        tool = WithdrawContributionTool()
        result = await tool.execute(
            proposal_id=proposal.proposal_id,
            contributor_address="0xDonor",
        )

        assert result["success"] is False


class TestQueryProposalsTool:
    """QueryProposalsTool 測試"""

    @pytest.fixture
    async def proposals(self, proposal_service, whitelist_service):
        """創建多個測試提案"""
        institutions = await whitelist_service.list_institutions()
        institution = institutions[0]

        proposals = []
        for i in range(5):
            proposal = await proposal_service.create_proposal(
                title=f"Proposal {i}",
                description=f"Test {i}",
                target_amount=1000.0 * (i + 1),
                deadline_days=30,
                institution_address=institution.address,
                creator_address="0xCreator",
                region="Asia" if i % 2 == 0 else "Europe",
            )
            proposals.append(proposal)
        return proposals

    @pytest.mark.asyncio
    async def test_query_all(self, proposal_service, proposals):
        """查詢所有提案"""
        from gaia_link.tools.query_proposals import QueryProposalsTool

        tool = QueryProposalsTool()
        result = await tool.execute()

        assert "proposals" in result
        assert result["total_count"] == 5

    @pytest.mark.asyncio
    async def test_query_by_status(self, proposal_service, proposals):
        """按狀態篩選"""
        from gaia_link.tools.query_proposals import QueryProposalsTool

        tool = QueryProposalsTool()
        result = await tool.execute(status="FUNDING")

        for p in result["proposals"]:
            assert p["status"] == "FUNDING"

    @pytest.mark.asyncio
    async def test_query_by_region(self, proposal_service, proposals):
        """按地區篩選"""
        from gaia_link.tools.query_proposals import QueryProposalsTool

        tool = QueryProposalsTool()
        result = await tool.execute(region="Asia")

        for p in result["proposals"]:
            assert p["region"] == "Asia"


class TestListInstitutionsTool:
    """ListInstitutionsTool 測試"""

    @pytest.mark.asyncio
    async def test_list_all(self, whitelist_service):
        """列出所有機構"""
        from gaia_link.tools.list_institutions import ListInstitutionsTool

        tool = ListInstitutionsTool()
        result = await tool.execute()

        assert "institutions" in result
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_list_by_region(self, whitelist_service):
        """按地區篩選"""
        from gaia_link.tools.list_institutions import ListInstitutionsTool

        # 添加特定地區的機構
        await whitelist_service.add_institution(
            address="0xAsia001",
            name="Asia Relief",
            region="Asia",
        )

        tool = ListInstitutionsTool()
        result = await tool.execute(region="Asia")

        for i in result["institutions"]:
            assert i["region"] == "Asia"

    @pytest.mark.asyncio
    async def test_list_active_only(self, whitelist_service):
        """只列出活躍機構"""
        from gaia_link.tools.list_institutions import ListInstitutionsTool

        # 添加非活躍機構
        await whitelist_service.add_institution(
            address="0xInactive001",
            name="Inactive Org",
            region="Test",
        )
        await whitelist_service.update_institution(
            address="0xInactive001",
            is_active=False,
        )

        tool = ListInstitutionsTool()
        result = await tool.execute(active_only=True)

        for i in result["institutions"]:
            assert i["is_active"] is True
