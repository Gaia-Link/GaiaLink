# V2 Merge Plan: GaiaLink Original <- Gaia_SpoonOS

> **Generated**: 2026-01-31
> **Purpose**: Safely merge V2 features into the original MVP repository

---

## Executive Summary

| Metric | Original (MVP) | V2 (SpoonOS) | Delta |
|--------|---------------|--------------|-------|
| Tools | 4 | 13 | +9 |
| Services | 5 | 7 | +2 |
| Agent Classes | 1 | 2 | +1 |
| Test Files | 11 | 21 | +10 |
| Test Coverage | ~80% | 83.53% | +3.5% |

---

## Part 1: Architecture Comparison

### 1.1 Agent Layer

```
ORIGINAL (agent.py)                    V2 (agent.py + agent_v2.py)
===================                    ============================
GaiaLinkAgent                          GaiaLinkAgent (preserved)
  |                                      |
  +-- SpoonReactAI                       +-- SpoonReactAI
  +-- 4 tools                            +-- 4 tools
  +-- Basic system prompt
                                       GaiaLinkAgentV2 [NEW]
                                         |
                                         +-- SpoonReactAI
                                         +-- SimpleSkillManager
                                         +-- 9 native tools
                                         +-- MCP tool support
                                         +-- Auto skill trigger
```

**Key Difference**: V2 adds `GaiaLinkAgentV2` which supports MCP integration and Skills system, while preserving backward compatibility with original `GaiaLinkAgent`.

### 1.2 Service Layer

```
ORIGINAL services/                     V2 services/
==================                     =============
base.py           [SAME]               base.py
mock_blockchain.py [SAME]              mock_blockchain.py
sepolia_blockchain.py [SAME]           sepolia_blockchain.py
polymarket/       [SAME]               polymarket/
sentiment/        [SAME]               sentiment/
ratelimit/        [SAME]               ratelimit/
audit/            [SAME]               audit/
                                       proposal/        [NEW]
                                       x402/            [NEW]
```

**New Services**:
1. **Proposal Service** - Crowdfunding proposal state machine (5 states)
2. **X402 Service** - HTTP 402 Payment Required protocol support

### 1.3 Tools Layer

```
ORIGINAL tools/                        V2 tools/
===============                        ==========
verify_crisis.py      [SAME]           verify_crisis.py
analyze_sentiment.py  [SAME]           analyze_sentiment.py
execute_donation.py   [SAME]           execute_donation.py
list_crises.py        [ORIGINAL ONLY]  (removed in V2)
                                       create_proposal.py      [NEW]
                                       contribute_proposal.py  [NEW]
                                       activate_proposal.py    [NEW]
                                       withdraw_contribution.py [NEW]
                                       query_proposals.py      [NEW]
                                       list_institutions.py    [NEW]
                                       x402_payment.py         [NEW]
```

**Note**: `list_crises.py` exists in ORIGINAL but was removed in V2. Decision needed: keep or remove?

### 1.4 New Components (V2 Only)

| Component | Path | Description |
|-----------|------|-------------|
| MCP Server | `mcp_server.py` | FastMCP server for external tool access |
| Skills | `skills/crisis-response/SKILL.md` | Crisis response skill definition |
| Skills | `skills/donation-advisor/SKILL.md` | Donation advice skill definition |
| Skills | `skills/pool-manager/SKILL.md` | Pool management skill definition |

---

## Part 2: Detailed Diff Analysis

### 2.1 services/__init__.py

```python
# ORIGINAL (113 lines) - Exports: 30 symbols
# V2 (173 lines) - Exports: 42 symbols

# NEW IMPORTS in V2:
+ from gaia_link.services.proposal import (
+     ProposalStatus, ProposalInfo, ContributionInfo, InstitutionInfo,
+     ProposalService, WhitelistService, MockProposalService, MockWhitelistService,
+     get_proposal_service, get_whitelist_service, set_proposal_service,
+     set_whitelist_service, reset_services as reset_proposal_services,
+ )
+
+ from gaia_link.services.x402 import (
+     PaymentStatus, PaymentRequirements, PaymentRequest, PaymentHeader,
+     VerifyResult, SettleResult, PaymentReceipt, X402Config, X402Service,
+     get_x402_service, set_x402_service, reset_x402_service,
+ )
```

