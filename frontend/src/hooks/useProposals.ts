import { useMemo } from 'react';
import { useReadContract, useReadContracts } from 'wagmi';
import { GAIA_PROPOSAL_MANAGER_ABI, GAIA_CHARITY_REGISTRY_ABI } from '@/lib/abis';
import { PROPOSAL_MANAGER_ADDRESS } from '@/lib/constants';
import { CrisisPoint } from '@/lib/mockData';
import { PROPOSAL_DESCRIPTIONS } from '@/lib/descriptions';

export function useProposals() {
    // 1. Fetch all proposals in one bulk call
    const { data: allProposals } = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'getAllProposals',
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
            // Struct: { proposer, charityId, asset, title, metadata, lat, lng, category, expiry, accepted, ... }
            const title = p.title;
            const metadataCid = p.metadata;
            const lat = Number(p.lat) / 10000;
            const lng = Number(p.lng) / 10000;

            // Mock IPFS Resolve -> Real Descriptions
            const description = PROPOSAL_DESCRIPTIONS[title] || "Detailed impact report pending verification.";

            // Map category to type for visual diversity (Demo Logic)
            // 1=Earthquake, 2=Flood, 3=Conflict, 4=Drought, 5=Fire, 6=Deforestation
            let type: 'crisis' | 'voice' | 'node' | 'warning' = 'crisis';
            const cat = Number(p.category);

            if (cat === 4) type = 'warning'; // Drought -> Warning (Yellow)
            if (cat === 6) type = 'node';    // Conservation -> Node (Blue)
            if (cat === 5) type = 'warning'; // Fire -> Warning (Yellow)

            return {
                id: i.toString(),
                lat,
                lng,
                intensity: 0.8,
                label: title,
                type,
                description,
                // On-Chain status
                accepted: p.accepted,
                directVault: p.directVault,
                noLossVault: p.noLossVault,
                asset: p.asset,
            };
        });
    }, [allProposals]);

    return points as (CrisisPoint & { accepted: boolean; directVault: `0x${string}`; noLossVault: `0x${string}`; asset: `0x${string}` })[];
}
