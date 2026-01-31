import type { CrisisPoint } from '@/lib/mockData';

/**
 * Returns the color for a given point type.
 * Pure function - easy to test.
 */
export function getColorByType(type: CrisisPoint['type']): string {
    switch (type) {
        case 'crisis':
            return 'rgba(255, 60, 60, 0.9)';
        case 'voice':
            return 'rgba(60, 150, 255, 0.9)';
        case 'node':
            return 'rgba(60, 255, 100, 0.9)';
        case 'warning':
            return 'rgba(255, 180, 60, 0.9)';
        default:
            return 'rgba(255, 255, 255, 0.7)';
    }
}

/**
 * Returns the label size for a given point type.
 */
export function getLabelSizeByType(type: CrisisPoint['type']): number {
    return type === 'crisis' ? 1.5 : 0.8;
}

/**
 * Returns the dot radius for a given point type.
 */
export function getDotRadiusByType(type: CrisisPoint['type']): number {
    return type === 'crisis' ? 1.0 : 0.4;
}
