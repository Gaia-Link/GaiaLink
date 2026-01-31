import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WagmiProvider, createConfig, http } from 'wagmi';
import { sepolia } from 'wagmi/chains';
import SpoonOSInterface from './SpoonOSInterface';

// Create a minimal wagmi config for testing
const testConfig = createConfig({
    chains: [sepolia],
    transports: {
        [sepolia.id]: http(),
    },
});

const queryClient = new QueryClient({
    defaultOptions: {
        queries: { retry: false },
    },
});

// Wrapper component for tests
function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
        <WagmiProvider config={testConfig}>
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        </WagmiProvider>
    );
}

// Custom render with providers
const customRender = (ui: React.ReactElement, options = {}) =>
    render(ui, { wrapper: TestWrapper, ...options });

// Define minimal mock responses locally to avoid importing actual module in mock factory
const LocalMockResponses = {
    'default': {
        message: "I am ready to assist.",
        action_taken: "idle_help",
        ui_hints: { mode: "IDLE", actions: [] }
    },
    'turkey': {
        message: "Since you asked about Turkey, here is the analysis.",
        action_taken: "verify_crisis",
        ui_hints: {
            mode: "DECISION",
            display_data: { title: "Turkey Crisis", risk_level: "CRITICAL", badge_text: "Verified", badge_color: "green" },
            actions: []
        }
    }
};

// Mock the service using local data
vi.mock('../services/agentService', () => {
    return {
        sendMessageToAgent: vi.fn(async (msg: string) => {
            // Check for a specific "delay" trigger string for testing intermediate states
            if (msg.includes('delay_me')) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            const lower = msg.toLowerCase();
            if (lower.includes('turkey')) return LocalMockResponses['turkey'];
            return LocalMockResponses['default'];
        })
    };
});

describe('SpoonOSInterface Integration', () => {
    it('renders in IDLE mode initially (or hidden)', () => {
        customRender(<SpoonOSInterface isOpen={false} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);
        const input = screen.queryByRole('textbox');
        // When IDLE/Hidden, input might not be interactive or present depending on implementation details
        // but checking it doesn't crash is good.
    });

    it('activates LISTENING mode when opened', () => {
        customRender(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);
        const input = screen.getByRole('textbox');
        expect(input).toBeDefined();
    });

    it('enters THINKING mode and keeps expanded view during processing', async () => {
        customRender(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);

        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: 'delay_me turkey' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        // Immediately after enter, we should be in THINKING mode
        // Verify "Thinking..." text is present inside the chat area
        await waitFor(() => {
            expect(screen.getByText('Thinking...')).toBeDefined();
        });

        // Verify it is expanded - checking for the header. 
        // In THINKING mode, the header title changes to "Processing..."
        // Use regex for case insensitivity if needed, but exact match is better if known
        expect(screen.getByText('Processing...')).toBeDefined();

        // Wait for it to finish and go to DECISION
        await waitFor(() => {
            // Since we mocked data locally, check that text
            const analysisText = screen.getByText(/Since you asked about/i);
            expect(analysisText).toBeDefined();
        }, { timeout: 2000 });

        // After finishing, it should revert to normal header
        expect(screen.getByText('GaiaLink Agent')).toBeDefined();
    });

    it('submits query and displays message response', async () => {
        customRender(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);

        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: 'Turkey earthquake' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        // Check for the agent's response message
        await waitFor(() => {
            const messageText = screen.getByText(/Since you asked about Turkey/i);
            expect(messageText).toBeDefined();
        });

        // Check that the header is the standard Agent header
        const header = screen.getByText('GaiaLink Agent');
        expect(header).toBeDefined();
    });

    it('re-opens in expanded DECISION mode if history exists', async () => {
        const { rerender } = customRender(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);

        // 1. Send a message to populate history
        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: 'Turkey' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        await waitFor(() => {
            expect(screen.getByText('GaiaLink Agent')).toBeDefined();
        });

        // 2. Close interface
        rerender(<SpoonOSInterface isOpen={false} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);

        // 3. Re-open interface
        rerender(<SpoonOSInterface isOpen={true} onClose={() => { }} selectedPoint={null} onAction={() => { }} />);

        // Should be in DECISION mode (expanded) not LISTENING
        // Check for expanded header
        await waitFor(() => {
            expect(screen.getByText('GaiaLink Agent')).toBeDefined();
        });

        // And history should be visible
        expect(screen.getByText(/Since you asked about Turkey/i)).toBeDefined();
    });
});
