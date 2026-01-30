'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Sparkles, ArrowRight, Wallet, Coins, TrendingUp, X } from 'lucide-react';
import { CrisisPoint } from '@/lib/mockData';

interface SpoonOSInterfaceProps {
    isOpen: boolean; // Managed by parent (Space key)
    onClose: () => void; // To close/reset
    selectedPoint: CrisisPoint | null;
    onAction: (action: string, data?: any) => void;
    onStateChange?: (isActive: boolean) => void; // To dim background
}

type Mode = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'DECISION' | 'SIGNATURE';

export default function SpoonOSInterface({ isOpen, onClose, selectedPoint, onAction, onStateChange }: SpoonOSInterfaceProps) {
    const [mode, setMode] = useState<Mode>('IDLE');
    const [inputValue, setInputValue] = useState('');
    const [placeholder, setPlaceholder] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    // Typewriter effect text
    const prompts = ["Type to help Turkey...", "Press Space to activate...", "Ask about Gaza relief...", "Verify donation needs..."];

    useEffect(() => {
        let currentPrompt = 0;
        let charIndex = 0;
        let isDeleting = false;
        let timeoutId: NodeJS.Timeout;

        const type = () => {
            const currentText = prompts[currentPrompt];

            if (isDeleting) {
                setPlaceholder(currentText.substring(0, charIndex - 1));
                charIndex--;
            } else {
                setPlaceholder(currentText.substring(0, charIndex + 1));
                charIndex++;
            }

            let typeSpeed = isDeleting ? 50 : 100;

            if (!isDeleting && charIndex === currentText.length) {
                typeSpeed = 2000; // Pause at end
                isDeleting = true;
            } else if (isDeleting && charIndex === 0) {
                isDeleting = false;
                currentPrompt = (currentPrompt + 1) % prompts.length;
                typeSpeed = 500;
            }

            timeoutId = setTimeout(type, typeSpeed);
        };

        if (mode === 'IDLE') {
            timeoutId = setTimeout(type, 100);
        } else {
            setPlaceholder("How can I help?");
        }

        return () => clearTimeout(timeoutId);
    }, [mode]);

    // Handle Parent Open Signal (Space Key)
    useEffect(() => {
        if (isOpen && mode === 'IDLE') {
            setMode('LISTENING');
        } else if (!isOpen && mode !== 'IDLE') {
            // If parent says close, we reset, unless we are deep in flow? 
            // Actually parent toggle usually just means "activate". 
            // We'll let internal state manage closure mostly, but respect explicit False if needed.
        }
    }, [isOpen]);

    // Notify parent of state for dimming
    useEffect(() => {
        onStateChange?.(mode !== 'IDLE');
    }, [mode, onStateChange]);

    // Auto-focus input
    useEffect(() => {
        if (mode === 'LISTENING') {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [mode]);

    const handleSubmit = () => {
        if (!inputValue.trim()) return;
        setMode('PROCESSING');

        // Mock processing delay
        setTimeout(() => {
            // Simple mock logic
            const lower = inputValue.toLowerCase();
            if (lower.includes('donate')) {
                setMode('DECISION');
            } else if (lower.includes('verify')) {
                // Just show decision for now as generic response
                setMode('DECISION');
            } else {
                setMode('DECISION'); // Default flow for demo
            }
        }, 1500);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSubmit();
        if (e.key === 'Escape') {
            setMode('IDLE');
            onClose();
        }
    };

    // Dynamic Styles based on Mode
    const variants = {
        IDLE: { width: '320px', height: '60px', borderRadius: '30px', y: 0 },
        LISTENING: { width: '600px', height: '70px', borderRadius: '20px', y: -20 },
        PROCESSING: { width: '600px', height: '70px', borderRadius: '20px', y: -20 },
        DECISION: { width: '400px', height: '450px', borderRadius: '24px', y: -100 },
        SIGNATURE: { width: '400px', height: '200px', borderRadius: '24px', y: -100 },
    };

    return (
        <div className="fixed bottom-[8%] left-1/2 -translate-x-1/2 z-50 flex flex-col items-center justify-end pointer-events-none">
            {/* The Capsule Container */}
            <motion.div
                initial="IDLE"
                animate={mode}
                variants={variants}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className={`
            pointer-events-auto overflow-hidden
            bg-black/60 backdrop-blur-xl border border-white/10 shadow-2xl
            flex flex-col relative
         `}
            >
                {/* IDLE / LISTENING / PROCESSING Content (The "Bar") */}
                <AnimatePresence mode="wait">
                    {(mode === 'IDLE' || mode === 'LISTENING' || mode === 'PROCESSING') && (
                        <motion.div
                            key="input-bar"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute top-0 left-0 w-full h-full flex items-center px-4 gap-3"
                        >
                            <div className={`p-2 rounded-full ${mode === 'LISTENING' ? 'bg-blue-500 text-white' : 'bg-white/10 text-gray-400'}`}>
                                {mode === 'PROCESSING' ? (
                                    <Sparkles className="w-5 h-5 animate-pulse text-yellow-400" />
                                ) : (
                                    <Mic className="w-5 h-5" />
                                )}
                            </div>

                            <input
                                ref={inputRef}
                                disabled={mode !== 'LISTENING'}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={placeholder}
                                className="flex-1 bg-transparent border-none outline-none text-white text-lg placeholder:text-white/30"
                                onClick={() => setMode('LISTENING')} // Click to wake
                            />

                            {mode === 'LISTENING' && inputValue && (
                                <button onClick={handleSubmit} className="p-2 bg-white/10 rounded-full hover:bg-white/20 text-white transition">
                                    <ArrowRight size={20} />
                                </button>
                            )}
                        </motion.div>
                    )}

                    {/* RESPONSE / DECISION CARD */}
                    {mode === 'DECISION' && (
                        <motion.div
                            key="decision-card"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className="flex flex-col h-full p-6"
                        >
                            {/* Header */}
                            <div className="flex justify-between items-start mb-6">
                                <div className="flex items-center gap-2">
                                    <div className="bg-blue-500/20 p-1.5 rounded-lg">
                                        <Sparkles className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <span className="text-sm font-semibold text-blue-200">SpoonOS Analysis</span>
                                </div>
                                <button onClick={() => { setMode('IDLE'); onClose(); }} className="text-gray-500 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="flex-1 space-y-4">
                                <p className="text-lg text-white font-medium leading-relaxed">
                                    I've located <span className="text-blue-400 font-bold">{selectedPoint?.label || "the target zone"}</span>.
                                    Urgency is <span className="text-red-400 font-bold">CRITICAL</span>.
                                    <br /><br />
                                    Verification confirmed by 3 sources via Polymarket.
                                </p>
                            </div>

                            {/* Actions */}
                            <div className="grid grid-cols-2 gap-3 mt-6">
                                <button
                                    onClick={() => {
                                        onAction('OPEN_DONATION', selectedPoint);
                                        setMode('IDLE');
                                    }}
                                    className="bg-white/10 hover:bg-white/20 border border-white/5 rounded-2xl p-4 flex flex-col items-center gap-2 transition group"
                                >
                                    <Coins className="w-8 h-8 text-blue-400 group-hover:scale-110 transition" />
                                    <span className="font-semibold text-white">Direct Donate</span>
                                </button>
                                <button
                                    onClick={() => {
                                        onAction('OPEN_DONATION', selectedPoint); // Or specific yield action
                                        setMode('IDLE');
                                    }}
                                    className="bg-white/10 hover:bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-white/5 rounded-2xl p-4 flex flex-col items-center gap-2 transition group relative overflow-hidden"
                                >
                                    <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-green-500/20 text-green-400 text-[10px] font-bold rounded">APY 4.5%</div>
                                    <TrendingUp className="w-8 h-8 text-purple-400 group-hover:scale-110 transition" />
                                    <span className="font-semibold text-white">Yield Donate</span>
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
