'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll } from 'framer-motion';
import dynamic from 'next/dynamic';

// Landing Page Components
import LandingOverlay from '@/features/landing/components/LandingOverlay';

// App Components
import Overlay from '@/features/crisis-details/components/Overlay';
import SpoonOSInterface from '@/features/spoon-os/components/SpoonOSInterface';
import DonationModal from '@/features/donation/components/DonationModal';
import LivingGlobe from '@/features/globe/components/LivingGlobe';
import { CrisisPoint } from '@/lib/mockData';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import RpcTester from '@/features/debug/RpcTester';
import { useSendTransaction } from 'wagmi';
import { History } from 'lucide-react';
import UserPortfolioModal from '@/features/portfolio/UserPortfolioModal';
import { useProposals } from '@/hooks/useProposals';

export default function Page() { // Unified Entry Point
    // --- Global State ---
    const [isLaunched, setIsLaunched] = useState(false);
    const [activeSection, setActiveSection] = useState(0);
    const [scrollProgress, setScrollProgress] = useState(0);
    const landingScrollRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({ container: landingScrollRef });

    // --- App State ---
    const [selectedPoint, setSelectedPoint] = useState<CrisisPoint | null>(null);
    const [isSpoonActive, setIsSpoonActive] = useState(false); // Controls dimming
    const [isSpoonOpen, setIsSpoonOpen] = useState(false);     // Controls visibility
    const [isDonationOpen, setIsDonationOpen] = useState(false);
    const [isPortfolioOpen, setIsPortfolioOpen] = useState(false);

    // --- Data & Hooks ---
    const { sendTransaction } = useSendTransaction();
    const onChainProposals = useProposals();
    const data = onChainProposals;

    // --- App Specific Effects ---
    // Toggle SpoonOS with Spacebar (Only if launched)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!isLaunched) return; // Only work in App Mode

            // Prevent triggering if typing in an input
            if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return;

            if (e.code === 'Space') {
                e.preventDefault();
                setIsSpoonOpen(prev => !prev);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isLaunched]);

    // Track scroll progress from landing overlay
    useEffect(() => {
        if (isLaunched) return; // Only track during landing page
        return scrollYProgress.on("change", (latest) => {
            console.log('📜 Scroll progress updated:', latest);
            setScrollProgress(latest);
        });
    }, [scrollYProgress, isLaunched]);

    // --- Handlers ---
    const handleDonate = (point: CrisisPoint) => {
        setSelectedPoint(point);
        setIsDonationOpen(true);
    };

    const handleSpoonAction = (action: string, data?: any) => {
        console.log('SpoonOS Action:', action, data);

        if (action === 'OPEN_DONATION') {
            setIsDonationOpen(true);
            if (data) setSelectedPoint(data);
        }
        else if (action === 'sign_proposal') {
            console.log('📝 Signing proposal transaction...', data);
            alert('✅ Transaction signed! (Mock)\n\nIn production, this would:\n1. Prompt your wallet to sign\n2. Deploy a new vault proposal on-chain\n3. Show transaction confirmation');
        }
        else if (action === 'sign_transaction') {
            console.log('📝 Signing donation transaction...', data);
            if (data && data.to && data.value) {
                try {
                    sendTransaction({
                        to: data.to,
                        value: BigInt(data.value),
                        data: data.data as `0x${string}`,
                        chainId: data.chainId
                    });
                } catch (error) {
                    console.error("Transaction failed:", error);
                    alert("Transaction failed to initiate.");
                }
            }
        }
        else if (action === 'donate_direct' || action === 'donate_yield') {
            setIsDonationOpen(true);
            if (data) setSelectedPoint(data);
        }
    };


    return (
        <main className="relative h-screen w-full overflow-hidden bg-black text-white">

            {/* 1. Underlying Persistent Globe Layer */}
            {/* It sits at z-0. It changes behavior based on isLaunched and activeSection */}
            <div className={`absolute inset-0 z-0 transition-all duration-1000 ${isSpoonActive && isLaunched ? 'scale-95 opacity-50 blur-sm rounded-3xl overflow-hidden' : 'scale-100 opacity-100 blur-0'}`}>
                <LivingGlobe
                    data={data}
                    onPointClick={setSelectedPoint}
                    isLaunched={isLaunched}
                    activeSection={activeSection}
                    scrollProgress={scrollProgress}
                />
            </div>


            {/* 2. Landing Page Overlay (Unmounted or Hidden after Launch) */}
            <AnimatePresence>
                {!isLaunched && (
                    <motion.div
                        ref={landingScrollRef}
                        className="absolute inset-0 z-20 overflow-y-auto scroll-smooth"
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0, pointerEvents: 'none', transition: { duration: 1 } }}
                    >
                        <LandingOverlay
                            onLaunch={() => setIsLaunched(true)}
                            onSectionChange={setActiveSection}
                        />
                    </motion.div>
                )}
            </AnimatePresence>


            {/* 3. Main App UI (Visible after Launch) */}
            <AnimatePresence>
                {isLaunched && (
                    <motion.div
                        className="absolute inset-0 z-10 pointer-events-none" // pointer-events-none to let clicks pass to Globe where no UI exists
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 1, delay: 0.5 }}
                    >
                        {/* Top Bar */}
                        <div className={`absolute top-0 left-0 w-full p-6 flex justify-between items-start z-10 pointer-events-none transition-opacity duration-500 ${isSpoonActive ? 'opacity-20' : 'opacity-100'}`}>
                            {/* Brand / Title */}
                            <div className="pointer-events-auto">
                                <h1 className="text-4xl font-black text-white tracking-tighter drop-shadow-lg">
                                    GAIA<span className="text-blue-400">LINK</span>
                                </h1>
                                <p className="text-white/70 text-sm max-w-xs mt-2 drop-shadow-md">
                                    Decentralized Humanitarian Aid Network. <br />
                                    Visualize. Verify. Act.
                                </p>
                            </div>

                            {/* Wallet Connect & Portfolio */}
                            <div className="pointer-events-auto flex items-center gap-3">
                                <button
                                    onClick={() => setIsPortfolioOpen(true)}
                                    className="p-2.5 bg-white/10 hover:bg-white/20 rounded-xl transition text-white border border-white/5 backdrop-blur-md"
                                    title="My Donations"
                                >
                                    <History size={20} />
                                </button>
                                <ConnectButton showBalance={false} />
                            </div>

                            <RpcTester />
                        </div>

                        {/* Modals & Interfaces (Pointer events auto inside) */}
                        <div className="pointer-events-auto">
                            <Overlay
                                point={selectedPoint}
                                onClose={() => setSelectedPoint(null)}
                                onDonate={handleDonate}
                            />

                            <SpoonOSInterface
                                isOpen={isSpoonOpen}
                                onClose={() => setIsSpoonOpen(false)}
                                selectedPoint={selectedPoint}
                                onAction={handleSpoonAction}
                                onStateChange={setIsSpoonActive}
                            />

                            <DonationModal
                                isOpen={isDonationOpen}
                                onClose={() => setIsDonationOpen(false)}
                                point={selectedPoint}
                            />

                            <UserPortfolioModal
                                isOpen={isPortfolioOpen}
                                onClose={() => setIsPortfolioOpen(false)}
                            />
                        </div>

                        {/* Instructions / Footer */}
                        <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 text-white/50 text-xs pointer-events-none z-0 transition-opacity ${isSpoonActive ? 'opacity-0' : 'opacity-100'}`}>
                            Click on Red Zones to view requests. Press <span className="font-bold text-white">SPACE</span> to speak to SpoonOS.
                        </div>

                    </motion.div>
                )}
            </AnimatePresence>

        </main>
    );
}
