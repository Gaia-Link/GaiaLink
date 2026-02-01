'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll } from 'framer-motion';

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
import { useNewsPoints } from '@/hooks/useNewsPoints';
import VaultCreationModal from '@/features/landing/components/VaultCreationModal';

// Internal component to handle scroll tracking safely
// This ensures useScroll is only active when the element exists
function LandingPageWrapper({
    onScroll,
    onLaunch,
    onSectionChange
}: {
    onScroll: (val: number) => void,
    onLaunch: () => void,
    onSectionChange: (val: number) => void
}) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({ container: scrollRef });

    useEffect(() => {
        return scrollYProgress.on("change", (latest) => {
            console.log('📜 Scroll progress updated:', latest);
            onScroll(latest);
        });
    }, [scrollYProgress, onScroll]);

    return (
        <motion.div
            ref={scrollRef}
            className="absolute inset-0 z-20 overflow-y-auto scroll-smooth"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, pointerEvents: 'none', transition: { duration: 1 } }}
        >
            <LandingOverlay
                onLaunch={onLaunch}
                onSectionChange={onSectionChange}
            />
        </motion.div>
    );
}

export default function Page() { // Unified Entry Point
    // --- Global State ---
    const [isLaunched, setIsLaunched] = useState(false);
    const [activeSection, setActiveSection] = useState(0);
    const [scrollProgress, setScrollProgress] = useState(0);

    // REMOVED: Top-level useScroll ref (moved to LandingPageWrapper)

    // --- App State ---
    const [selectedPoint, setSelectedPoint] = useState<CrisisPoint | null>(null);
    const [isSpoonActive, setIsSpoonActive] = useState(false); // Controls dimming
    const [isSpoonOpen, setIsSpoonOpen] = useState(false);     // Controls visibility
    const [isDonationOpen, setIsDonationOpen] = useState(false);
    const [isPortfolioOpen, setIsPortfolioOpen] = useState(false);
    const [flyToLocation, setFlyToLocation] = useState<{ lng: number, lat: number, zoom?: number } | null>(null);
    const [creationCoords, setCreationCoords] = useState<{ lat: number, lng: number } | null>(null);
    const [optimisticPoints, setOptimisticPoints] = useState<CrisisPoint[]>([]);

    // --- Data & Hooks ---
    const { sendTransaction } = useSendTransaction();
    const onChainProposals = useProposals();
    const { newsPoints } = useNewsPoints();

    // Deduplicate: Remove optimistic points if a real point exists near the same location
    const filteredOptimistic = optimisticPoints.filter(op => {
        // If we find a real proposal within ~0.01 degrees, assume it's the confirmed version of this temp point
        const exists = onChainProposals.some(real =>
            Math.abs(real.lat - op.lat) < 0.0001 && Math.abs(real.lng - op.lng) < 0.0001
        );
        return !exists;
    });

    // Deduplicate: Remove news points if a real on-chain proposal exists near the same location
    const filteredNews = newsPoints.filter(np => {
        const exists = onChainProposals.some(real =>
            Math.abs(real.lat - np.lat) < 0.005 && Math.abs(real.lng - np.lng) < 0.005
        );
        return !exists;
    });

    const data = [...onChainProposals, ...filteredOptimistic, ...filteredNews];

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

    // --- Handlers ---
    const handleDonate = (point: CrisisPoint) => {
        setSelectedPoint(point);
        setIsDonationOpen(true);
    };

    const handleProposalCreated = (newPoint: CrisisPoint) => {
        console.log('🚀 Optimistic Update:', newPoint);
        setOptimisticPoints(prev => [...prev, newPoint]);
    };

    const handleMapClick = (coords: { lat: number, lng: number }) => {
        console.log('📍 Map Clicked:', coords);
        setCreationCoords(coords);
    };

    const handleSpoonAction = (action: string, data?: any) => {
        console.log('SpoonOS Action:', action, data);

        if (action === 'FLY_TO_LOCATION' && data) {
            setFlyToLocation(data);
        }
        else if (action === 'OPEN_PROPOSAL' && data) {
            console.log("📂 Opening proposal:", data);
            // 1. Fly to location
            if (data.lat && data.lng) {
                setFlyToLocation({
                    lat: data.lat,
                    lng: data.lng,
                    zoom: data.zoom || 12 // Default to close zoom if not specified 
                });
            }

            // 2. Open details (Requires finding the point or constructing a mock one)
            // Since we have data.id, we can look it up in 'data' (onChainProposals)
            const proposal = onChainProposals.find(p => p.id === data.id.toString());

            if (proposal) {
                setSelectedPoint(proposal);
                setIsDonationOpen(true);
            } else {
                // Fallback if not found in current globe data (maybe filtered out or fresh)
                // Construct a temporary point object
                const tempPoint: CrisisPoint = {
                    id: data.id.toString(),
                    lat: data.lat || 0,
                    lng: data.lng || 0,
                    label: "Proposal Details",
                    type: 'node',
                    intensity: 1,
                    hasVault: true,
                    // Add other required fields with defaults
                };
                // We might need to fetch details if not in list, but for now try to open with limited info
                // or just rely on DonationModal fetching details by ID? 
                // DonationModal takes 'point' which is CrisisPoint.
                // Let's rely on finding it first.
                console.warn("Proposal not found in current globe data:", data.id);
            }
        }
        else if (action === 'OPEN_DONATION') {
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
                    onMapClick={handleMapClick}
                    isLaunched={isLaunched}
                    activeSection={activeSection}
                    scrollProgress={scrollProgress}
                    flyToLocation={flyToLocation}
                />
            </div>


            {/* 2. Landing Page Overlay (Unmounted or Hidden after Launch) */}
            <AnimatePresence>
                {!isLaunched && (
                    <LandingPageWrapper
                        onScroll={setScrollProgress}
                        onLaunch={() => setIsLaunched(true)}
                        onSectionChange={setActiveSection}
                    />
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

                            <VaultCreationModal
                                isOpen={!!creationCoords}
                                onClose={() => setCreationCoords(null)}
                                coords={creationCoords}
                                onProposalCreated={handleProposalCreated}
                            />
                        </div>

                        {/* Instructions / Footer */}
                        <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 text-white/50 text-xs pointer-events-none z-0 transition-opacity ${isSpoonActive ? 'opacity-0' : 'opacity-100'}`}>
                            Click on Red Zones to view requests. Click anywhere to deploy a new Vault. Press <span className="font-bold text-white">SPACE</span> to speak to SpoonOS.
                        </div>

                    </motion.div>
                )}
            </AnimatePresence>

        </main>
    );
}
