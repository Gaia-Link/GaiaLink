// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {GaiaAgentRegistry} from "../src/access/GaiaAgentRegistry.sol";
import {GaiaProposalManager} from "../src/proposals/GaiaProposalManager.sol";
import {GaiaCharityRegistry} from "../src/access/GaiaCharityRegistry.sol";

contract DeployGaia is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envOr("WALLET_PRIVATE_KEY", uint256(0));
        address owner = vm.envOr("OWNER_ADDRESS", msg.sender);

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Agent Registry
        GaiaAgentRegistry agentRegistry = new GaiaAgentRegistry();
        console2.log("GaiaAgentRegistry deployed at:", address(agentRegistry));

        // 2. Deploy Charity Registry
        GaiaCharityRegistry charityRegistry = new GaiaCharityRegistry(owner);
        console2.log("GaiaCharityRegistry deployed at:", address(charityRegistry));

        // 3. Deploy Proposal Manager
        GaiaProposalManager manager = new GaiaProposalManager(owner, address(charityRegistry), address(agentRegistry));
        console2.log("GaiaProposalManager deployed at:", address(manager));

        vm.stopBroadcast();
    }
}
