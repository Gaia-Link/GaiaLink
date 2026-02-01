import { useState, useEffect } from 'react';
import { CrisisPoint } from '@/lib/mockData';

export function useNewsPoints() {
    const [newsPoints, setNewsPoints] = useState<CrisisPoint[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function fetchCrises() {
            try {
                const response = await fetch('http://localhost:8000/api/crises');
                if (!response.ok) throw new Error('Failed to fetch crises');
                const data = await response.json();

                const crises = data.crises || [];
                console.log('[useNewsPoints] crises count:', crises.length);
                const points: CrisisPoint[] = crises.map((c: any) => ({
                    id: `news-${c.id}`,
                    lat: c.location.lat,
                    lng: c.location.lng,
                    intensity: 0.6, // News points have lower intensity
                    label: c.title,
                    type: 'crisis',
                    description: c.description,
                    hasVault: c.vaults && c.vaults.length > 0,
                    isBackend: true,
                    // If it has a vault in data.json, we might want to show it as "active" 
                    // but usually we want to prefer on-chain data.
                }));

                setNewsPoints(points);
            } catch (error) {
                console.error('Error fetching news points:', error);
            } finally {
                setIsLoading(false);
            }
        }

        fetchCrises();
    }, []);

    return { newsPoints, isLoading };
}
