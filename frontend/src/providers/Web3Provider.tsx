'use client';

import * as React from 'react';
import '@rainbow-me/rainbowkit/styles.css';
import {
    getDefaultConfig,
    RainbowKitProvider,
} from '@rainbow-me/rainbowkit';
import { WagmiProvider, cookieStorage, createStorage, http } from 'wagmi';
import {
    mainnet,
    polygon,
    optimism,
    arbitrum,
    base,
    sepolia,
    foundry, // Local Anvil
} from 'wagmi/chains';
import {
    QueryClientProvider,
    QueryClient,
} from "@tanstack/react-query";

const config = getDefaultConfig({
    appName: 'Gaia Link',
    projectId: '76d95ee5ce69de7321d0749e0b87c2b8',
    chains: [mainnet, polygon, optimism, arbitrum, base, sepolia, foundry],
    ssr: true,
    storage: createStorage({
        storage: cookieStorage,
    }),
    transports: {
        [mainnet.id]: http(),
        [sepolia.id]: http('https://1rpc.io/sepolia', { batch: false }),
        [polygon.id]: http(),
        [optimism.id]: http(),
        [arbitrum.id]: http(),
        [base.id]: http(),
        [foundry.id]: http('http://localhost:8545'),
    },
});

// Custom QueryClient with error suppression for known harmless errors
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            // Suppress error logging for specific known issues
            // The decimals() call on non-ERC20 contracts is a wagmi/RainbowKit internal quirk
            retry: (failureCount, error) => {
                // Don't retry and don't log for known harmless errors
                const errorStr = String(error);
                if (errorStr.includes('0x313ce567') || // decimals()
                    errorStr.includes('0x95d89b41') || // symbol()
                    errorStr.includes('execution reverted')) {
                    // Silently fail - this is expected behavior for non-ERC20 contracts
                    return false;
                }
                return failureCount < 3;
            },
        },
        mutations: {
            // Don't log mutation errors that are expected
        }
    }
});

export function Web3Provider({ children }: { children: React.ReactNode }) {
    const [mounted, setMounted] = React.useState(false);
    React.useEffect(() => setMounted(true), []);

    return (
        <WagmiProvider config={config}>
            <QueryClientProvider client={queryClient}>
                <RainbowKitProvider>
                    {mounted ? children : null}
                </RainbowKitProvider>
            </QueryClientProvider>
        </WagmiProvider>
    );
}
