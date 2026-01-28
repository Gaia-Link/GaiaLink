import { describe, it, expect } from 'vitest';
import { getVerificationStatus, formatLocation } from '@/features/forum/utils/verificationUtils';
import type { CrisisPoint } from '@/lib/mockData';

describe('verificationUtils', () => {
    describe('getVerificationStatus', () => {
        it('returns verified status for crisis type with 98% confidence', () => {
            const crisisPoint: CrisisPoint = {
                lat: 37.0902,
                lng: 37.1611,
                label: 'Earthquake',
                type: 'crisis',
            };

            const result = getVerificationStatus(crisisPoint);

            expect(result.isVerified).toBe(true);
            expect(result.confidence).toBe(98);
            expect(result.message).toContain('Polymarket');
        });

        it('returns verified status for node type with 100% confidence', () => {
            const nodePoint: CrisisPoint = {
                lat: 48.8566,
                lng: 2.3522,
                label: 'Red Cross HQ',
                type: 'node',
            };

            const result = getVerificationStatus(nodePoint);

            expect(result.isVerified).toBe(true);
            expect(result.confidence).toBe(100);
            expect(result.message).toContain('humanitarian');
        });

        it('returns unverified status for voice type', () => {
            const voicePoint: CrisisPoint = {
                lat: 37.15,
                lng: 37.2,
                label: 'Supplies Needed',
                type: 'voice',
            };

            const result = getVerificationStatus(voicePoint);

            expect(result.isVerified).toBe(false);
            expect(result.confidence).toBe(0);
            expect(result.message).toContain('Community report');
        });
    });

    describe('formatLocation', () => {
        it('formats coordinates to 4 decimal places', () => {
            expect(formatLocation(37.09023456, 37.16115678)).toBe('37.0902, 37.1612');
        });

        it('handles negative coordinates', () => {
            expect(formatLocation(-33.8688, 151.2093)).toBe('-33.8688, 151.2093');
        });

        it('handles zero coordinates', () => {
            expect(formatLocation(0, 0)).toBe('0.0000, 0.0000');
        });
    });
});