### 2.2 tools/__init__.py

```python
# ORIGINAL (17 lines) - Exports: 4 tools
# V2 (45 lines) - Exports: 13 tools

# ORIGINAL has ListCrisesTool (V2 does not)
- from gaia_link.tools.list_crises import ListCrisesTool

# V2 adds:
+ from gaia_link.tools.create_proposal import CreateProposalTool
+ from gaia_link.tools.contribute_proposal import ContributeProposalTool
+ from gaia_link.tools.activate_proposal import ActivateProposalTool
+ from gaia_link.tools.withdraw_contribution import WithdrawContributionTool
+ from gaia_link.tools.query_proposals import QueryProposalsTool
+ from gaia_link.tools.list_institutions import ListInstitutionsTool
+ from gaia_link.tools.x402_payment import (
+     X402PaymentTool, X402VerifyPaymentTool,
+     X402SettlePaymentTool, X402DecodeReceiptTool,
+ )
```

### 2.3 agent.py vs agent_v2.py

| Aspect | Original agent.py | V2 agent_v2.py |
|--------|------------------|----------------|
| Class | `GaiaLinkAgent` | `GaiaLinkAgentV2` |
| Base | `SpoonReactAI` | `SpoonReactAI` |
| Tools | 4 (basic) | 9 (proposal system) |
| Skills | None | 3 (via SimpleSkillManager) |
| MCP | None | Yes (MCPTool support) |
| System Prompt | English/Chinese | Chinese focused |
| Max Steps | 5 | 8 |
| Lines | 170 | 619 |

---

## Part 3: Merge Strategy

### Strategy Options

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Additive** | Add new files, preserve original | Safe, reversible | May have duplicates |
| **B: Replace** | Replace with V2 entirely | Clean | May break frontend |
| **C: Feature Branch** | Create branch, merge via PR | Best practice | More steps |

**Recommended: Option C (Feature Branch)**

### 3.1 Phase 1: Copy New Service Directories (LOW RISK)

```bash
# Copy proposal service
cp -r Gaia_SpoonOS/python_agent/gaia_link/services/proposal \
      GaiaLink_Original/python_agent/gaia_link/services/

# Copy x402 service
cp -r Gaia_SpoonOS/python_agent/gaia_link/services/x402 \
      GaiaLink_Original/python_agent/gaia_link/services/
```

**Files Added**:
- `services/proposal/__init__.py`
- `services/proposal/models.py`
- `services/proposal/base.py`
- `services/proposal/mock_proposal.py`
- `services/proposal/mock_whitelist.py`
- `services/x402/__init__.py`
- `services/x402/models.py`
- `services/x402/base.py`
- `services/x402/mock_x402.py`

### 3.2 Phase 2: Copy New Tool Files (LOW RISK)

```bash
# Proposal tools
cp Gaia_SpoonOS/python_agent/gaia_link/tools/create_proposal.py \
   GaiaLink_Original/python_agent/gaia_link/tools/
cp Gaia_SpoonOS/python_agent/gaia_link/tools/contribute_proposal.py \
   GaiaLink_Original/python_agent/gaia_link/tools/
cp Gaia_SpoonOS/python_agent/gaia_link/tools/activate_proposal.py \
   GaiaLink_Original/python_agent/gaia_link/tools/
cp Gaia_SpoonOS/python_agent/gaia_link/tools/withdraw_contribution.py \
   GaiaLink_Original/python_agent/gaia_link/tools/
cp Gaia_SpoonOS/python_agent/gaia_link/tools/query_proposals.py \
   GaiaLink_Original/python_agent/gaia_link/tools/
cp Gaia_SpoonOS/python_agent/gaia_link/tools/list_institutions.py \
   GaiaLink_Original/python_agent/gaia_link/tools/

# X402 tools
cp Gaia_SpoonOS/python_agent/gaia_link/tools/x402_payment.py \
   GaiaLink_Original/python_agent/gaia_link/tools/
```

