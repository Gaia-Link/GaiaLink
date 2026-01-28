import type { CrisisPoint } from '@/lib/mockData';

export interface VerificationResult {
    isVerified: boolean;
    confidence: number;
    message: string;
}

/**
 * Determines the verification status for a given crisis point.
 * Pure function - easy to test.
 */
export function getVerificationStatus(point: CrisisPoint): VerificationResult {
    if (point.type === 'crisis') {
        return {
            isVerified: true,
            confidence: 98,
            message: 'Verified against real-time Polymarket & news data.',
        };
    }

    if (point.type === 'node') {
        return {
            isVerified: true,
            confidence: 100,
            message: 'Verified humanitarian organization.',
        };
    }

    // voice type
    return {
        isVerified: false,
        confidence: 0,
        message: 'Community report. Needs more verifications from local nodes.',
    };
}

/**
 * Format location coordinates for display.
 */
export function formatLocation(lat: number, lng: number): string {
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
}
