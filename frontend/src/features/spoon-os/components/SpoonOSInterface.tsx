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

type Mode = 'IDLE' | 'LISTENING' | 'THINKING' | 'DECISION' | 'SIGNATURE';

interface Message {
    role: 'user' | 'agent';
    content: string;
    response?: AgentResponse;
}

export default function SpoonOSInterface({ isOpen, onClose, selectedPoint, onAction, onStateChange }: SpoonOSInterfaceProps) {
    const [mode, setMode] = useState<Mode>('IDLE');
    const [inputValue, setInputValue] = useState('');
    const [placeholder, setPlaceholder] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const inputRef = useRef<HTMLInputElement>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, mode]);

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
        if (isOpen) {
            // Only force DECISION if we are currently IDLE or LISTENING (collapsed or bar)
            // If we are already THINKING or DECISION, do not disturb the state.
            if (messages.length > 0 && (mode === 'IDLE' || mode === 'LISTENING')) {
                setMode('DECISION');
            } else if (mode === 'IDLE') {
                setMode('LISTENING');
            }
        } else if (!isOpen && mode !== 'IDLE') {
            setMode('IDLE');
        }
    }, [isOpen]); // REMOVED messages.length dependency to prevent auto-switching during chat

    // Notify parent of state for dimming
    useEffect(() => {
        onStateChange?.(mode !== 'IDLE');
    }, [mode, onStateChange]);

    // Auto-focus input
    useEffect(() => {
        if (mode === 'LISTENING' || mode === 'DECISION') {
            // Small delay to allow animation
            setTimeout(() => inputRef.current?.focus(), 150);
        }
    }, [mode]);

    const handleSubmit = async (textOverride?: string) => {
        const textToSend = textOverride || inputValue;
        if (!textToSend.trim()) return;

        // Add user message to history
        const newUserMsg: Message = { role: 'user', content: textToSend };
        setMessages(prev => [...prev, newUserMsg]);
        setInputValue('');

        // Force switch to THINKING (Expanded Mode) immediately
        setMode('THINKING');

        try {
            // Call the Agent Service
            const response = await sendMessageToAgent(textToSend, { selectedPoint });

            // Add agent response to history
            const newAgentMsg: Message = {
                role: 'agent',
                content: response.message,
                response: response
            };
            setMessages(prev => [...prev, newAgentMsg]);

            if (response.ui_hints.mode) {
                // Map legacy PROCESSING to THINKING if needed, though backend likely sends DECISION
                if (response.ui_hints.mode === 'PROCESSING') {
                    setMode('THINKING');
                } else if (response.ui_hints.mode === 'IDLE') {
                    // Prevent collapsing if we just had a conversation step
                    setMode('DECISION');
                } else {
                    setMode(response.ui_hints.mode as Mode);
                }
            } else {
                setMode('DECISION');
            }
        } catch (error) {
            console.error("Agent Error:", error);
            setMessages(prev => [...prev, { role: 'agent', content: "Sorry, I encountered an error. Please try again." }]);
            setMode('DECISION');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSubmit();
        if (e.key === 'Escape') {
            setMode('IDLE');
            onClose();
            // Optional: clear messages on close? 
            // setMessages([]); 
        }
    };

    // Simplified Variants: Explicitly define which modes are Large vs Small
    const variants = {
        IDLE: { width: '320px', height: '60px', borderRadius: '30px', y: 0 },
        LISTENING: { width: '600px', height: '70px', borderRadius: '20px', y: -20 },
        // THINKING is ALWAYS Expanded
        THINKING: { width: '600px', height: '600px', borderRadius: '24px', y: -50 },
        DECISION: { width: '600px', height: '600px', borderRadius: '24px', y: -50 },
        SIGNATURE: { width: '600px', height: 'auto', minHeight: '350px', borderRadius: '32px', y: '-20vh' },
    };

    const isExpandedMode = mode === 'THINKING' || mode === 'DECISION' || mode === 'SIGNATURE';

    return (
        <div className="fixed bottom-[8%] left-1/2 -translate-x-1/2 z-50 flex flex-col items-center justify-end pointer-events-none">
            <motion.div
                initial="IDLE"
                animate={mode}
                variants={variants}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className={`
                    pointer-events-auto overflow-hidden
                    bg-black/85 backdrop-blur-2xl border border-white/10 shadow-2xl
                    flex flex-col relative
                `}
            >
                <AnimatePresence mode="wait">
                    {/* BAR VIEW: Only for IDLE or LISTENING */}
                    {!isExpandedMode && (
                        <motion.div
                            key="bar-ui"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute top-0 left-0 w-full h-full flex items-center px-4 gap-3"
                        >
                            <div className="p-2 rounded-full bg-white/10 text-gray-400">
                                <Mic className="w-5 h-5" />
                            </div>
                            <input
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder={placeholder}
                                className="flex-1 bg-transparent border-none outline-none text-white text-lg placeholder:text-white/30"
                                onClick={() => {
                                    // If we click the bar and have history, go straight to DECISION to show it
                                    if (mode === 'IDLE') {
                                        if (messages.length > 0) setMode('DECISION');
                                        else setMode('LISTENING');
                                    }
                                }}
                            />
                            {mode === 'LISTENING' && inputValue && (
                                <button onClick={() => handleSubmit()} className="p-2 bg-blue-500 rounded-full text-white shadow-lg shadow-blue-500/20 hover:bg-blue-600 transition">
                                    <ArrowRight size={20} />
                                </button>
                            )}
                        </motion.div>
                    )}

                    {/* EXPANDED VIEW: THINKING, DECISION, SIGNATURE */}
                    {isExpandedMode && (
                        <motion.div
                            key="expanded-ui"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col h-full w-full"
                        >
                            {/* Header (Hidden in Signature for focus) */}
                            {mode !== 'SIGNATURE' && (
                                <div className="flex justify-between items-center p-5 border-b border-white/5 bg-white/5">
                                    <div className="flex items-center gap-2">
                                        <div className="bg-blue-500/20 p-1.5 rounded-lg">
                                            {mode === 'THINKING' ? (
                                                <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
                                            ) : (
                                                <Sparkles className="w-4 h-4 text-blue-400" />
                                            )}
                                        </div>
                                        <span className="text-sm font-semibold text-blue-100 uppercase tracking-wider">
                                            {mode === 'THINKING' ? 'Processing...' : 'GaiaLink Agent'}
                                        </span>
                                    </div>
                                    <button onClick={() => { setMode('IDLE'); onClose(); }} className="text-gray-400 hover:text-white p-1 hover:bg-white/10 rounded-full transition">
                                        <X size={20} />
                                    </button>
                                </div>
                            )}

                            <div className="flex-1 overflow-hidden relative">
                                <AnimatePresence mode="wait">
                                    {mode === 'SIGNATURE' ? (
                                        <motion.div
                                            key="signature-content"
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.95 }}
                                            className="flex flex-col p-8 items-center text-center space-y-6 h-full justify-center"
                                        >
                                            <div className="w-20 h-20 bg-yellow-500/20 rounded-full flex items-center justify-center animate-pulse">
                                                <Wallet className="w-10 h-10 text-yellow-400" />
                                            </div>
                                            <div className="space-y-2">
                                                <h3 className="text-2xl font-bold text-white tracking-tight">Security Confirmation</h3>
                                                <p className="text-gray-400 max-w-sm">
                                                    {messages[messages.length - 1]?.content || "Please review and sign the transaction."}
                                                </p>
                                            </div>
                                            <div className="w-full space-y-3 pt-4 px-4">
                                                {messages[messages.length - 1]?.response?.ui_hints.actions?.map((action, idx) => (
                                                    <button
                                                        key={idx}
                                                        onClick={() => {
                                                            onAction(action.type, messages[messages.length - 1]?.response?.transaction_payload);
                                                            setMode('IDLE');
                                                            onClose();
                                                        }}
                                                        className="w-full py-4 bg-yellow-500 text-black font-bold rounded-2xl hover:bg-yellow-400 transition transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2"
                                                    >
                                                        <Send size={20} />
                                                        {action.label}
                                                    </button>
                                                ))}
                                                <button onClick={() => setMode('DECISION')} className="w-full py-3 text-gray-500 hover:text-white transition">
                                                    Cancel & Return to Chat
                                                </button>
                                            </div>
                                        </motion.div>
                                    ) : (
                                        <motion.div
                                            key="chat-content"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            className="flex flex-col h-full"
                                        >
                                            <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar">
                                                {messages.map((msg, idx) => (
                                                    <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                                        <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-md leading-relaxed whitespace-pre-wrap ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white/10 text-gray-100 rounded-tl-none border border-white/5'}`}>
                                                            {msg.content}
                                                        </div>
                                                        {msg.role === 'agent' && msg.response?.ui_hints.actions && (
                                                            <div className="flex flex-wrap gap-2 mt-3 ml-2">
                                                                {msg.response.ui_hints.actions.map((act, aiIdx) => (
                                                                    <button
                                                                        key={aiIdx}
                                                                        onClick={() => {
                                                                            if (act.type.startsWith('select_vault')) handleSubmit(act.label);
                                                                            else {
                                                                                onAction(act.type, selectedPoint);
                                                                                if (act.type !== 'sign_proposal') { setMode('IDLE'); onClose(); }
                                                                            }
                                                                        }}
                                                                        className="px-3 py-1.5 bg-white/5 hover:bg-white/20 border border-white/10 rounded-full text-xs font-medium text-blue-200 transition"
                                                                    >
                                                                        {act.label}
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}

                                                {/* THINKING INDICATOR */}
                                                {mode === 'THINKING' && (
                                                    <div className="flex flex-col items-start animate-pulse">
                                                        <div className="bg-white/5 text-gray-400 px-4 py-3 rounded-2xl rounded-tl-none border border-white/5 flex items-center gap-2">
                                                            <Sparkles className="w-4 h-4 animate-spin-slow text-yellow-400" />
                                                            <span className="text-sm">Thinking...</span>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Input Box */}
                                            <div className="p-4 border-t border-white/5 bg-black/20">
                                                <div className="flex items-center gap-3 bg-white/5 rounded-2xl p-2 px-4 border border-white/10 focus-within:border-blue-500/50 transition">
                                                    <input
                                                        ref={inputRef}
                                                        value={inputValue}
                                                        onChange={(e) => setInputValue(e.target.value)}
                                                        onKeyDown={handleKeyDown}
                                                        placeholder="Ask a follow up..."
                                                        className="flex-1 bg-transparent border-none outline-none text-white text-md placeholder:text-white/20"
                                                    />
                                                    <button
                                                        onClick={() => handleSubmit()}
                                                        disabled={!inputValue.trim() || mode === 'THINKING'}
                                                        className="p-2 bg-blue-500 rounded-xl text-white disabled:opacity-30 transition"
                                                    >
                                                        <Send size={18} />
                                                    </button>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
