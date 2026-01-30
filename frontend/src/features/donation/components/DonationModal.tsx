'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight, ShieldCheck, Wallet, Coins, TrendingUp } from 'lucide-react';
import { CrisisPoint } from '@/lib/mockData';

interface DonationModalProps {
    isOpen: boolean;
    onClose: () => void;
    point: CrisisPoint | null;
}

type DonationType = 'DIRECT' | 'YIELD';

export default function DonationModal({ isOpen, onClose, point }: DonationModalProps) {
    const [amount, setAmount] = useState<string>('');
    const [donationType, setDonationType] = useState<DonationType>('DIRECT');
    const [isSuccess, setIsSuccess] = useState(false);

    if (!isOpen || !point) return null;

    const handleDonate = () => {
        // Simulate transaction
        setTimeout(() => {
            setIsSuccess(true);
        }, 1000);
    };

    const handleClose = () => {
        setIsSuccess(false);
        setAmount('');
        onClose();
    }

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
            >
                <div className="w-full max-w-md bg-[#111] border border-white/10 rounded-2xl shadow-2xl overflow-hidden relative">

                    {isSuccess ? (
                        <div className="p-8 flex flex-col items-center justify-center text-center space-y-4">
                            <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mb-2">
                                <ShieldCheck className="w-10 h-10 text-green-500" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">Donation Successful!</h3>
                            <p className="text-gray-400">
                                You successfully donated <span className="text-white font-mono">{amount} USDC</span> to {point.label}.
                                {donationType === 'YIELD' && <br /> && <span className="text-blue-400 text-sm mt-2 block">Yield farming active via Euler Finance. Protocol APY: 4.5%</span>}
                            </p>
                            <button onClick={handleClose} className="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-3 rounded-xl transition mt-4">
                                Close
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* Header */}
                            <div className="p-6 border-b border-white/10">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h2 className="text-xl font-bold text-white">Make a Donation</h2>
                                        <p className="text-sm text-gray-400">Target: {point.label}</p>
                                    </div>
                                    <button onClick={onClose} className="text-gray-500 hover:text-white transition">
                                        <X size={24} />
                                    </button>
                                </div>
                            </div>

                            {/* Type Selection */}
                            <div className="p-6 space-y-6">
                                <div className="space-y-3">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Donation Type</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        <button
                                            onClick={() => setDonationType('DIRECT')}
                                            className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition ${donationType === 'DIRECT'
                                                    ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                                                    : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'
                                                }`}
                                        >
                                            <Coins size={24} />
                                            <span className="font-semibold text-sm">Direct Give</span>
                                        </button>
                                        <button
                                            onClick={() => setDonationType('YIELD')}
                                            className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition relative overflow-hidden ${donationType === 'YIELD'
                                                    ? 'bg-purple-600/20 border-purple-500 text-purple-400'
                                                    : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'
                                                }`}
                                        >
                                            <div className="absolute top-1 right-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] px-1.5 py-0.5 rounded font-bold">
                                                No-Loss
                                            </div>
                                            <TrendingUp size={24} />
                                            <span className="font-semibold text-sm">Yield Give</span>
                                        </button>
                                    </div>
                                    <p className="text-xs text-gray-500 h-4">
                                        {donationType === 'DIRECT'
                                            ? "Funds are transferred directly to the verified wallet immediately."
                                            : "Principal is deposited into DeFi protocols; yield is donated automatically."}
                                    </p>
                                </div>

                                {/* Amount Input */}
                                <div className="space-y-3">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Amount (USDC)</label>
                                    <div className="relative">
                                        <input
                                            type="number"
                                            value={amount}
                                            onChange={(e) => setAmount(e.target.value)}
                                            placeholder="0.00"
                                            className="w-full bg-black/40 border border-white/10 rounded-xl py-4 pl-4 pr-16 text-2xl font-mono text-white focus:outline-none focus:border-blue-500 transition"
                                        />
                                        <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold">
                                            USDC
                                        </div>
                                    </div>
                                </div>

                                {/* Agent Option */}
                                <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-900/10 border border-blue-900/30">
                                    <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                                        <Wallet size={18} />
                                    </div>
                                    <div className="flex-1">
                                        <h4 className="text-sm font-semibold text-blue-200">SpoonOS Agent Pay (X402)</h4>
                                        <p className="text-xs text-blue-400/70">Agent handles gas & verification</p>
                                    </div>
                                    <div className="h-5 w-5 rounded border border-blue-500/50 bg-blue-500 flex items-center justify-center">
                                        <ShieldCheck size={12} className="text-white" />
                                    </div>
                                </div>

                                <button
                                    onClick={handleDonate}
                                    disabled={!amount}
                                    className="w-full bg-white text-black font-bold py-4 rounded-xl hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
                                >
                                    <span>Confirm {donationType === 'YIELD' ? 'Deposit' : 'Donation'}</span>
                                    <ArrowRight size={18} />
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
