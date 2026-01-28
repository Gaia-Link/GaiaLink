'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Globe, ShieldCheck, Heart } from 'lucide-react';

export default function LandingPage() {
    return (
        <main className="min-h-screen bg-black text-white overflow-hidden relative selection:bg-blue-500/30">

            {/* Background Elements */}
            <div className="absolute top-0 left-0 w-full h-full z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[128px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-green-600/20 rounded-full blur-[128px]" />
            </div>

            {/* Navbar */}
            <nav className="relative z-10 container mx-auto px-6 py-6 flex justify-between items-center bg-white/5 backdrop-blur-sm rounded-b-2xl border-b border-white/10">
                <div className="text-2xl font-black tracking-tighter">
                    GAIA<span className="text-blue-500">LINK</span>
                </div>
                <div className="hidden md:flex gap-8 text-sm font-medium text-gray-400">
                    <a href="#features" className="hover:text-white transition-colors">Features</a>
                    <a href="#about" className="hover:text-white transition-colors">Mission</a>
                    <a href="#community" className="hover:text-white transition-colors">Community</a>
                </div>
                <Link href="/app">
                    <button className="bg-white text-black px-6 py-2 rounded-full font-bold hover:bg-gray-200 transition-colors flex items-center gap-2 text-sm">
                        Launch App
                    </button>
                </Link>
            </nav>

            {/* Hero Section */}
            <section className="relative z-10 container mx-auto px-6 pt-32 pb-20 flex flex-col items-center text-center">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    <div className="inline-block px-4 py-1.5 rounded-full border border-white/10 bg-white/5 text-blue-400 text-xs font-bold uppercase tracking-widest mb-6">
                        The Earth is Speaking
                    </div>
                    <h1 className="text-6xl md:text-8xl font-black leading-tight tracking-tighter mb-8">
                        Visualizing <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400">
                            Humanity's Pulse.
                        </span>
                    </h1>
                    <p className="max-w-2xl mx-auto text-xl text-gray-400 mb-10 leading-relaxed">
                        Gaia Link combines 3D visualization, real-time crisis data, and AI agents to create a decentralized humanitarian aid network.
                        See where help is needed. Verify with SpoonOS. Act instantly.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link href="/app">
                            <button className="h-14 px-8 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-bold text-lg transition-all flex items-center gap-2 group shadow-lg shadow-blue-900/20">
                                Enter the Globe
                                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                            </button>
                        </Link>
                        <button className="h-14 px-8 rounded-full border border-white/10 hover:bg-white/5 text-white font-bold text-lg transition-all">
                            Learn More
                        </button>
                    </div>
                </motion.div>
            </section>

            {/* Feature Cards */}
            <section id="features" className="relative z-10 container mx-auto px-6 py-20 border-t border-white/10">
                <div className="grid md:grid-cols-3 gap-8">
                    <FeatureCard
                        icon={<Globe className="text-blue-400" size={32} />}
                        title="Living Globe"
                        desc="Real-time 3D visualization of global crisis points (Red Zones) and community voices (Blue Bubbles)."
                    />
                    <FeatureCard
                        icon={<ShieldCheck className="text-green-400" size={32} />}
                        title="Verified by AI"
                        desc="SpoonOS Agent cross-references Polymarket and news data to filter out misinformation."
                    />
                    <FeatureCard
                        icon={<Heart className="text-red-400" size={32} />}
                        title="Direct Impact"
                        desc="Connect directly with verified organizations and individuals. Donate via crypto with one click."
                    />
                </div>
            </section>
        </main>
    );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
    return (
        <motion.div
            whileHover={{ y: -5 }}
            className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
        >
            <div className="mb-6 p-4 bg-white/5 w-fit rounded-2xl">{icon}</div>
            <h3 className="text-2xl font-bold mb-4">{title}</h3>
            <p className="text-gray-400 leading-relaxed">{desc}</p>
        </motion.div>
    );
}
