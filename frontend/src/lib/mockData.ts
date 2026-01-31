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
