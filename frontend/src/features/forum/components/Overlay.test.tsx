import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Overlay from '@/features/forum/components/Overlay';
import type { CrisisPoint } from '@/lib/mockData';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('Overlay Component', () => {
    const mockCrisisPoint: CrisisPoint = {
        id: 'c1',
        lat: 37.0902,
        lng: 37.1611,
        intensity: 0.8,
        label: 'Test Earthquake',
        type: 'crisis',
        description: 'Test description for earthquake',
    };

    const mockVoicePoint: CrisisPoint = {
        id: 'v1',
        lat: 37.15,
        lng: 37.2,
        intensity: 0.5,
        label: 'Test Voice',
        type: 'voice',
        description: 'Test voice description',
    };

    it('renders null when point is null', () => {
        const { container } = render(<Overlay point={null} onClose={() => { }} />);
        expect(container.firstChild).toBeNull();
    });

    it('renders the point label as heading', () => {
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} />);
        expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Test Earthquake');
    });

    it('displays the point type badge', () => {
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} />);
        expect(screen.getByText('crisis')).toBeInTheDocument();
    });

    it('displays the description', () => {
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} />);
        expect(screen.getByText('Test description for earthquake')).toBeInTheDocument();
    });

    it('displays formatted location', () => {
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} />);
        expect(screen.getByText(/37.0902, 37.1611/)).toBeInTheDocument();
    });

    it('calls onClose when close button is clicked', () => {
        const onClose = vi.fn();
        render(<Overlay point={mockCrisisPoint} onClose={onClose} />);

        fireEvent.click(screen.getByRole('button', { name: /close/i }));

        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onDonate when donate button is clicked', () => {
        const onDonate = vi.fn();
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} onDonate={onDonate} />);

        fireEvent.click(screen.getByRole('button', { name: /donate/i }));

        expect(onDonate).toHaveBeenCalledWith(mockCrisisPoint);
    });

    it('calls onDiscuss when discuss button is clicked', () => {
        const onDiscuss = vi.fn();
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} onDiscuss={onDiscuss} />);

        fireEvent.click(screen.getByRole('button', { name: /discuss/i }));

        expect(onDiscuss).toHaveBeenCalledWith(mockCrisisPoint);
    });

    it('shows verified status for crisis type', () => {
        render(<Overlay point={mockCrisisPoint} onClose={() => { }} />);
        expect(screen.getByText(/Polymarket/)).toBeInTheDocument();
        expect(screen.getByText(/98%/)).toBeInTheDocument();
    });

    it('shows unverified status for voice type', () => {
        render(<Overlay point={mockVoicePoint} onClose={() => { }} />);
        expect(screen.getByText(/Community report/)).toBeInTheDocument();
    });
});
