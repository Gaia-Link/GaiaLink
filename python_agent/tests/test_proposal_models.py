"""
Proposal Models 測試

測試數據模型的定義和屬性。
"""

import pytest
from datetime import datetime, timedelta

from gaia_link.services.proposal.models import (
    ProposalStatus,
    ProposalInfo,
    ContributionInfo,
    InstitutionInfo,
)


class TestProposalStatus:
    """提案狀態枚舉測試"""

    def test_status_values(self):
        """狀態值應符合定義"""
        assert ProposalStatus.FUNDING == 0
        assert ProposalStatus.FUNDED == 1
        assert ProposalStatus.ACTIVATED == 2
        assert ProposalStatus.EXPIRED == 3
        assert ProposalStatus.CANCELLED == 4

    def test_status_is_intenum(self):
        """狀態應該是 IntEnum"""
        assert isinstance(ProposalStatus.FUNDING, int)
        assert ProposalStatus.FUNDING == 0

    def test_status_comparison(self):
        """狀態應支援比較"""
        assert ProposalStatus.FUNDING < ProposalStatus.FUNDED
        assert ProposalStatus.ACTIVATED > ProposalStatus.FUNDED


class TestProposalInfo:
    """提案資訊測試"""

    @pytest.fixture
    def sample_proposal(self):
        """創建測試用提案"""
        return ProposalInfo(
            proposal_id="prop-001",
            address="0x1234567890abcdef",
            creator="0xCreator",
            institution="0xInstitution",
            institution_name="Red Cross",
            title="Emergency Relief",
            description="Help earthquake victims",
            target_amount=10000.0,
            total_raised=5000.0,
            deadline=datetime.now() + timedelta(days=30),
            status=ProposalStatus.FUNDING,
            contributors_count=10,
            region="Asia",
        )

    def test_proposal_creation(self, sample_proposal):
        """應能創建提案"""
        assert sample_proposal.proposal_id == "prop-001"
        assert sample_proposal.title == "Emergency Relief"
        assert sample_proposal.status == ProposalStatus.FUNDING

    def test_progress_percent(self, sample_proposal):
        """進度百分比計算正確"""
        assert sample_proposal.progress_percent == 50.0

    def test_progress_percent_zero_target(self):
        """目標為零時進度為 0"""
        proposal = ProposalInfo(
            proposal_id="prop-002",
            address="0x...",
            creator="0x...",
            institution="0x...",
            institution_name="Test",
            title="Test",
            description="Test",
            target_amount=0,
            total_raised=100,
            deadline=datetime.now(),
            status=ProposalStatus.FUNDING,
        )
        assert proposal.progress_percent == 0.0

    def test_progress_percent_capped_at_100(self):
        """進度百分比上限為 100"""
        proposal = ProposalInfo(
            proposal_id="prop-003",
            address="0x...",
            creator="0x...",
            institution="0x...",
            institution_name="Test",
            title="Test",
            description="Test",
            target_amount=1000,
            total_raised=2000,  # 超募
            deadline=datetime.now(),
            status=ProposalStatus.FUNDED,
        )
        assert proposal.progress_percent == 100.0

    def test_is_funded_true(self, sample_proposal):
        """達標判斷 - 已達標"""
        sample_proposal.total_raised = 10000.0
        assert sample_proposal.is_funded is True

    def test_is_funded_false(self, sample_proposal):
        """達標判斷 - 未達標"""
        assert sample_proposal.is_funded is False

    def test_remaining_amount(self, sample_proposal):
        """剩餘金額計算"""
        assert sample_proposal.remaining_amount == 5000.0

    def test_remaining_amount_zero_when_funded(self, sample_proposal):
        """達標時剩餘為 0"""
        sample_proposal.total_raised = 15000.0
        assert sample_proposal.remaining_amount == 0.0

    def test_optional_fields_default(self):
        """可選欄位默認值"""
        proposal = ProposalInfo(
            proposal_id="prop-004",
            address="0x...",
            creator="0x...",
            institution="0x...",
            institution_name="Test",
            title="Test",
            description="Test",
            target_amount=1000,
            total_raised=0,
            deadline=datetime.now(),
            status=ProposalStatus.FUNDING,
        )
        assert proposal.funded_at is None
        assert proposal.activation_deadline is None
        assert proposal.contributors_count == 0
        assert proposal.region is None


class TestContributionInfo:
    """捐款記錄測試"""

    def test_contribution_creation(self):
        """應能創建捐款記錄"""
        contribution = ContributionInfo(
            contributor="0xDonor",
            amount=100.0,
            timestamp=datetime.now(),
            proposal_id="prop-001",
        )
        assert contribution.contributor == "0xDonor"
        assert contribution.amount == 100.0

    def test_contribution_with_tx_hash(self):
        """捐款記錄可包含交易哈希"""
        contribution = ContributionInfo(
            contributor="0xDonor",
            amount=100.0,
            timestamp=datetime.now(),
            proposal_id="prop-001",
            tx_hash="0xabcdef...",
        )
        assert contribution.tx_hash == "0xabcdef..."


class TestInstitutionInfo:
    """機構資訊測試"""

    def test_institution_creation(self):
        """應能創建機構資訊"""
        institution = InstitutionInfo(
            address="0xRedCross",
            name="Red Cross",
            region="Global",
        )
        assert institution.address == "0xRedCross"
        assert institution.is_active is True  # 默認值

    def test_institution_defaults(self):
        """默認值正確"""
        institution = InstitutionInfo(
            address="0x...",
            name="Test",
            region="Test",
        )
        assert institution.is_active is True
        assert institution.total_received == 0.0
        assert institution.proposals_count == 0
        assert institution.website is None
        assert institution.description is None

    def test_institution_full_info(self):
        """完整資訊"""
        institution = InstitutionInfo(
            address="0xUNICEF",
            name="UNICEF",
            region="Global",
            is_active=True,
            total_received=1000000.0,
            proposals_count=50,
            website="https://unicef.org",
            description="United Nations Children's Fund",
        )
        assert institution.name == "UNICEF"
        assert institution.website == "https://unicef.org"
