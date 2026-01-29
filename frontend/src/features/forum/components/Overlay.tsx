'use client';

import type { CrisisPoint } from '@/lib/mockData';
import { X, MessageCircle, Heart, ShieldCheck, ShieldAlert } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getVerificationStatus, formatLocation } from '../utils/verificationUtils';

export interface OverlayProps {
    point: CrisisPoint | null;
    onClose: () => void;
    onDonate?: (point: CrisisPoint) => void;
    onDiscuss?: (point: CrisisPoint) => void;
}

export default function Overlay({ point, onClose, onDonate, onDiscuss }: OverlayProps) {
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

                    {/* Action Buttons */}
                    <div className="flex gap-4 pt-4">
                        <button
                            onClick={() => onDonate?.(point)}
                            className="flex-1 bg-white text-black font-bold py-3 px-6 rounded-full hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
                        >
                            <Heart size={20} className="text-red-500" />
                            Donate
                        </button>
                        <button
                            onClick={() => onDiscuss?.(point)}
                            className="flex-1 bg-white/10 text-white font-bold py-3 px-6 rounded-full hover:bg-white/20 transition-colors flex items-center justify-center gap-2"
                        >
                            <MessageCircle size={20} />
                            Discuss
                        </button>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
