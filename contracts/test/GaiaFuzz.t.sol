// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console2} from "forge-std/Test.sol";
import {GaiaProposalManager} from "../src/proposals/GaiaProposalManager.sol";
import {GaiaCharityRegistry} from "../src/access/GaiaCharityRegistry.sol";
import {GaiaAgentRegistry} from "../src/access/GaiaAgentRegistry.sol";
import {DirectVault} from "../src/vaults/DirectVault.sol";
import {MockERC20} from "./mocks/MockERC20.sol";

contract GaiaFuzzTest is Test {
    GaiaProposalManager public manager;
    GaiaCharityRegistry public charityRegistry;
    GaiaAgentRegistry public agentRegistry;
    MockERC20 public token;
    
    address public owner = address(1);
    address public proposer = address(2);
    address public charityAdmin = address(3);
    address public charityMember = address(4);

    uint256 public charityId;

    function setUp() public {
        vm.startPrank(owner);
        token = new MockERC20("USD Coin", "USDC");
        
        charityRegistry = new GaiaCharityRegistry(owner);
        agentRegistry = new GaiaAgentRegistry();
        manager = new GaiaProposalManager(owner, address(charityRegistry), address(agentRegistry));
        
        charityRegistry.registerCharity(charityAdmin, "Red Cross");
        charityId = 1;
        
        vm.stopPrank();

        vm.prank(charityAdmin);
        charityRegistry.addMember(charityMember);
    }

    // Fuzz Test 1: Random Deposit Amounts
    function testFuzz_Deposit(uint96 amount, bool isNoLoss) public {
        vm.assume(amount > 0);
        
        vm.prank(proposer);
        uint256 pid = manager.createProposal(charityId, token, "Fuzz Proposal", "ipfs://", 0, 0, 1, 1 days);

        address donor = address(0x123);
        token.mint(donor, uint256(amount));
        
        vm.startPrank(donor);
        token.approve(address(manager), amount);
        manager.depositToProposal(pid, amount, isNoLoss);
        vm.stopPrank();

        (,,,,,,,,,,, uint256 totalDirect, uint256 totalNoLoss,,) = manager.proposals(pid);

        if (isNoLoss) {
            assertEq(totalNoLoss, amount);
            assertEq(totalDirect, 0);
        } else {
            assertEq(totalDirect, amount);
            assertEq(totalNoLoss, 0);
        }
    }

    // Fuzz Test 2: Proposal Creation Metadata
    function testFuzz_CreateProposal(int24 lat, int24 lng, uint8 category, uint32 duration) public {
        vm.assume(duration > 0);
        
        vm.prank(proposer);
        uint256 pid = manager.createProposal(charityId, token, "Geo Proposal", "ipfs://", lat, lng, category, duration);

        (,,,,, int24 rLat, int24 rLng, uint8 rCat, uint256 rExpiry,,,,,,) = manager.proposals(pid);
        
        assertEq(rLat, lat);
        assertEq(rLng, lng);
        assertEq(rCat, category);
        assertEq(rExpiry, block.timestamp + duration);
    }

    // Fuzz Test 3: Withdrawal Integrity
    function testFuzz_Withdrawal(uint96 amount) public {
        vm.assume(amount > 0);
        
        vm.prank(proposer);
        uint256 pid = manager.createProposal(charityId, token, "Exit Proposal", "ipfs://", 0, 0, 1, 1 days);

        address donor = address(0x999);
        token.mint(donor, amount);

        vm.startPrank(donor);
        token.approve(address(manager), amount);
        manager.depositToProposal(pid, amount, false); // Direct mode
        vm.stopPrank();

        // Withdraw
        vm.prank(donor);
        manager.withdrawFromProposal(pid);

        assertEq(token.balanceOf(donor), amount);
        
        // Proposal total should be 0
        (,,,,,,,,,,, uint256 totalDirect, uint256 totalNoLoss,,) = manager.proposals(pid);
        assertEq(totalDirect, 0);
        assertEq(totalNoLoss, 0);
    }
}
