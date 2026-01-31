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

    // Scenario 3: Intent Donate (100 USDC)
    'donate_intent': {
        message: "I have prepared a DIRECT donation of 100 USDC to Turkey. Please sign the transaction to proceed.",
        action_taken: "execute_donation",
        ui_hints: {
            mode: "SIGNATURE",
            display_data: {
                title: "Turkey-Syria Earthquake",
                badge_text: "Donation Ready",
                badge_color: "green",
                risk_level: "CRITICAL"
            },
            actions: [
                { label: "Sign Transaction", type: "sign_transaction", icon: "pen-tool" }
            ]
        },
        transaction_payload: {
            // Sepolia USDC contract address
            to: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
            value: "0",
            // transfer(0x742d35Cc6634C0532925a3b844Bc9e7595f5bE91, 100000000) - 100 USDC
            data: "0xa9059cbb000000000000000000000000742d35cc6634c0532925a3b844bc9e7595f5be910000000000000000000000000000000000000000000000000000000005f5e100",
            chainId: 11155111,
            gas: "65000",
            intent_summary: "Donate 100 USDC via DIRECT Vault"
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
 * Calls the Python Agent API.
 */
export async function sendMessageToAgent(message: string, context?: any): Promise<AgentResponse> {
    try {
        const res = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                context: context || {}
            }),
        });

        if (!res.ok) {
            throw new Error(`Server error: ${res.status}`);
        }

        const data = await res.json();
        return data as AgentResponse;

    } catch (error) {
        console.error("Agent API connection failed:", error);

        // Fallback for demo if server is down
        const lowerMsg = message.toLowerCase();
        if (lowerMsg.includes('100') || (lowerMsg.includes('donate') && lowerMsg.includes('usdc'))) {
            const fallback = MockAgentResponses['donate_intent'];
            return {
                ...fallback,
                message: "[DEMO MODE] " + fallback.message + " (Backend offline - using cached response)",
                ui_hints: {
                    ...fallback.ui_hints,
                    display_data: {
                        title: fallback.ui_hints.display_data?.title || "Donation Ready",
                        risk_level: fallback.ui_hints.display_data?.risk_level || "LOW",
                        badge_text: "Demo Mode",
                        badge_color: "yellow"
                    }
                }
            };
        }

        return {
            message: "[Backend Offline] Unable to connect to the GaiaLink Agent server. Please ensure the Python backend is running on port 8000.",
            action_taken: "connection_error",
            ui_hints: {
                mode: "IDLE",
                display_data: {
                    title: "Connection Error",
                    badge_text: "Offline",
                    badge_color: "red",
                    risk_level: "LOW"
                }
            }
        };
    }
}
