'use client';

import React, { useEffect, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { ArrowDown, Zap, Globe, Lock, Activity, ShieldCheck, Database } from 'lucide-react';

interface LandingOverlayProps {
    onLaunch: () => void;
    onSectionChange: (sectionIndex: number) => void;
    onScrollProgress?: (progress: number) => void;
}

export default function LandingOverlay({ onLaunch, onSectionChange }: LandingOverlayProps) {
    // Note: onScrollProgress is now handled in parent page.tsx

    // Track sections
    const section1Ref = useRef(null);
    const section2Ref = useRef(null);
    const section3Ref = useRef(null);
    const section4Ref = useRef(null);
    const section5Ref = useRef(null);
    const section6Ref = useRef(null);
    const section7Ref = useRef(null);

    const isInView1 = useInView(section1Ref, { amount: 0.5 });
    const isInView2 = useInView(section2Ref, { amount: 0.5 });
    const isInView3 = useInView(section3Ref, { amount: 0.5 });
    const isInView4 = useInView(section4Ref, { amount: 0.5 });
    const isInView5 = useInView(section5Ref, { amount: 0.5 });
    const isInView6 = useInView(section6Ref, { amount: 0.5 });
    const isInView7 = useInView(section7Ref, { amount: 0.5 });

    useEffect(() => {
        if (isInView1) { onSectionChange(0); }
        else if (isInView2) { onSectionChange(1); }
        else if (isInView3) { onSectionChange(2); }
        else if (isInView4) { onSectionChange(3); }
        else if (isInView5) { onSectionChange(4); }
        else if (isInView6) { onSectionChange(5); }
        else if (isInView7) { onSectionChange(6); }
    }, [isInView1, isInView2, isInView3, isInView4, isInView5, isInView6, isInView7, onSectionChange]);

    return (
        <div className="relative z-10 w-full overflow-x-hidden text-white selection:bg-blue-500/30">

            {/* --- Section 1: Hero --- */}
            <section ref={section1Ref} className="h-screen w-full flex flex-col items-center pt-32 relative pointer-events-none">
                <div className="pointer-events-auto text-center z-10 p-6 max-w-4xl">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={isInView1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -30 }}
                        transition={{ duration: 0.8 }}
                    >
                        <h1 className="text-7xl md:text-9xl font-black tracking-tighter mb-4 mix-blend-overlay">
                            GaiaLink
                        </h1>
                        <div className="flex justify-center mb-8">
                            <div className="h-px w-24 bg-gradient-to-r from-transparent via-blue-500 to-transparent"></div>
                        </div>
                        <div className="overflow-hidden mb-8 flex justify-center">
                            <motion.p
                                initial={{ y: "100%" }}
                                animate={{ y: 0 }}
                                transition={{ delay: 0.5, duration: 0.8, ease: "circOut" }}
                                className="text-xl md:text-3xl font-mono text-white drop-shadow-xl leading-relaxed"
                            >
                                The First <span className="text-blue-400 font-bold">Intent-Centric</span> Spatial OS <br className="hidden md:block" /> for Humanitarian Aid.
                            </motion.p>
                        </div>

                        <button
                            onClick={onLaunch}
                            className="bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 text-white px-8 py-3 rounded-full font-bold text-lg transition-all hover:scale-105 active:scale-95 group shadow-[0_0_30px_rgba(59,130,246,0.3)] animate-pulse hover:animate-none"
                        >
                            Launch OS
                        </button>
                    </motion.div>
                </div>

                <motion.div
                    className="absolute bottom-10 left-1/2 -translate-x-1/2 text-white/50 flex flex-col items-center gap-2"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 2, duration: 1 }}
                >
                    <span className="text-xs uppercase tracking-widest">Scroll to initialize</span>
                    <ArrowDown className="animate-bounce" size={20} />
                </motion.div>
            </section>


            {/* --- Section 2: The Problem (Split Layout) --- */}
            <section ref={section2Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
                <div className="container mx-auto grid grid-cols-1 md:grid-cols-2 gap-24 align-middle h-full">

                    {/* Left Column: Context */}
                    <div className="flex flex-col justify-center pointer-events-auto">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8 }}
                            className="mb-12"
                        >
                            <h2 className="text-4xl md:text-6xl font-bold mb-4 leading-tight w-full">System Failure.<br /><span className="text-red-500">Inefficiency Detected.</span></h2>
                            <p className="text-gray-400 text-lg mt-4 max-w-md">
                                Current humanitarian protocols are slow, opaque, and analog. We need a system upgrade.
                            </p>
                        </motion.div>
                    </div>

                    {/* Right Column: Visual Intelligence Legend */}
                    <div className="flex flex-col justify-center pointer-events-auto items-end space-y-4">
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 }}
                            className="bg-black/60 backdrop-blur-xl border border-white/10 p-4 rounded-xl w-64 shadow-[0_0_20px_rgba(0,0,0,0.5)]"
                        >
                            <h3 className="text-sm font-bold mb-3 text-blue-300 uppercase tracking-widest">Visual Recon</h3>
                            <div className="space-y-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-[#F56565] shadow-[0_0_8px_#F56565]"></div>
                                    <span className="text-xs text-gray-300">High Severity Vault</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-[#F6E05E] shadow-[0_0_8px_#F6E05E]"></div>
                                    <span className="text-xs text-gray-300">Medium Severity Vault</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-[#4299E1] shadow-[0_0_8px_#4299E1]"></div>
                                    <span className="text-xs text-gray-300">Standard Aid Vault</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-[#9F7AEA] shadow-[0_0_8px_#9F7AEA] animate-pulse"></div>
                                    <span className="text-xs text-gray-200 font-bold">New Crisis / Event</span>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 }}
                            className="text-right pr-2"
                        >
                            <p className="text-xs text-gray-500 font-mono">
                                DATA_STREAM: ACTIVE<br />
                                RESOLUTION: HIGH<br />
                                MODE: SPATIAL_INTEL
                            </p>
                        </motion.div>
                    </div>
                </div>
            </section>


            {/* --- Section 3: The Solution (Split Layout Inverted) --- */}
            <section ref={section3Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
                <div className="container mx-auto grid grid-cols-1 md:grid-cols-2 gap-24 align-middle h-full">

                    {/* Left Column: AI Skills Map */}
                    <div className="flex flex-col justify-center pointer-events-auto space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="p-4 bg-red-500/10 rounded-xl border border-red-500/20 backdrop-blur-md"
                            >
                                <ShieldCheck className="text-red-400 mb-2" size={20} />
                                <h3 className="text-sm font-bold text-white">Crisis Response</h3>
                                <p className="text-[10px] text-gray-400">Verify & Validate Events</p>
                            </motion.div>

                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20 backdrop-blur-md"
                            >
                                <Zap className="text-blue-400 mb-2" size={20} />
                                <h3 className="text-sm font-bold text-white">Donation Advisor</h3>
                                <p className="text-[10px] text-gray-400">Path & Gas Optimization</p>
                            </motion.div>

                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="p-4 bg-purple-500/10 rounded-xl border border-purple-500/20 backdrop-blur-md"
                            >
                                <Database className="text-purple-400 mb-2" size={20} />
                                <h3 className="text-sm font-bold text-white">Pool Manager</h3>
                                <p className="text-[10px] text-gray-400">Vault & Yield Control</p>
                            </motion.div>

                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className="p-4 bg-green-500/10 rounded-xl border border-green-500/20 backdrop-blur-md"
                            >
                                <Activity className="text-green-400 mb-2" size={20} />
                                <h3 className="text-sm font-bold text-white">Donation Tracker</h3>
                                <p className="text-[10px] text-gray-400">Impact & Transparency</p>
                            </motion.div>
                        </div>
                    </div>

                    {/* Right Column: Title */}
                    <div className="flex flex-col justify-center pointer-events-auto">
                        <motion.div
                            initial={{ opacity: 0, x: 50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8 }}
                            className="mb-12"
                        >
                            <div className="inline-block px-4 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-xs font-bold uppercase tracking-widest mb-6 backdrop-blur-md">
                                SpoonOS Activated
                            </div>
                            <h2 className="text-4xl md:text-6xl font-bold mb-4 leading-tight">Spatial Intelligence. <br /><span className="text-blue-400">Powered by Agents.</span></h2>
                            <p className="text-gray-400 text-lg max-w-md">
                                Multi-skill AI agents manage the complexity of global aid, from on-chain verification to yield optimization.
                            </p>
                        </motion.div>
                    </div>
                </div>
            </section>


            {/* --- Section 4: Architecture (L1/L2) --- */}
            <section ref={section4Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
                <div className="container mx-auto grid grid-cols-1 md:grid-cols-2 gap-24 align-middle h-full">

                    {/* Left Column: Title */}
                    <div className="flex flex-col justify-center pointer-events-auto">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8 }}
                            className="mb-12"
                        >
                            <div className="inline-block px-4 py-1.5 rounded-full border border-green-500/30 bg-green-500/10 text-green-400 text-xs font-bold uppercase tracking-widest mb-6 backdrop-blur-md">
                                Protocol Architecture
                            </div>
                            <h2 className="text-4xl md:text-6xl font-bold mb-4 leading-tight">Two-Layer Impact.<br /><span className="text-green-400">Trust at Scale.</span></h2>
                            <p className="text-gray-400 text-lg max-w-md">
                                Balancing permissionless community proposals with institutional-grade verification.
                            </p>
                        </motion.div>
                    </div>

                    {/* Right Column: Layer Diagram */}
                    <div className="flex flex-col justify-center pointer-events-auto items-center space-y-6">
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            className="w-full max-w-sm p-6 bg-green-500/10 border border-green-500/30 rounded-2xl backdrop-blur-xl relative overflow-hidden group"
                        >
                            <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-100 transition-opacity">
                                <ShieldCheck className="text-green-400" size={16} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Layer 1: Institution</h3>
                            <p className="text-xs text-green-200/60 leading-relaxed">
                                Whitelisted NGOs and established relief organizations. Direct, immediate funding for verified global crises.
                            </p>
                            <div className="mt-4 flex gap-2">
                                <span className="text-[10px] px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">Verified Org</span>
                                <span className="text-[10px] px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">High Trust</span>
                            </div>
                        </motion.div>

                        <div className="h-12 w-px bg-gradient-to-b from-green-500/50 to-blue-500/50 dash-line"></div>

                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            className="w-full max-w-sm p-6 bg-blue-500/10 border border-blue-500/30 rounded-2xl backdrop-blur-xl relative overflow-hidden group"
                        >
                            <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-100 transition-opacity">
                                <Globe className="text-blue-400" size={16} />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Layer 2: Community</h3>
                            <p className="text-xs text-blue-200/60 leading-relaxed">
                                Permissionless proposals for any crisis. Funds move to L1 institutions only upon activation and verification.
                            </p>
                            <div className="mt-4 flex gap-2">
                                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">Permissionless</span>
                                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">L2 Proposal</span>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>


            {/* --- Section 5: No-Loss Yield --- */}
            <section ref={section5Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
                <div className="container mx-auto grid grid-cols-1 md:grid-cols-2 gap-24 align-middle h-full">

                    {/* Left Column: Yield Visual */}
                    <div className="flex flex-col justify-center pointer-events-auto items-center">
                        <div className="relative w-64 h-64 flex items-center justify-center">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                                className="absolute inset-0 border-2 border-dashed border-cyan-500/30 rounded-full"
                            />
                            <motion.div
                                className="bg-black/80 backdrop-blur-2xl border border-cyan-500/50 p-8 rounded-full flex flex-col items-center justify-center shadow-[0_0_50px_rgba(6,182,212,0.2)]"
                            >
                                <Zap className="text-cyan-400 mb-2" size={40} />
                                <span className="text-2xl font-black text-white">YIELD</span>
                                <span className="text-[10px] text-cyan-500 uppercase tracking-tighter">Perpetual Aid</span>
                            </motion.div>
                        </div>
                    </div>

                    {/* Right Column: Title */}
                    <div className="flex flex-col justify-center pointer-events-auto">
                        <motion.div
                            initial={{ opacity: 0, x: 50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.8 }}
                            className="mb-12"
                        >
                            <div className="inline-block px-4 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-bold uppercase tracking-widest mb-6 backdrop-blur-md">
                                Economic Model
                            </div>
                            <h2 className="text-4xl md:text-6xl font-bold mb-4 leading-tight">No-Loss Donations.<br /><span className="text-cyan-400">Impact Forever.</span></h2>
                            <p className="text-gray-400 text-lg max-w-md">
                                Keep your principal. Donate the yield. Powered by Euler and Pendle modules to create sustainable aid.
                            </p>
                        </motion.div>
                    </div>
                </div>
            </section>


            {/* --- Section 6: Tech Stack --- */}
            <section ref={section6Ref} className="min-h-screen w-full flex flex-col items-center pt-20 p-6 relative pointer-events-none">
                <div className="pointer-events-auto max-w-4xl w-full">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-5xl font-bold mb-4">Core Architecture</h2>
                    </motion.div>

                    {/* Circuit Diagram Mockup */}
                    <div className="relative flex flex-col md:flex-row items-center justify-between gap-4">
                        {/* Diagram Nodes (Same as before but scalable) */}
                        <div className="flex flex-col items-center gap-2 z-10 scale-75 md:scale-100">
                            <div className="w-20 h-20 rounded-2xl bg-black border border-white/20 flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.1)]">
                                <span className="font-bold">Intent</span>
                            </div>
                        </div>

                        <div className="h-16 w-1 md:h-1 md:w-full bg-gradient-to-b md:bg-gradient-to-r from-blue-500/20 via-cyan-400 to-blue-500/20 relative">
                            <div className="absolute top-0 left-0 w-full h-full bg-cyan-400 blur-[8px] opacity-50"></div>
                        </div>

                        <div className="flex flex-col items-center gap-2 z-10 scale-75 md:scale-100">
                            <div className="w-24 h-24 rounded-2xl bg-black border border-cyan-500/50 flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.3)]">
                                <div className="text-center">
                                    <span className="font-bold block text-blue-400 mb-1">SpoonOS</span>
                                </div>
                            </div>
                        </div>

                        <div className="h-16 w-1 md:h-1 md:w-full bg-gradient-to-b md:bg-gradient-to-r from-blue-500/20 via-cyan-400 to-blue-500/20 relative">
                            <div className="absolute top-0 left-0 w-full h-full bg-cyan-400 blur-[8px] opacity-50"></div>
                        </div>

                        <div className="flex flex-col items-center gap-2 z-10 scale-75 md:scale-100">
                            <div className="w-20 h-20 rounded-2xl bg-indigo-900/20 border border-indigo-500 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.3)]">
                                <Database className="text-indigo-500" />
                            </div>
                        </div>
                    </div>

                    <div className="mt-16 flex justify-center gap-8 opacity-50 grayscale hover:grayscale-0 transition-all duration-500 relative z-50 pointer-events-auto">
                        <span className="font-mono font-bold">Ethereum</span>
                        <span className="font-mono font-bold">Solidity</span>
                        <span className="font-mono font-bold">IPFS</span>
                    </div>

                </div>
            </section>


            {/* --- Section 7: Call to Action --- */}
            <section ref={section7Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
                <div className="container mx-auto text-center pointer-events-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <h2 className="text-4xl md:text-6xl font-bold mb-8 leading-tight">
                            The world needs you.<br />
                            <span className="text-blue-400">Are you ready?</span>
                        </h2>
                        <button
                            onClick={onLaunch}
                            className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-full font-bold text-lg transition-colors shadow-[0_0_30px_rgba(37,99,235,0.5)]"
                        >
                            Launch OS
                        </button>
                    </motion.div>
                </div>
            </section>

        </div>
    );
}

