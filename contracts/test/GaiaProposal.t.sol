// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console2} from "forge-std/Test.sol";
import {GaiaProposalManager} from "../src/proposals/GaiaProposalManager.sol";
import {NoLossVault} from "../src/vaults/NoLossVault.sol";
import {DirectVault} from "../src/vaults/DirectVault.sol";
import {GaiaCharityRegistry} from "../src/access/GaiaCharityRegistry.sol";
import {GaiaAgentRegistry} from "../src/access/GaiaAgentRegistry.sol";
import {MockERC20} from "./mocks/MockERC20.sol";

contract GaiaProposalTest is Test {
    GaiaProposalManager public manager;
    GaiaCharityRegistry public charityRegistry;
    GaiaAgentRegistry public agentRegistry;
    MockERC20 public token;
    
    address public owner = address(1);
    address public proposer = address(2);
    address public charityAdmin = address(3); // Red Cross Admin
    address public charityMember = address(10); // Red Cross Worker
    address public donor1 = address(4);
    address public donor2 = address(5);
    address public agent = address(6);

    uint256 public charityId;

    function setUp() public {
        vm.startPrank(owner);
        token = new MockERC20("USD Coin", "USDC");
        
        charityRegistry = new GaiaCharityRegistry(owner);
        agentRegistry = new GaiaAgentRegistry();
        manager = new GaiaProposalManager(owner, address(charityRegistry), address(agentRegistry));
        
        // 1. Register Charity (Tier 1)
        charityRegistry.registerCharity(charityAdmin, "Red Cross");
        charityId = 1;

        // 2. Authorize Agent
        agentRegistry.authorizeAgent(agent);
        
        vm.stopPrank();

        // 3. Charity adds Member (Tier 2)
        vm.prank(charityAdmin);
        charityRegistry.addMember(charityMember);

        token.mint(donor1, 1000e18);
        token.mint(donor2, 1000e18);
    }

    function testDualModeProposalFlow() public {
        // 1. Create Proposal with Rich Metadata
        vm.prank(proposer);
        // lat: 25.0, lng: 121.0, category: 1 (Earthquake)
        uint256 pid = manager.createProposal(charityId, token, "Taiwan Earthquake Relief", "ipfs://QmHash", 250000, 1210000, 1, 1 days);

        // 2. Verified by Agent
        vm.prank(agent);
        manager.verifyProposal(pid);
        // Unpack: (proposer, charityId, asset, title, metadata, lat, lng, category, expiry, accepted, isVerified, totalDirect, totalNoLoss, dVault, nVault)
        (,,,,,,,,,, bool isVerified,,,,) = manager.proposals(pid);
        assertTrue(isVerified);

        // 3. Donors Deposit
        vm.startPrank(donor1);
        token.approve(address(manager), 100e18);
        manager.depositToProposal(pid, 100e18, false); // Direct
        vm.stopPrank();

        vm.startPrank(donor2);
        token.approve(address(manager), 500e18);
        manager.depositToProposal(pid, 500e18, true); // No-Loss
        vm.stopPrank();

        // 4. Unauthorized Acceptance (Fail)
        vm.startPrank(proposer);
        vm.expectRevert("Caller not authorized for this charity");
        manager.acceptProposal(pid);
        vm.stopPrank();

        // 5. Authorized Acceptance (Member)
        vm.prank(charityMember);
        manager.acceptProposal(pid);

        // 6. Verify Vaults
        (,,,,,,,,,,,,, address dVault, address nVault) = manager.proposals(pid);
        
        // Verify Direct Vault balance
        assertEq(token.balanceOf(dVault), 100e18);
        
        // Verify Charity Admin can withdraw from Direct Vault
        // Note: DirectVault checks owner which is manager owner, but funds are for charityAdmin?
        // Wait, current DirectVault implementation expects charityAddress to withdraw.
        // In acceptProposal, we passed `charityAdmin` as the `_charity` argument to DirectVault.
        
        vm.prank(charityAdmin);
        DirectVault(dVault).withdraw(100e18);
        assertEq(token.balanceOf(charityAdmin), 100e18);
    }

    function testAnytimeWithdrawal() public {
        vm.prank(proposer);
        uint256 pid = manager.createProposal(charityId, token, "Flex Refund", "ipfs://QmFlex", 0, 0, 1, 1 hours);

        // Deposit
        vm.startPrank(donor1);
        token.approve(address(manager), 50e18);
        manager.depositToProposal(pid, 50e18, false);
        vm.stopPrank();

        // Withdraw ANYTIME
        vm.prank(donor1);
        manager.withdrawFromProposal(pid);
        
        assertEq(token.balanceOf(donor1), 1000e18);
    }
}
