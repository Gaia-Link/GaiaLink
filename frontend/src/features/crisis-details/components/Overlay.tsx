'use client';

import type { CrisisPoint } from '@/lib/mockData';
import { X, Heart, ShieldCheck, ShieldAlert } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getVerificationStatus, formatLocation } from '../utils/verificationUtils';

export interface OverlayProps {
    point: CrisisPoint | null;
    onClose: () => void;
    onDonate?: (point: CrisisPoint) => void;
}

export default function Overlay({ point, onClose, onDonate }: OverlayProps) {
    if (!point) return null;

    const verification = getVerificationStatus(point);

    return (
        <AnimatePresence>
            <motion.div
                initial={{ x: '100%', opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: '100%', opacity: 0 }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="fixed right-0 top-0 h-full w-full md:w-[480px] bg-black/80 backdrop-blur-md text-white border-l border-white/10 shadow-2xl p-6 z-50 overflow-y-auto"
            >
                <button
                    onClick={onClose}
                    className="absolute top-6 right-6 p-2 hover:bg-white/10 rounded-full transition-colors"
                    aria-label="Close overlay"
                >
                    <X size={24} />
                </button>

                <div className="mt-12 space-y-6">
                    {/* Header */}
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${point.type === 'crisis' ? 'bg-red-500/20 text-red-500' :
                                point.type === 'voice' ? 'bg-blue-500/20 text-blue-400' :
                                    point.type === 'warning' ? 'bg-yellow-500/20 text-yellow-500' :
                                        'bg-green-500/20 text-green-400'
                                }`}>
                                {point.type}
                            </span>
                            <span className="text-gray-400 text-sm">Just now</span>
                        </div>
                        <h2 className="text-3xl font-bold leading-tight">{point.label}</h2>
                    </div>

                    {/* Validation Status (SpoonOS Agent) */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-start gap-4">
                        <div className={`mt-1 p-1 rounded-full ${verification.isVerified ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-500'}`}>
                            {verification.isVerified ? <ShieldCheck size={20} /> : <ShieldAlert size={20} />}
                        </div>
                        <div>
                            <h4 className="font-semibold text-sm mb-1">SpoonOS Analysis</h4>
                            <p className="text-sm text-gray-300">
                                {verification.message}
                                {verification.isVerified && ` Confidence: ${verification.confidence}%.`}
                            </p>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="prose prose-invert">
                        <p className="text-lg text-gray-200 leading-relaxed">
                            {point.description || "No further details available at this moment."}
                        </p>
                        <p className="text-gray-400">
                            Location: {formatLocation(point.lat, point.lng)}
                        </p>
                    </div>

                    {/* Funding & Action Footer */}
                    <div className="space-y-6">
                        <div className="text-center p-6 border border-white/10 rounded-2xl bg-white/5 backdrop-blur-sm">
                            <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">
                                {point.hasVault ? "Vault Balance" : "Pledged / Waiting"}
                            </p>
                            <p className="text-4xl font-mono font-bold text-green-400 mb-4">
                                ${(Number(point.raised || 0) / 1e18).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                <span className="text-sm ml-1 text-gray-500">USDC</span>
                            </p>

                            {point.id.toString().startsWith('temp-') ? (
                                <div className="w-full bg-yellow-500/20 text-yellow-400 font-bold py-4 rounded-xl border border-yellow-500/30 flex items-center justify-center gap-2 animate-pulse cursor-not-allowed">
                                    <ShieldAlert size={20} />
                                    Confirming Deployment...
                                </div>
                            ) : point.hasVault ? (
                                <button
                                    onClick={() => onDonate?.(point)}
                                    className="w-full bg-white text-black font-bold py-4 rounded-xl hover:bg-gray-200 transition-all flex items-center justify-center gap-2 group"
                                >
                                    <Heart size={20} className="text-red-500 group-hover:scale-125 transition-transform" />
                                    Donate More
                                </button>
                            ) : (
                                <div className="space-y-3">
                                    <button
                                        onClick={() => onDonate?.(point)}
                                        className="w-full bg-blue-600 text-white font-bold py-4 rounded-xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2"
                                    >
                                        <Heart size={20} className="text-white" />
                                        Support & Open Vault
                                    </button>
                                    <p className="text-[10px] text-gray-500 leading-relaxed italic">
                                        Funds are held securely by the Gaia Contract. Once an institution verifies and accepts this crisis, the vault will be deployed and funds transferred for immediate aid.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
