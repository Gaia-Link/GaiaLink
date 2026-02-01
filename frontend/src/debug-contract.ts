
import { createPublicClient, http, parseAbiItem, createWalletClient } from 'viem';
import { foundry } from 'viem/chains';
import { CONTRACTS } from './lib/contracts';
import { GAIA_PROPOSAL_MANAGER_ABI, GAIA_CHARITY_REGISTRY_ABI } from './lib/abis';

const client = createPublicClient({
    chain: foundry,
    transport: http('http://127.0.0.1:8545')
});

async function main() {
    console.log("--- Debugging Contracts ---");
    console.log("Registry:", CONTRACTS.GaiaCharityRegistry);
    console.log("Manager:", CONTRACTS.GaiaProposalManager);

    // 1. Check Charity 1 Status
    try {
        const data = await client.readContract({
            address: CONTRACTS.GaiaCharityRegistry as `0x${string}`,
            abi: GAIA_CHARITY_REGISTRY_ABI,
            functionName: 'getCharity',
            args: [1n]
        });
        console.log("Charity 1:", data);
    } catch (e: any) {
        console.log("Charity 1 Failed:", e.message?.split('\n')[0]);
    }

    // 2. Simulate Create Proposal with Random Account
    console.log("--- Simulating Transaction (Random Account) ---");
    const account = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; // Anvil Account #1

    try {
        const { request } = await client.simulateContract({
            account,
            address: CONTRACTS.GaiaProposalManager as `0x${string}`,
            abi: GAIA_PROPOSAL_MANAGER_ABI,
            functionName: 'createProposal',
            args: [
                1n, // Charity 1 (Valid)
                CONTRACTS.MockERC20 as `0x${string}`,
                "Test Proposal Valid",
                "{}",
                300000,
                -700000,
                1,
                BigInt(30 * 24 * 60 * 60)
            ],
            gas: 3000000n
        });
        console.log("Simulation (Charity 1) SUCCESS.");
    } catch (e: any) {
        console.error("Simulation (Charity 1) FAILED:", e.message?.split('\n')[0]);
    }

    // 3. Simulate Invalid Charity (0)
    try {
        await client.simulateContract({
            account,
            address: CONTRACTS.GaiaProposalManager as `0x${string}`,
            abi: GAIA_PROPOSAL_MANAGER_ABI,
            functionName: 'createProposal',
            args: [
                0n, // Charity 0 (Invalid)
                CONTRACTS.MockERC20 as `0x${string}`,
                "Test Proposal Invalid",
                "{}",
                300000,
                -700000,
                1,
                BigInt(30 * 24 * 60 * 60)
            ],
        });
        console.log("Simulation (Charity 0) UNEXPECTEDLY PROCEEDED.");
    } catch (e: any) {
        console.log("Simulation (Charity 0) FAILED (Expected):", e.message?.split('\n')[0]);
    }
}

main();
