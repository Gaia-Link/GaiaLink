import { useMemo } from 'react';
import { useReadContract, useReadContracts } from 'wagmi';
import { GAIA_PROPOSAL_MANAGER_ABI, GAIA_CHARITY_REGISTRY_ABI } from '@/lib/abis';
import { PROPOSAL_MANAGER_ADDRESS, MOCK_IPFS_GATEWAY } from '@/lib/constants';
import { CrisisPoint } from '@/lib/mockData';

export function useProposals() {
    // 1. Get total count
    const { data: nextProposalId } = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'nextProposalId',
    });

    // 2. Prepare calls for all proposals
    const count = nextProposalId ? Number(nextProposalId) : 0;
    const proposalCalls = useMemo(() => Array.from({ length: count }, (_, i) => ({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'proposals',
        args: [BigInt(i)]
    })), [count]);

    const { data: proposalsData } = useReadContracts({
        contracts: proposalCalls as any,
    });

    // 3. Prepare calls for charities
    const charityRegistryAddress = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'charityRegistry',
    });

    const charityCalls = useMemo(() => proposalsData?.map((p) => {
        if (!p.result) return null;
        const charityId = (p.result as any)[1]; // index 1 is charityId
        return {
            address: charityRegistryAddress.data,
            abi: GAIA_CHARITY_REGISTRY_ABI,
            functionName: 'getCharity',
            args: [charityId]
        };
    }).filter(Boolean), [proposalsData, charityRegistryAddress.data]);

    const { data: charitiesData } = useReadContracts({
        contracts: charityCalls as any,
        query: {
            enabled: !!charityRegistryAddress.data && !!proposalsData
        }
    });

    // 4. Transform to CrisisPoint
    // Note: This relies on hooks running in stable order/count which is true here as we rebuild list on render
    // but in a real app might need more stable query management.

    const points = useMemo(() => {
        if (!proposalsData) return [];

        return proposalsData.map((p, i) => {
            if (!p.result) return null;
            // Result: [proposer, charityId, asset, title, metadata, lat, lng, category, expiry, accepted, ...]
            const r = p.result as any;
            const title = r[3];
            const metadataCid = r[4];
            const lat = Number(r[5]) / 10000;
            const lng = Number(r[6]) / 10000;

            // Mock IPFS Resolve
            const description = MOCK_IPFS_GATEWAY[metadataCid]?.description || "Loading description from IPFS...";

            return {
                id: i.toString(),
                lat,
                lng,
                intensity: 0.8, // Hardcoded for now
                label: title,
                type: 'crisis' as const,
                description,
                // On-Chain status
                accepted: r[9] as boolean,
                directVault: r[12] as `0x${string}`,
                noLossVault: r[13] as `0x${string}`,
            };
        }).filter(Boolean);
    }, [proposalsData]);

    return points as (CrisisPoint & { accepted: boolean; directVault: `0x${string}`; noLossVault: `0x${string}` })[];
}
