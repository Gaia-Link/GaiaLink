import { describe, it, expect } from 'vitest';
import { getColorByType, getLabelSizeByType, getDotRadiusByType } from '@/features/globe/utils/globeUtils';

describe('globeUtils', () => {
    describe('getColorByType', () => {
        it('returns red color for crisis type', () => {
            expect(getColorByType('crisis')).toBe('rgba(255, 60, 60, 0.9)');
        });

        it('returns blue color for voice type', () => {
            expect(getColorByType('voice')).toBe('rgba(60, 150, 255, 0.9)');
        });

        it('returns green color for node type', () => {
            expect(getColorByType('node')).toBe('rgba(60, 255, 100, 0.9)');
        });
    });

    describe('getLabelSizeByType', () => {
        it('returns larger size for crisis type', () => {
            expect(getLabelSizeByType('crisis')).toBe(1.5);
        });

        it('returns smaller size for voice type', () => {
            expect(getLabelSizeByType('voice')).toBe(0.8);
        });

        it('returns smaller size for node type', () => {
            expect(getLabelSizeByType('node')).toBe(0.8);
        });
    });

    describe('getDotRadiusByType', () => {
        it('returns larger radius for crisis type', () => {
            expect(getDotRadiusByType('crisis')).toBe(1.0);
        });

        it('returns smaller radius for voice type', () => {
            expect(getDotRadiusByType('voice')).toBe(0.4);
        });

        it('returns smaller radius for node type', () => {
            expect(getDotRadiusByType('node')).toBe(0.4);
        });
    });
});