**Files Added**: 7 tool files

### 3.3 Phase 3: Update __init__.py Files (MEDIUM RISK)

**File**: `gaia_link/services/__init__.py`

Add after line 47 (after Audit imports):
```python
# Proposal Service
from gaia_link.services.proposal import (
    ProposalStatus,
    ProposalInfo,
    ContributionInfo,
    InstitutionInfo,
    ProposalService,
    WhitelistService,
    MockProposalService,
    MockWhitelistService,
    get_proposal_service,
    get_whitelist_service,
    set_proposal_service,
    set_whitelist_service,
    reset_services as reset_proposal_services,
)

# X402 Payment Service
from gaia_link.services.x402 import (
    PaymentStatus,
    PaymentRequirements,
    PaymentRequest,
    PaymentHeader,
    VerifyResult,
    SettleResult,
    PaymentReceipt,
    X402Config,
    X402Service,
    get_x402_service,
    set_x402_service,
    reset_x402_service,
)
```

Update `__all__` list to include new exports.

**File**: `gaia_link/tools/__init__.py`

Add after line 10 (after existing imports):
```python
# Phase 1-2 Proposal Tools
from gaia_link.tools.create_proposal import CreateProposalTool
from gaia_link.tools.contribute_proposal import ContributeProposalTool
from gaia_link.tools.activate_proposal import ActivateProposalTool
from gaia_link.tools.withdraw_contribution import WithdrawContributionTool
from gaia_link.tools.query_proposals import QueryProposalsTool
from gaia_link.tools.list_institutions import ListInstitutionsTool

# Phase 3 X402 Payment Tools
from gaia_link.tools.x402_payment import (
    X402PaymentTool,
    X402VerifyPaymentTool,
    X402SettlePaymentTool,
    X402DecodeReceiptTool,
)
```

Update `__all__` list.

### 3.4 Phase 4: Copy Tests (LOW RISK)

```bash
# Proposal tests
cp Gaia_SpoonOS/python_agent/tests/test_proposal_models.py \
   GaiaLink_Original/python_agent/tests/
cp Gaia_SpoonOS/python_agent/tests/test_proposal_service.py \
   GaiaLink_Original/python_agent/tests/
cp Gaia_SpoonOS/python_agent/tests/test_proposal_tools.py \
   GaiaLink_Original/python_agent/tests/
cp Gaia_SpoonOS/python_agent/tests/test_whitelist_service.py \
   GaiaLink_Original/python_agent/tests/

# X402 tests
cp Gaia_SpoonOS/python_agent/tests/test_x402_service.py \
   GaiaLink_Original/python_agent/tests/
cp Gaia_SpoonOS/python_agent/tests/test_x402_tools.py \
   GaiaLink_Original/python_agent/tests/
```

**Files Added**: 6 test files

### 3.5 Phase 5: Optional - Add Agent V2 + MCP + Skills (OPTIONAL)

```bash
# Agent V2
cp Gaia_SpoonOS/python_agent/gaia_link/agent_v2.py \
   GaiaLink_Original/python_agent/gaia_link/

# MCP Server
cp Gaia_SpoonOS/python_agent/gaia_link/mcp_server.py \
   GaiaLink_Original/python_agent/gaia_link/

# Skills directory
cp -r Gaia_SpoonOS/python_agent/gaia_link/skills \
      GaiaLink_Original/python_agent/gaia_link/

# V2 tests
cp Gaia_SpoonOS/python_agent/tests/test_agent_v2.py \
   GaiaLink_Original/python_agent/tests/
cp Gaia_SpoonOS/python_agent/tests/test_mcp_server.py \
   GaiaLink_Original/python_agent/tests/
cp Gaia_SpoonOS/python_agent/tests/test_skills.py \
   GaiaLink_Original/python_agent/tests/
```

---

## Part 4: Risk Assessment

| Phase | Risk | Impact | Mitigation |
|-------|------|--------|------------|
| 1. Services | LOW | None - new directories | Git revert if needed |
| 2. Tools | LOW | None - new files | Git revert if needed |
| 3. __init__.py | MEDIUM | Import errors | Test after change |
| 4. Tests | LOW | None - new files | Run pytest |
| 5. Agent V2 | LOW | Optional component | Don't change existing code |

