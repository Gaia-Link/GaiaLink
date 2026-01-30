import { describe, it, expect } from 'vitest';
import { sendMessageToAgent } from './agentService';

describe('agentService (Mock)', () => {
    it('should return Turkey verification response for "Turkey earthquake"', async () => {
        const response = await sendMessageToAgent("Tell me about Turkey earthquake");

        expect(response.message).toContain("verified the Turkey-Syria Earthquake");
        expect(response.ui_hints.mode).toBe("DECISION");
        expect(response.ui_hints.display_data?.risk_level).toBe("CRITICAL");
    });

    it('should return Proposal creation response for "Create proposal for Morocco"', async () => {
        const response = await sendMessageToAgent("Create proposal for Morocco");

        expect(response.message).toContain("create a new Layer 2 Proposal");
        expect(response.ui_hints.mode).toBe("SIGNATURE");
        expect(response.transaction_payload).toBeDefined();
    });

    it('should return default response for unknown queries', async () => {
        const response = await sendMessageToAgent("Hello world");

        expect(response.action_taken).toBe("idle_help");
        expect(response.ui_hints.mode).toBe("IDLE");
    });
});
