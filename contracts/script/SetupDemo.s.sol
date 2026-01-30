// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {GaiaAgentRegistry} from "../src/access/GaiaAgentRegistry.sol";
import {GaiaProposalManager} from "../src/proposals/GaiaProposalManager.sol";
import {GaiaCharityRegistry} from "../src/access/GaiaCharityRegistry.sol";
import {MockERC20} from "../test/mocks/MockERC20.sol";

contract SetupDemo is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envOr("WALLET_PRIVATE_KEY", uint256(0));
        address owner = vm.envOr("OWNER_ADDRESS", msg.sender);

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Mocks
        MockERC20 token = new MockERC20("USDC", "USDC");
        console2.log("MockUSDC deployed at:", address(token));

        // 2. Deploy Registries
        GaiaAgentRegistry agentRegistry = new GaiaAgentRegistry();
        GaiaCharityRegistry charityRegistry = new GaiaCharityRegistry(owner);
        console2.log("GaiaAgentRegistry:", address(agentRegistry));
        console2.log("GaiaCharityRegistry:", address(charityRegistry));

        // 3. Deploy Manager
        GaiaProposalManager manager = new GaiaProposalManager(owner, address(charityRegistry), address(agentRegistry));
        console2.log("GaiaProposalManager:", address(manager));

        // 4. Seed Data: Register Charities
        charityRegistry.registerCharity(owner, "Red Cross International"); // ID 1
        charityRegistry.registerCharity(owner, "UNICEF"); // ID 2
        console2.log("Seeded Charities: Red Cross (1), UNICEF (2)");

        // Seed Data: Create Real-world Proposals matching backend_data/data.json
        
        // 1. Turkey-Syria Earthquake Relief (CRITICAL)
        // Lat: 37.166 -> 371660, Lng: 38.795 -> 387950
        manager.createProposal(1, token, "Turkey-Syria Earthquake Relief", "ipfs://turkey", 371660, 387950, 1, 30 days);

        // 2. Ukraine Humanitarian Crisis (CRITICAL)
        // Lat: 50.450 -> 504500, Lng: 30.523 -> 305230
        manager.createProposal(2, token, "Ukraine Humanitarian Crisis", "ipfs://ukraine", 504500, 305230, 3, 30 days);

        // 3. Gaza Humanitarian Aid (CRITICAL)
        // Lat: 31.500 -> 315000, Lng: 34.466 -> 344660
        manager.createProposal(2, token, "Gaza Humanitarian Aid", "ipfs://gaza", 315000, 344660, 3, 30 days);

        // 4. Sudan Emergency Famine Relief (CRITICAL)
        // Lat: 15.500 -> 155000, Lng: 32.559 -> 325590
        manager.createProposal(1, token, "Sudan Emergency Famine Relief", "ipfs://sudan", 155000, 325590, 4, 30 days);

        // 5. Yemen Humanitarian Crisis (HIGH)
        // Lat: 15.369 -> 153690, Lng: 44.191 -> 441910
        manager.createProposal(1, token, "Yemen Humanitarian Crisis", "ipfs://yemen", 153690, 441910, 3, 30 days);

        // 6. Libya Derna Flood Recovery (HIGH)
        // Lat: 32.767 -> 327670, Lng: 22.636 -> 226360
        manager.createProposal(2, token, "Libya Derna Flood Recovery", "ipfs://libya", 327670, 226360, 2, 30 days);

        // 7. Morocco Earthquake Reconstruction (HIGH)
        // Lat: 31.629 -> 316290, Lng: -7.981 -> -79810
        manager.createProposal(1, token, "Morocco Earthquake Reconstruction", "ipfs://morocco", 316290, -79810, 1, 30 days);

        // 8. Afghanistan Earthquake (Herat) (HIGH)
        // Lat: 34.352 -> 343520, Lng: 62.204 -> 622040
        manager.createProposal(1, token, "Herat Afghanistan Earthquake", "ipfs://afghanistan", 343520, 622040, 1, 30 days);

        // 9. Pakistan Flood Recovery (MODERATE)
        // Lat: 30.375 -> 303750, Lng: 69.345 -> 693450
        manager.createProposal(2, token, "Pakistan Flood Recovery", "ipfs://pakistan", 303750, 693450, 2, 30 days);

        // 10. Horn of Africa Drought (CRITICAL)
        // Lat: 5.152 -> 51520, Lng: 46.199 -> 461990
        manager.createProposal(2, token, "Horn of Africa Drought", "ipfs://somalia", 51520, 461990, 4, 30 days);

        console2.log("Seeded 10 Real-world Proposals from backend_data");

        vm.stopBroadcast();
    }
}