### Potential Issues

1. **Import Conflicts**: V2 removes `ListCrisesTool` - ensure it's kept in original
2. **Dependency Versions**: Check `requirements.txt` compatibility
3. **Frontend Integration**: `service.py` may need updates for new tools
4. **Test Isolation**: New tests may need conftest.py updates

---

## Part 5: Verification Checklist

### After Phase 1-2 (Services + Tools)
```bash
cd GaiaLink_Original/python_agent
python -c "from gaia_link.services.proposal import MockProposalService; print('OK')"
python -c "from gaia_link.services.x402 import get_x402_service; print('OK')"
python -c "from gaia_link.tools.create_proposal import CreateProposalTool; print('OK')"
```

### After Phase 3 (Init Files)
```bash
cd GaiaLink_Original/python_agent
python -c "from gaia_link.services import ProposalStatus, PaymentRequest; print('OK')"
python -c "from gaia_link.tools import CreateProposalTool, X402PaymentTool; print('OK')"
```

### After Phase 4 (Tests)
```bash
cd GaiaLink_Original/python_agent
python -m pytest tests/test_proposal_*.py -v
python -m pytest tests/test_x402_*.py -v
python -m pytest tests/test_whitelist_service.py -v
```

### Full Test Suite
```bash
python -m pytest tests/ -v --tb=short
```

---

## Part 6: Rollback Plan

If merge fails:

```bash
cd GaiaLink_Original
git checkout .
git clean -fd
```

Or selectively:
```bash
git checkout -- python_agent/gaia_link/services/__init__.py
git checkout -- python_agent/gaia_link/tools/__init__.py
rm -rf python_agent/gaia_link/services/proposal
rm -rf python_agent/gaia_link/services/x402
rm python_agent/gaia_link/tools/create_proposal.py
# ... etc
```

---

## Appendix A: File Inventory

### Files to ADD (16 files)

| Source | Destination |
|--------|-------------|
| `services/proposal/__init__.py` | Same |
| `services/proposal/models.py` | Same |
| `services/proposal/base.py` | Same |
| `services/proposal/mock_proposal.py` | Same |
| `services/proposal/mock_whitelist.py` | Same |
| `services/x402/__init__.py` | Same |
| `services/x402/models.py` | Same |
| `services/x402/base.py` | Same |
| `services/x402/mock_x402.py` | Same |
| `tools/create_proposal.py` | Same |
| `tools/contribute_proposal.py` | Same |
| `tools/activate_proposal.py` | Same |
| `tools/withdraw_contribution.py` | Same |
| `tools/query_proposals.py` | Same |
| `tools/list_institutions.py` | Same |
| `tools/x402_payment.py` | Same |

### Files to MODIFY (2 files)

| File | Changes |
|------|---------|
| `services/__init__.py` | Add Proposal + X402 imports |
| `tools/__init__.py` | Add 10 new tool imports |

### Files to ADD (Tests - 6 files)

| File |
|------|
| `tests/test_proposal_models.py` |
| `tests/test_proposal_service.py` |
| `tests/test_proposal_tools.py` |
| `tests/test_whitelist_service.py` |
| `tests/test_x402_service.py` |
| `tests/test_x402_tools.py` |

---

## Appendix B: Decision Points

### Decision 1: Keep ListCrisesTool?

- **Original**: Has `list_crises.py` tool
- **V2**: Removed this tool
- **Recommendation**: KEEP in merged version for backward compatibility

### Decision 2: Include Agent V2?

- **Option A**: Skip - keep original agent only
- **Option B**: Add as optional alternative
- **Recommendation**: Option B - add but don't replace

### Decision 3: Include MCP + Skills?

- **Option A**: Skip - not needed for core functionality
- **Option B**: Include for Hackathon demo
- **Recommendation**: Depends on demo requirements

---

**WAITING FOR CONFIRMATION**: Proceed with this merge plan? (yes/modify/questions)
