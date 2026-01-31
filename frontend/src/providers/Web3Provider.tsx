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
        [foundry.id]: http('http://127.0.0.1:8545'),
    },
});

const queryClient = new QueryClient();

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
