import { useReadContract } from 'wagmi';
import { foundry } from 'wagmi/chains';
import { GAIA_CHARITY_REGISTRY_ABI } from '@/lib/abis';
import { CONTRACTS } from '@/lib/contracts';

export function useCharity(charityId?: number) {
    const { data: charityInfo, isLoading, isError } = useReadContract({
        address: CONTRACTS.GaiaCharityRegistry as `0x${string}`,
        abi: GAIA_CHARITY_REGISTRY_ABI,
        functionName: 'getCharity',
        args: charityId ? [BigInt(charityId)] : undefined,
        chainId: foundry.id,
        query: {
            enabled: !!charityId,
        }
    });

    return {
        name: charityInfo ? (charityInfo as any)[0] as string : undefined,
        admin: charityInfo ? (charityInfo as any)[1] as string : undefined,
        isActive: charityInfo ? (charityInfo as any)[2] as boolean : false,
        isLoading,
        isError
    };
}
