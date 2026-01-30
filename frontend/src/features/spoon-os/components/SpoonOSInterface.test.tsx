import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SpoonOSInterface from './SpoonOSInterface';
import { MockAgentResponses } from '../services/agentService';

// Mock the simulate delay to speed up tests
vi.mock('../services/agentService', async () => {
    const actual = await vi.importActual('../services/agentService');
    return {
        ...actual,
        sendMessageToAgent: vi.fn(async (msg: string) => {
            // Return immediate response for tests
            const lower = msg.toLowerCase();
            if (lower.includes('turkey')) return MockAgentResponses['turkey'];
            return MockAgentResponses['default'];
        })
    };
});

describe('SpoonOSInterface Integration', () => {
    it('renders in IDLE mode initially (or hidden)', () => {
        render(<SpoonOSInterface isOpen={false} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);
        // When not open, it might still render but not be visible/active in "LISTENING"
        // Based on code: isOpen=false + IDLE -> just renders IDLE bar
        const input = screen.queryByRole('textbox');
        // Initial state is IDLE, input should be present but maybe placeholders typing
    });

    it('activates LISTENING mode when opened', () => {
        render(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);
        const input = screen.getByRole('textbox');
        expect(input).toBeDefined();
    });

    it('submits query and displays DECISION card', async () => {
        render(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);

        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: 'Turkey earthquake' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        // Should go to PROCESSING then DECISION
        // Since we mocked sendMessageToAgent to be instant, we wait for re-render

        await waitFor(() => {
            const analysisText = screen.getByText(/SpoonOS Analysis/i);
            expect(analysisText).toBeDefined();
        });

        await waitFor(() => {
            const riskLevel = screen.getByText(/CRITICAL/i);
            expect(riskLevel).toBeDefined();
        });
    });
});
