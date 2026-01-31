// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {GaiaProposalManager} from "../src/proposals/GaiaProposalManager.sol";
import {GaiaCharityRegistry} from "../src/access/GaiaCharityRegistry.sol";
import {MockERC20} from "../test/mocks/MockERC20.sol";

contract SetupDemo is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envOr("WALLET_PRIVATE_KEY", uint256(0));
        
        if (deployerPrivateKey != 0) {
            vm.startBroadcast(deployerPrivateKey);
        } else {
            vm.startBroadcast();
        }

        address owner = vm.envOr("OWNER_ADDRESS", msg.sender);

        // 1. Deploy Mocks
        MockERC20 token = new MockERC20("USDC", "USDC");
        console2.log("MockUSDC deployed at:", address(token));

        // 2. Deploy Registries
        GaiaCharityRegistry charityRegistry = new GaiaCharityRegistry(owner);
        console2.log("GaiaCharityRegistry:", address(charityRegistry));

        // 3. Deploy Manager
        GaiaProposalManager manager = new GaiaProposalManager(owner, address(charityRegistry));
        console2.log("GaiaProposalManager:", address(manager));

        // 4. Seed Data: Register Charities
        address charityAdmin1 = owner;
        address charityAdmin2 = address(0x2);
        
        charityRegistry.registerCharity(charityAdmin1, "Red Cross International"); // ID 1
        charityRegistry.registerCharity(charityAdmin2, "UNICEF"); // ID 2
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

        // 11. Tigray Post-Conflict Recovery (HIGH)
        // Lat: 14.032 -> 140320, Lng: 38.316 -> 383160
        manager.createProposal(2, token, "Tigray Post-Conflict Recovery", "ipfs://tigray", 140320, 383160, 3, 30 days);

        // 12. Maui Wildfire Restoration (MODERATE)
        // Lat: 20.885 -> 208850, Lng: -156.678 -> -1566780
        manager.createProposal(1, token, "Maui Wildfire Restoration", "ipfs://maui", 208850, -1566780, 5, 30 days);

        // 13. Canadian Wildfire Response (HIGH)
        // Lat: 55.000 -> 550000, Lng: -100.000 -> -1000000
        manager.createProposal(2, token, "Canadian Wildfire Response", "ipfs://canada", 550000, -1000000, 5, 30 days);

        // 14. Amazon Rainforest Conservation (HIGH)
        // Lat: -3.465 -> -34650, Lng: -62.215 -> -622150
        manager.createProposal(1, token, "Amazon Rainforest Conservation", "ipfs://amazon", -34650, -622150, 6, 30 days);

        // 15. Australia Bushfire Preparedness (MODERATE)
        // Lat: -33.868 -> -338680, Lng: 151.209 -> 1512090
        manager.createProposal(2, token, "Australia Bushfire Preparedness", "ipfs://australia", -338680, 1512090, 5, 30 days);

        // 16. Japan Seismic Risk Prep (MODERATE)
        // Lat: 35.676 -> 356760, Lng: 139.650 -> 1396500
        manager.createProposal(1, token, "Japan Seismic Risk Prep", "ipfs://japan", 356760, 1396500, 1, 30 days);

        // 17. California Water Resilience (MODERATE)
        // Lat: 36.778 -> 367780, Lng: -119.417 -> -1194170
        manager.createProposal(2, token, "California Water Resilience", "ipfs://california", 367780, -1194170, 4, 30 days);

        // 18. Bangladesh Cyclone Shelters (HIGH)
        // Lat: 23.685 -> 236850, Lng: 90.356 -> 903560
        manager.createProposal(1, token, "Bangladesh Cyclone Shelters", "ipfs://bangladesh", 236850, 903560, 2, 30 days);

        // 19. Haiti Medical & Food Aid (CRITICAL)
        // Lat: 18.594 -> 185940, Lng: -72.307 -> -723070
        manager.createProposal(2, token, "Haiti Medical & Food Aid", "ipfs://haiti", 185940, -723070, 3, 30 days);

        // 20. Venezuelan Migrant Support (HIGH)
        // Lat: 6.423 -> 64230, Lng: -66.589 -> -665890
        manager.createProposal(1, token, "Venezuelan Migrant Support", "ipfs://venezuela", 64230, -665890, 3, 30 days);

        // 21. Philippines Super Typhoon Rai Relief (HIGH)
        // Lat: 14.599 -> 145990, Lng: 120.984 -> 1209840
        manager.createProposal(2, token, "Philippines Typhoon Relief", "ipfs://philippines", 145990, 1209840, 2, 30 days);

        // 22. Mt. Semeru Eruption Relief (HIGH)
        // Lat: -8.108 -> -81080, Lng: 112.922 -> 1129220
        manager.createProposal(1, token, "Mt. Semeru Eruption Relief", "ipfs://indonesia", -81080, 1129220, 1, 30 days);

        // 23. Iceland Grindavik Housing (MODERATE)
        // Lat: 63.842 -> 638420, Lng: -22.438 -> -224380
        manager.createProposal(2, token, "Iceland Grindavik Housing", "ipfs://iceland", 638420, -224380, 1, 30 days);

        // 24. Chile Valparaiso Fire Recovery (HIGH)
        // Lat: -33.047 -> -330470, Lng: -71.612 -> -716120
        manager.createProposal(1, token, "Chile Valparaiso Fire Recovery", "ipfs://chile", -330470, -716120, 5, 30 days);

        // 25. Myanmar Emergency Medical Aid (CRITICAL)
        // Lat: 21.916 -> 219160, Lng: 95.956 -> 959560
        manager.createProposal(2, token, "Myanmar Emergency Medical Aid", "ipfs://myanmar", 219160, 959560, 3, 30 days);

        console2.log("Seeded 25 Real-world Proposals from backend_data");

        vm.stopBroadcast();
    }
}
