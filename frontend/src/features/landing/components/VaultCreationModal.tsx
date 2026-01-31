import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Target, Save, Loader2, Sparkles, Shield, Zap } from 'lucide-react';
import { useWriteContract, useWaitForTransactionReceipt, usePublicClient, useAccount } from 'wagmi';
import { GAIA_PROPOSAL_MANAGER_ABI } from '@/lib/abis';
import { PROPOSAL_MANAGER_ADDRESS } from '@/lib/constants';
import { CONTRACTS } from '@/lib/contracts';
import { CrisisPoint } from '@/lib/mockData';

interface VaultCreationModalProps {
    isOpen: boolean;
    onClose: () => void;
    coords: { lat: number, lng: number } | null;
    onProposalCreated?: (point: CrisisPoint) => void;
}

export default function VaultCreationModal({ isOpen, onClose, coords, onProposalCreated }: VaultCreationModalProps) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [targetAmount, setTargetAmount] = useState('');
    const [isNoLoss, setIsNoLoss] = useState(false); // Toggle for Direct vs No-Loss

    // Wagmi Hooks
    const { writeContractAsync, isPending } = useWriteContract();
    const publicClient = usePublicClient();
    const { address: userAddress } = useAccount();

    const [txHash, setTxHash] = useState<`0x${string}` | undefined>(undefined);

    const { isLoading: isConfirming, isSuccess } = useWaitForTransactionReceipt({
        hash: txHash,
    });

    const handleDeploy = async () => {
        if (!coords) return;

        try {
            // 1. Prepare Metadata
            // We encode the "Type" into the metadata string for the demo frontend to parse
            // 1a. Pre-flight Check: Verify Charity Active
            try {
                // We can't easily read from here without a hook, but relying on simulation is better.
                console.log("Pre-flight: encoding arguments...");
            } catch (e) {
                console.warn("Pre-flight check skipped");
            }

            // 1. Prepare Metadata
            const metadataString = JSON.stringify({
                description: description,
                isNoLossPriority: isNoLoss
            });

            const args = [
                1n, // _charityId (1 is Red Cross)
                CONTRACTS.MockERC20,
                name,
                metadataString,
                BigInt(Math.round(coords.lat * 10000)), // Explicit BigInt for int24
                BigInt(Math.round(coords.lng * 10000)), // Explicit BigInt for int24
                1,
                BigInt(30 * 24 * 60 * 60)
            ];
            console.log("Creating Proposal with Args:", args);

            // 2. Simulate First (Robust Pattern)
            if (!publicClient || !userAddress) throw new Error("Wallet not ready");

            console.log("Simulating real deployment...");
            const { request } = await publicClient.simulateContract({
                account: userAddress,
                address: PROPOSAL_MANAGER_ADDRESS,
                abi: GAIA_PROPOSAL_MANAGER_ABI,
                functionName: 'createProposal',
                args: args as any,
            });

            // 3. Execute Transaction
            const hash = await writeContractAsync(request);

            console.log('Transaction sent:', hash);
            setTxHash(hash);

            // 3. Optimistic UI Update (Call immediately for instant feedback, or wait for receipt)
            // For better UX, we'll notify the parent to show the marker optimistically.

            if (onProposalCreated) {
                const newPoint: CrisisPoint = {
                    id: `temp-${Date.now()}`,
                    lat: coords.lat,
                    lng: coords.lng,
                    intensity: 1.0,
                    label: name,
                    type: isNoLoss ? 'voice' : 'crisis', // Visual distinction: Voice(Teal) for NoLoss, Crisis(Yellow/Red) for Direct
                    description: description,
                    hasVault: true, // It's a proposal, but we show as active for demo
                    // Custom field to track type if needed
                };
                onProposalCreated(newPoint);
            }

            alert(`Transaction Sent! Hash: ${hash}`);
            onClose();

            // Reset Form 
            setName('');
            setDescription('');
            setTargetAmount('');
            setTxHash(undefined);

        } catch (error: any) {
            console.error("Deployment failed:", error);

            // Extract logic for user-friendly errors
            const msg = error.shortMessage || error.message || "Unknown error";
            if (msg.includes("User rejected")) {
                // Ignore user rejection
                return;
            }
            alert(`Deployment Failed: ${msg}\n\nCheck console for details.`);
        }
    };

    if (!isOpen) return null;

    const isLoading = isPending || isConfirming;

    return (
        <AnimatePresence>
            <motion.div
                className="fixed inset-0 z-50 flex items-center justify-center p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
            >
                {/* Backdrop */}
                <div
                    className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                    onClick={onClose}
                />

                {/* Modal */}
                <motion.div
                    className="relative w-full max-w-lg bg-gray-900 border border-blue-500/30 rounded-2xl shadow-[0_0_50px_rgba(59,130,246,0.2)] overflow-hidden"
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                >
                    {/* Header */}
                    <div className="p-6 border-b border-white/10 bg-black/40 flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                                <Target size={20} />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Deploy New Vault</h2>
                                <p className="text-xs text-blue-400/70 font-mono">
                                    LAT: {coords?.lat.toFixed(4)} • LNG: {coords?.lng.toFixed(4)}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/10 rounded-full text-white/50 hover:text-white transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    {/* Body */}
                    <div className="p-6 space-y-4">
                        {/* Funding Type Toggle */}
                        <div className="flex bg-black/50 p-1 rounded-lg border border-white/10">
                            <button
                                onClick={() => setIsNoLoss(false)}
                                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md transition-all ${!isNoLoss ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                <Zap size={16} />
                                <span className="text-xs font-bold uppercase">Direct Impact</span>
                            </button>
                            <button
                                onClick={() => setIsNoLoss(true)}
                                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md transition-all ${isNoLoss ? 'bg-purple-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                <Shield size={16} />
                                <span className="text-xs font-bold uppercase">No-Loss Protocol</span>
                            </button>
                        </div>

                        <p className="text-xs text-center text-gray-500">
                            {isNoLoss
                                ? "Principal is preserved. Only yield is donated."
                                : "100% of funds go directly to the cause."}
                        </p>

                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">
                                Vault Name
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g. Clean Water Initiative"
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-blue-500 transition-colors"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">
                                Description
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe the mission..."
                                rows={3}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-blue-500 transition-colors resize-none"
                            />
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-white/10 bg-black/40 flex justify-end gap-3">
                        <button
                            onClick={async () => {
                                if (!publicClient || !coords || !userAddress) {
                                    alert("Client/Coords/User not ready");
                                    return;
                                }
                                try {
                                    const metadataString = JSON.stringify({
                                        description: description,
                                        isNoLossPriority: isNoLoss
                                    });
                                    const args = [
                                        1n, // Charity 1
                                        CONTRACTS.MockERC20,
                                        name || "Debug Proposal",
                                        metadataString,
                                        BigInt(Math.round(coords.lat * 10000)),
                                        BigInt(Math.round(coords.lng * 10000)),
                                        1,
                                        BigInt(30 * 24 * 60 * 60)
                                    ];
                                    console.log("Simulating with:", args);
                                    const { request } = await publicClient.simulateContract({
                                        account: userAddress,
                                        address: PROPOSAL_MANAGER_ADDRESS,
                                        abi: GAIA_PROPOSAL_MANAGER_ABI,
                                        functionName: 'createProposal',
                                        args: args as any
                                    });
                                    alert(`Simulation Success! Gas: ${request.gas}`);
                                } catch (e: any) {
                                    console.error("Simulation Error:", e);
                                    alert(`Simulation Failed: ${e.message?.split('\n')[0]}`);
                                }
                            }}
                            className="px-4 py-2 rounded-lg text-sm font-bold text-yellow-500 hover:bg-yellow-500/10 transition-colors"
                        >
                            Debug
                        </button>
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-sm font-bold text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleDeploy}
                            disabled={!name || isLoading}
                            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold text-sm shadow-lg transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${isNoLoss ? 'bg-purple-600 hover:bg-purple-500 shadow-purple-600/20' : 'bg-blue-600 hover:bg-blue-500 shadow-blue-600/20'} text-white`}
                        >
                            {isLoading ? (
                                <Loader2 size={16} className="animate-spin" />
                            ) : (
                                <Sparkles size={16} />
                            )}
                            {isLoading ? 'Confirming...' : 'Deploy Proposal'}
                        </button>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
