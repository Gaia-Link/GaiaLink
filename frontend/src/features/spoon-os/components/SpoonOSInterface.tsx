'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Sparkles, ArrowRight, Wallet, Coins, TrendingUp, X } from 'lucide-react';
import { CrisisPoint } from '@/lib/mockData';
import { sendMessageToAgent, AgentResponse } from '../services/agentService';

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
    const [agentResponse, setAgentResponse] = useState<AgentResponse | null>(null); // Store response
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
        console.log('SpoonOS isOpen:', isOpen, 'mode:', mode);
        if (isOpen && mode === 'IDLE') {
            setMode('LISTENING');
        } else if (!isOpen && mode !== 'IDLE') {
            setMode('IDLE');
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

    const handleSubmit = async (textOverride?: string) => {
        const textToSend = textOverride || inputValue;
        if (!textToSend.trim()) return;

        setInputValue(textToSend); // Show what was selected
        setMode('PROCESSING');

        try {
            // Call the Agent Service
            const response = await sendMessageToAgent(textToSend, { selectedPoint });
            setAgentResponse(response);

            if (response.ui_hints.mode) {
                setMode(response.ui_hints.mode as Mode);
            } else {
                setMode('DECISION');
            }
        } catch (error) {
            console.error("Agent Error:", error);
            setMode('IDLE');
        }
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
        DECISION: { width: '480px', height: '500px', borderRadius: '24px', y: -100 }, // Taller/Wider
        // Signature: Large, Centered, Auto height for content safety
        SIGNATURE: { width: '600px', height: 'auto', minHeight: '350px', borderRadius: '32px', y: '-40vh' },
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
            bg-black/80 backdrop-blur-xl border border-white/10 shadow-2xl
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
                                <button onClick={() => handleSubmit()} className="p-2 bg-white/10 rounded-full hover:bg-white/20 text-white transition">
                                    <ArrowRight size={20} />
                                </button>
                            )}
                        </motion.div>
                    )}

                    {/* RESPONSE / DECISION / SIGNATURE CARD */}
                    {(mode === 'DECISION' || mode === 'SIGNATURE') && agentResponse && (
                        <motion.div
                            key="decision-card"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className="flex flex-col h-full p-6 text-center items-center" // Centered text for signature
                        >
                            {/* Header */}
                            <div className="flex justify-between items-start w-full mb-4">
                                <div className="flex items-center gap-2 text-left">
                                    <div className="bg-blue-500/20 p-1.5 rounded-lg">
                                        <Sparkles className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <div className="flex flex-col text-left">
                                        <span className="text-sm font-semibold text-blue-200">SpoonOS Analysis</span>
                                        {agentResponse.ui_hints.display_data && (
                                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded w-fit mt-1 ${agentResponse.ui_hints.display_data.badge_color === 'green' ? 'bg-green-500/20 text-green-400' :
                                                agentResponse.ui_hints.display_data.badge_color === 'yellow' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    'bg-red-500/20 text-red-400'
                                                }`}>
                                                {agentResponse.ui_hints.display_data.badge_text}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <button onClick={() => { setMode('IDLE'); onClose(); }} className="text-gray-500 hover:text-white">
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="flex-1 flex flex-col justify-center items-center space-y-4 w-full">
                                {mode === 'SIGNATURE' && <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center mb-2"><Wallet className="w-8 h-8 text-yellow-400" /></div>}
                                <p className="text-lg text-white font-medium leading-relaxed">
                                    {agentResponse.message}
                                </p>
                            </div>

                            {/* Actions */}
                            <div className="grid grid-cols-1 w-full gap-3 mt-6">
                                {agentResponse.ui_hints.actions?.map((action, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => {
                                            if (action.type.startsWith('select_vault')) {
                                                handleSubmit(action.label); // Conversational turn
                                            } else {
                                                onAction(action.type, selectedPoint);
                                                if (action.type !== 'sign_proposal') setMode('IDLE');
                                            }
                                        }}
                                        className={`
                                            bg-white/10 hover:bg-white/20 border border-white/5 rounded-2xl p-4 flex items-center justify-center gap-3 transition group w-full
                                            ${action.type === 'sign_proposal' ? 'bg-yellow-500/20 border-yellow-500/30 hover:bg-yellow-500/30' : ''}
                                        `}
                                    >
                                        {action.icon === 'coins' && <Coins className="w-5 h-5 text-blue-400" />}
                                        {action.icon === 'trending_up' && <TrendingUp className="w-5 h-5 text-purple-400" />}
                                        {action.icon === 'wallet' && <Wallet className="w-5 h-5 text-gray-400" />}
                                        {action.icon === 'pen-tool' && <Send className="w-5 h-5 text-yellow-400" />}

                                        <span className="font-semibold text-white text-md">{action.label}</span>
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
