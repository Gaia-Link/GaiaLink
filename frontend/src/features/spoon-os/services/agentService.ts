import { CrisisPoint } from '@/lib/mockData';

export interface AgentResponse {
    message: string;
    action_taken: string;
    recommendation?: {
        action: 'PROCEED' | 'CAUTION' | 'ABORT';
        confidence: number;
        reason: string;
    };
    ui_hints: {
        mode: 'IDLE' | 'LISTENING' | 'PROCESSING' | 'DECISION' | 'SIGNATURE';
        display_data?: {
            title: string;
            badge_text: string;
            badge_color: string;
            risk_level: string;
            [key: string]: any;
        };
        actions?: Array<{
            label: string;
            type: string;
            icon: string;
            [key: string]: any;
        }>;
    };
    transaction_payload?: any;
}

export const MockAgentResponses: Record<string, AgentResponse> = {
    // Scenario 1: Verify Crisis (Turkey)
    'turkey': {
        message: "I verified the Turkey-Syria Earthquake data. Polymarket confirms it's a critical situation with 95% confidence. Humanitarian aid is urgently needed.",
        action_taken: "verify_crisis",
        recommendation: {
            action: "PROCEED",
            confidence: 95,
            reason: "Verified via Polymarket & Cross-referenced News."
        },
        ui_hints: {
            mode: "DECISION",
            display_data: {
                title: "Turkey-Syria Earthquake",
                badge_text: "Verified Crisis",
                badge_color: "green",
                risk_level: "CRITICAL"
            },
            actions: [
                { label: "Direct Donate (USDC)", type: "donate_direct", icon: "coins" },
                { label: "Yield Donate (4.5% APY)", type: "donate_yield", icon: "trending_up" }
            ]
        }
    },

    // Scenario 2a: Create Proposal - Ask Type (Morocco)
    'morocco_ask_type': {
        message: "I see no active vaults for Morocco. To create a new Proposal, please select the Vault implementation type.",
        action_taken: "ask_vault_type",
        ui_hints: {
            mode: "DECISION",
            display_data: {
                title: "New Proposal: Morocco",
                badge_text: "Configuration Needed",
                badge_color: "yellow",
                risk_level: "HIGH"
            },
            actions: [
                { label: "Yield Vault (Aave V3 Strategy)", type: "select_vault_yield", icon: "trending_up" },
                { label: "Direct Vault (Standard)", type: "select_vault_direct", icon: "wallet" }
            ]
        }
    },

    // Scenario 2b: Create Proposal - Ready to Sign
    'morocco_ready_sign': {
        message: "I've prepared the transaction for a Yield Vault (4.5% APY). Please review and sign to deploy the Proposal.",
        action_taken: "create_proposal",
        ui_hints: {
            mode: "SIGNATURE",
            display_data: {
                title: "Deploy Proposal",
                badge_text: "Pending Signature",
                badge_color: "yellow",
                risk_level: "HIGH"
            },
            actions: [
                { label: "Sign & Deploy", type: "sign_proposal", icon: "pen-tool" }
            ]
        },
        transaction_payload: {
            to: "0xFactory...",
            data: "0xCreateProposal(Morocco, Yield)..."
        }
    },

    // Default / Generic
    'default': {
        message: "I am ready to assist. You can ask me to verify a crisis, donate funds, or create a new proposal for an unlisted region.",
        action_taken: "idle_help",
        ui_hints: {
            mode: "IDLE",
            actions: []
        }
    }
};

/**
 * Simulates calling the Python Agent API.
 * In a real app, this would POST to /api/agent/chat
 */
export async function sendMessageToAgent(message: string, context?: any): Promise<AgentResponse> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    const lowerMsg = message.toLowerCase();

    // Simple keyword matching for Mock Logic
    if (lowerMsg.includes('turkey') || lowerMsg.includes('quake')) {
        return MockAgentResponses['turkey'];
    }

    // Step 1: Ask for Morroco Proposal
    if (lowerMsg.includes('morocco') || lowerMsg.includes('proposal')) {
        return MockAgentResponses['morocco_ask_type'];
    }

    // Step 2: Confirm Vault Type -> Ready to Sign
    if (lowerMsg.includes('yield') || lowerMsg.includes('direct') || lowerMsg.includes('vault')) {
        return MockAgentResponses['morocco_ready_sign'];
    }

    return MockAgentResponses['default'];
}
