import { useMemo } from 'react';
import { useReadContract } from 'wagmi';
import { foundry } from 'wagmi/chains';
import { GAIA_PROPOSAL_MANAGER_ABI } from '@/lib/abis';
import { PROPOSAL_MANAGER_ADDRESS } from '@/lib/constants';
import { CrisisPoint } from '@/lib/mockData';
import { PROPOSAL_DESCRIPTIONS } from '@/lib/descriptions';

export function useProposals() {
    // Fetch all proposals in one bulk call
    const { data: allProposals, error, isLoading, isError } = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'getAllProposals',
        chainId: foundry.id,
    });

    // Debug logging
    console.log('[useProposals] Loading:', isLoading, 'Error:', isError, error?.message);
    console.log('[useProposals] Raw data:', allProposals ? `${(allProposals as any[]).length} proposals` : 'null');

    // Transform to CrisisPoint
    const points = useMemo(() => {
        if (!allProposals) {
            console.log('[useProposals] No proposals data yet');
            return [];
        }

        console.log('[useProposals] Transforming', (allProposals as any[]).length, 'proposals');
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
