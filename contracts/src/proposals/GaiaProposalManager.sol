// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {NoLossVault} from "../vaults/NoLossVault.sol";
import {DirectVault} from "../vaults/DirectVault.sol";
import {GaiaCharityRegistry} from "../access/GaiaCharityRegistry.sol";
import {GaiaAgentRegistry} from "../access/GaiaAgentRegistry.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GaiaProposalManager
 * @dev Manages dual-mode donation proposals with rich metadata for 3D Globe visualization.
 * Integrates 2-tier Charity Registry for permissioned acceptance.
 */
contract GaiaProposalManager is Ownable {
    using SafeERC20 for IERC20;

    struct Proposal {
        address proposer;
        uint256 charityId; // ID from GaiaCharityRegistry
        IERC20 asset;
        
        // Frontend Metadata
        string title;
        string metadata; // IPFS CID
        int24 lat;       // Scaled by 10^4 (e.g., 25.1234 -> 251234)
        int24 lng;
        uint8 category;  // e.g., 1=Earthquake, 2=Flood, 3=Conflict
        
        uint256 expiry;
        bool accepted;
        bool isVerified; // AI Agent Verification

        // Dual-Mode Tracking
        uint256 totalDirect;
        uint256 totalNoLoss;
        address directVault;
        address noLossVault;
    }

    struct UserBalance {
        uint256 directAmount;
        uint256 noLossAmount;
    }

    uint256 public nextProposalId;
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => UserBalance)) public userBalances;

    GaiaCharityRegistry public charityRegistry;
    GaiaAgentRegistry public agentRegistry;

    // Rich Events for 3D Globe
    event ProposalCreated(
        uint256 indexed proposalId, 
        string title, 
        uint256 indexed charityId, 
        int24 lat, 
        int24 lng, 
        uint8 category
    );
    event FundsDeposited(uint256 indexed proposalId, address indexed user, uint256 amount, bool isNoLoss);
    event FundsWithdrawn(uint256 indexed proposalId, address indexed user, uint256 directAmount, uint256 noLossAmount);
    event ProposalAccepted(uint256 indexed proposalId, address directVault, address noLossVault);
    event ProposalVerified(uint256 indexed proposalId, address indexed agent);

    constructor(address _owner, address _charityRegistry, address _agentRegistry) Ownable(_owner) {
        charityRegistry = GaiaCharityRegistry(_charityRegistry);
        agentRegistry = GaiaAgentRegistry(_agentRegistry);
    }

    /**
     * @dev Create a new crisis donation proposal with rich metadata.
     */
    function createProposal(
        uint256 _charityId,
        IERC20 _asset,
        string calldata _title,
        string calldata _metadata,
        int24 _lat,
        int24 _lng,
        uint8 _category,
        uint256 _duration
    ) external returns (uint256) {
        require(_duration > 0, "Duration must be positive");
        
        // Validate charity exists (active)
        (,, bool isActive) = charityRegistry.getCharity(_charityId);
        require(isActive, "Invalid or inactive charity");

        uint256 proposalId = nextProposalId++;
        proposals[proposalId] = Proposal({
            proposer: msg.sender,
            charityId: _charityId,
            asset: _asset,
            title: _title,
            metadata: _metadata,
            lat: _lat,
            lng: _lng,
            category: _category,
            expiry: block.timestamp + _duration,
            accepted: false,
            isVerified: false,
            totalDirect: 0,
            totalNoLoss: 0,
            directVault: address(0),
            noLossVault: address(0)
        });

        emit ProposalCreated(proposalId, _title, _charityId, _lat, _lng, _category);
        return proposalId;
    }

    /**
     * @dev Deposit to a proposal.
     */
    function depositToProposal(uint256 _proposalId, uint256 _amount, bool _isNoLoss) external {
        Proposal storage p = proposals[_proposalId];
        require(!p.accepted, "Proposal already accepted");
        require(block.timestamp < p.expiry, "Proposal expired");

        p.asset.safeTransferFrom(msg.sender, address(this), _amount);
        
        if (_isNoLoss) {
            userBalances[_proposalId][msg.sender].noLossAmount += _amount;
            p.totalNoLoss += _amount;
        } else {
            userBalances[_proposalId][msg.sender].directAmount += _amount;
            p.totalDirect += _amount;
        }

        emit FundsDeposited(_proposalId, msg.sender, _amount, _isNoLoss);
    }

    /**
     * @dev Institution accepts the proposal. Restricted to Members of the specific Charity.
     */
    function acceptProposal(uint256 _proposalId) external {
        Proposal storage p = proposals[_proposalId];
        require(!p.accepted, "Already accepted");
        require(block.timestamp < p.expiry, "Proposal expired");

        // Permission Check: Caller must be a member of the Proposal's Target Charity
        require(charityRegistry.isMember(p.charityId, msg.sender), "Caller not authorized for this charity");

        p.accepted = true;

        // Get Charity Admin address for Vault ownership/recipient
        (, address charityAdmin,) = charityRegistry.getCharity(p.charityId);

        // 1. Handle Direct Donation
        if (p.totalDirect > 0) {
            DirectVault dVault = new DirectVault(p.asset, charityAdmin, owner());
            // Add charity admin to whitelist automatically? 
            // Better: The charity address itself IS the admin, so it's handled by DirectVault check.
            p.directVault = address(dVault);
            p.asset.approve(address(dVault), p.totalDirect);
            dVault.deposit(p.totalDirect);
        }

        // 2. Handle No-Loss Donation
        if (p.totalNoLoss > 0) {
            NoLossVault nVault = new NoLossVault(p.asset, charityAdmin, owner());
            p.noLossVault = address(nVault);
            p.asset.approve(address(nVault), p.totalNoLoss);
            nVault.deposit(p.totalNoLoss);
        }

        emit ProposalAccepted(_proposalId, p.directVault, p.noLossVault);
    }
    
    /**
     * @dev Authorized AI Agent validates a proposal.
     */
    function verifyProposal(uint256 _proposalId) external {
        require(agentRegistry.isAuthorized(msg.sender), "Not authorized agent");
        Proposal storage p = proposals[_proposalId];
        p.isVerified = true;
        emit ProposalVerified(_proposalId, msg.sender);
    }

    /**
     * @dev Anytime withdrawal for donors.
     */
    function withdrawFromProposal(uint256 _proposalId) external {
        Proposal storage p = proposals[_proposalId];
        require(!p.accepted, "Proposal already accepted");

        UserBalance storage balance = userBalances[_proposalId][msg.sender];
        uint256 directAmt = balance.directAmount;
        uint256 noLossAmt = balance.noLossAmount;
        uint256 total = directAmt + noLossAmt;
        
        require(total > 0, "No deposit to withdraw");

        balance.directAmount = 0;
        balance.noLossAmount = 0;
        p.totalDirect -= directAmt;
        p.totalNoLoss -= noLossAmt;
        
        p.asset.safeTransfer(msg.sender, total);

        emit FundsWithdrawn(_proposalId, msg.sender, directAmt, noLossAmt);
    }
}
