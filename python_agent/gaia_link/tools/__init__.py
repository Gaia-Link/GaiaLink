"""
Gaia Link 工具模組

所有工具都繼承自 SpoonOS BaseTool，符合 SpoonOS 最低技術要求
"""

# Original MVP Tools
from gaia_link.tools.verify_crisis import VerifyCrisisTool
from gaia_link.tools.analyze_sentiment import AnalyzeSentimentTool
from gaia_link.tools.execute_donation import ExecuteDonationTool
from gaia_link.tools.list_crises import ListCrisesTool
from gaia_link.tools.create_vault import CreateVaultTool

# V2 Proposal Tools
from gaia_link.tools.create_proposal import CreateProposalTool
from gaia_link.tools.contribute_proposal import ContributeProposalTool
from gaia_link.tools.activate_proposal import ActivateProposalTool
from gaia_link.tools.withdraw_contribution import WithdrawContributionTool
from gaia_link.tools.query_proposals import QueryProposalsTool
from gaia_link.tools.list_institutions import ListInstitutionsTool

# V2 X402 Payment Tools
from gaia_link.tools.x402_payment import (
    X402PaymentTool,
    X402VerifyPaymentTool,
    X402SettlePaymentTool,
    X402DecodeReceiptTool,
)

__all__ = [
    # Original MVP Tools
    "VerifyCrisisTool",
    "AnalyzeSentimentTool",
    "ExecuteDonationTool",
    "ListCrisesTool",
    # V2 Proposal Tools
    "CreateProposalTool",
    "ContributeProposalTool",
    "ActivateProposalTool",
    "WithdrawContributionTool",
    "QueryProposalsTool",
    "ListInstitutionsTool",
    # V2 X402 Payment Tools
    "X402PaymentTool",
    "X402VerifyPaymentTool",
    "X402SettlePaymentTool",
    "X402DecodeReceiptTool",
]
