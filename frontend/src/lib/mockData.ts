export interface CrisisPoint {
    lat: number;
    lng: number;
    label: string;
    type: 'crisis' | 'voice' | 'node';
    description?: string;
    intensity?: number; // 0-1 for visual pulse
}

export const MOCK_DATA: CrisisPoint[] = [
    // Red Zones (Crisis)
    { lat: 37.0902, lng: 37.1611, label: 'Earthquake - Gaziantep', type: 'crisis', intensity: 0.9, description: '7.8 Magnitude Earthquake, Urgent Medical Aid Needed' },
    { lat: 14.5995, lng: 120.9842, label: 'Typhoon - Manila', type: 'crisis', intensity: 0.8, description: 'Super Typhoon Landfall, Flooding in Low-lying Areas' },
    { lat: 31.501, lng: 34.466, label: 'Conflict Zone - Gaza', type: 'crisis', intensity: 0.95, description: 'Active Conflict, Humanitarian Corridor Required' },

    // Blue Bubbles (Voices)
    { lat: 37.15, lng: 37.2, label: 'Supplies Needed', type: 'voice', description: 'We need clean water and blankets at shelter A.' },
    { lat: 14.65, lng: 121.0, label: 'Road Blocked', type: 'voice', description: 'Main bridge is down, alternative route via north.' },

    // Green Nodes (Verified Orgs)
    { lat: 48.8566, lng: 2.3522, label: 'Red Cross HQ', type: 'node', description: 'Coordination Center' },
];
