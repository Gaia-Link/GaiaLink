import { useMemo } from 'react';
import { useReadContract, useReadContracts } from 'wagmi';
import { GAIA_PROPOSAL_MANAGER_ABI, GAIA_CHARITY_REGISTRY_ABI } from '@/lib/abis';
import { PROPOSAL_MANAGER_ADDRESS } from '@/lib/constants';
import { CrisisPoint } from '@/lib/mockData';
import { PROPOSAL_DESCRIPTIONS } from '@/lib/descriptions';

export function useProposals() {
    // 1. Fetch all proposals in one bulk call
    const { data: allProposals, refetch } = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'getAllProposals',
        query: {
            refetchInterval: 5000, // Refetch every 5 seconds to pick up new proposals
        }
    });

    // 2. Prepare calls for charities (keeping this as is for now)
    const charityRegistryAddress = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'charityRegistry',
    });

    // We can just iterate over allProposals to get charityIds
    const charityCalls = useMemo(() => {
        if (!allProposals) return [];
        return (allProposals as any[]).map((p) => ({
            address: charityRegistryAddress.data,
            abi: GAIA_CHARITY_REGISTRY_ABI,
            functionName: 'getCharity',
            args: [p.charityId]
        }));
    }, [allProposals, charityRegistryAddress.data]);

    const { data: charitiesData } = useReadContracts({
        contracts: charityCalls as any,
        query: {
            enabled: !!charityRegistryAddress.data && !!allProposals
        }
    });

    // 3. Transform to CrisisPoint
    const points = useMemo(() => {
        if (!allProposals) return [];

        return (allProposals as any[]).map((p, i) => {
            const title = p.title;
            const metadataCid = p.metadata;
            const lat = Number(p.lat) / 10000;
            const lng = Number(p.lng) / 10000;

            const description = PROPOSAL_DESCRIPTIONS[title] || "Detailed impact report pending verification.";

            let type: 'crisis' | 'voice' | 'node' | 'warning' = 'crisis';
            const cat = Number(p.category);

            if (cat === 4) type = 'warning';
            if (cat === 6) type = 'node';
            if (cat === 5) type = 'warning';

            // Funding Logic
            // Note: We use 18 decimals for local MockERC20
            const raised = Number((p.totalDirect || 0n) + (p.totalNoLoss || 0n));
            const hasVault = p.directVault !== "0x0000000000000000000000000000000000000000" || p.noLossVault !== "0x0000000000000000000000000000000000000000";

            return {
                id: i.toString(),
                lat,
                lng,
                intensity: 0.8,
                label: title,
                type,
                description,
                raised,
                hasVault,
                // On-Chain status
                accepted: p.accepted,
                directVault: p.directVault as `0x${string}`,
                noLossVault: p.noLossVault as `0x${string}`,
                asset: p.asset as `0x${string}`,
            };
        });
    }, [allProposals]);

    return points as (CrisisPoint & { accepted: boolean; directVault: `0x${string}`; noLossVault: `0x${string}`; asset: `0x${string}` })[];
}
