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

    const isInView1 = useInView(section1Ref, { amount: 0.5 });
    const isInView2 = useInView(section2Ref, { amount: 0.5 });
    const isInView3 = useInView(section3Ref, { amount: 0.5 });
    const isInView4 = useInView(section4Ref, { amount: 0.5 });
    const isInView5 = useInView(section5Ref, { amount: 0.5 });

    useEffect(() => {
        if (isInView1) { onSectionChange(0); }
        else if (isInView2) { onSectionChange(1); }
        else if (isInView3) { onSectionChange(2); }
        else if (isInView4) { onSectionChange(3); }
        else if (isInView5) { onSectionChange(4); }
    }, [isInView1, isInView2, isInView3, isInView4, isInView5, onSectionChange]);

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
                        <div className="overflow-hidden mb-8">
                            <motion.p
                                initial={{ y: "100%" }}
                                animate={{ y: 0 }}
                                transition={{ delay: 0.5, duration: 0.8, ease: "circOut" }}
                                className="text-xl md:text-2xl font-mono text-blue-200/80"
                            >
                                "The First Intent-Centric Spatial OS for Humanitarian Aid."
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

                    {/* Right Column: Data Cards (Bento) */}
                    <div className="flex flex-col justify-center pointer-events-auto space-y-4">
                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            className="bg-black/40 backdrop-blur-xl border border-red-500/20 p-6 rounded-2xl flex items-center gap-4"
                        >
                            <Activity className="text-red-500" size={32} />
                            <div>
                                <h3 className="font-bold text-red-100">Opaque Funding</h3>
                                <p className="text-xs text-red-500/50">40% Leakage</p>
                            </div>
                        </motion.div>

                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex items-center gap-4"
                        >
                            <Activity className="text-yellow-500 animate-spin-slow" size={32} />
                            <div>
                                <h3 className="font-bold text-white">Latency</h3>
                                <p className="text-xs text-gray-500">Weeks to Deploy</p>
                            </div>
                        </motion.div>

                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex items-center gap-4"
                        >
                            <Lock className="text-gray-400" size={32} />
                            <div>
                                <h3 className="font-bold text-white">Unverified</h3>
                                <p className="text-xs text-gray-500">Misinformation Risk</p>
                            </div>
                        </motion.div>

                    </div>
                </div>
            </section>


            {/* --- Section 3: The Solution (Split Layout Inverted) --- */}
            <section ref={section3Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
                <div className="container mx-auto grid grid-cols-1 md:grid-cols-2 gap-24 align-middle h-full">

                    {/* Left Column: Features */}
                    <div className="flex flex-col justify-center pointer-events-auto space-y-6">
                        <motion.div className="flex items-center gap-4 text-right justify-end group cursor-default">
                            <div className="text-right">
                                <h3 className="text-xl font-bold text-blue-200">Real-time Vis</h3>
                                <p className="text-blue-500/50 text-xs uppercase">Mapping Data</p>
                            </div>
                            <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 group-hover:bg-blue-500/30 transition-colors">
                                <Globe className="text-blue-400" size={24} />
                            </div>
                        </motion.div>

                        <motion.div className="flex items-center gap-4 text-right justify-end group cursor-default">
                            <div className="text-right">
                                <h3 className="text-xl font-bold text-purple-200">Intent Engine</h3>
                                <p className="text-purple-500/50 text-xs uppercase">AI Processing</p>
                            </div>
                            <div className="p-3 bg-purple-500/10 rounded-xl border border-purple-500/20 group-hover:bg-purple-500/30 transition-colors">
                                <Zap className="text-purple-400" size={24} />
                            </div>
                        </motion.div>

                        <motion.div className="flex items-center gap-4 text-right justify-end group cursor-default">
                            <div className="text-right">
                                <h3 className="text-xl font-bold text-green-200">Verification</h3>
                                <p className="text-green-500/50 text-xs uppercase">On-chain Trust</p>
                            </div>
                            <div className="p-3 bg-green-500/10 rounded-xl border border-green-500/20 group-hover:bg-green-500/30 transition-colors">
                                <ShieldCheck className="text-green-400" size={24} />
                            </div>
                        </motion.div>
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
                                Protocol Activated
                            </div>
                            <h2 className="text-4xl md:text-6xl font-bold mb-4 leading-tight">Spatial Intelligence. <br /><span className="text-blue-400">Powered by Agents.</span></h2>
                        </motion.div>
                    </div>

                </div>
            </section>


            {/* --- Section 4: Tech Stack --- */}
            <section ref={section4Ref} className="min-h-screen w-full flex flex-col items-center pt-20 p-6 relative pointer-events-none">
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


            {/* --- Section 5: Call to Action --- */}
            <section ref={section5Ref} className="min-h-screen w-full flex items-center p-6 relative pointer-events-none">
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

