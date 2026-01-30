export interface CrisisPoint {
    id: string;
    lat: number;
    lng: number;
    intensity: number; // 0 to 1
    label: string;
    type: 'crisis' | 'voice' | 'node';
    description?: string;
    hasVault?: boolean;
}

export const MOCK_DATA: CrisisPoint[] = [
    { id: '1', lat: 48.8566, lng: 2.3522, intensity: 1, label: 'Red Cross HQ', type: 'node', description: 'Coordination Center' },
];
