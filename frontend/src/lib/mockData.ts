export interface CrisisPoint {
    id: string;
    lat: number;
    lng: number;
    intensity: number; // 0 to 1
    label: string;
    type: 'crisis' | 'voice' | 'node' | 'warning';
    description?: string;
    hasVault?: boolean;
    asset?: string;
}

export const MOCK_DATA: CrisisPoint[] = [
    {
        id: '0',
        lat: 31.7917,
        lng: -7.0926,
        intensity: 0.8,
        label: 'Morocco Earthquake Reconstruction',
        type: 'crisis',
        description: 'Post-earthquake reconstruction for remote villages in the Atlas Mountains.'
    },
];
