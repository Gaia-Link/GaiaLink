'use client';

import { useState, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Wallet, ShieldCheck, TrendingUp, Coins, ChevronDown, ChevronUp, Loader2, ArrowUpRight } from 'lucide-react';
import { useAccount, useReadContracts, useReadContract, usePublicClient, useWatchContractEvent, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { formatUnits, parseAbiItem } from 'viem';
import { useQuery } from '@tanstack/react-query';
import { PROPOSAL_MANAGER_ADDRESS } from '@/lib/constants';
import { GAIA_PROPOSAL_MANAGER_ABI, GAIA_NO_LOSS_VAULT_ABI, GAIA_STRATEGY_ABI } from '@/lib/abis';
import { useProposals } from '@/hooks/useProposals';

interface UserPortfolioModalProps {
    isOpen: boolean;
    onClose: () => void;
}

// Simple Cache for block timestamps to avoid redundant RPC calls
const GLOBAL_BLOCK_TIME_CACHE: Record<number, number> = {};

export default function UserPortfolioModal({ isOpen, onClose }: UserPortfolioModalProps) {
    const { address } = useAccount();
    const publicClient = usePublicClient();
    const [activeTab, setActiveTab] = useState<'portfolio' | 'history'>('portfolio');
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const { writeContractAsync } = useWriteContract();

    // Fetch real proposals from chain
    const proposals = useProposals();

    // Use React Query for History Log
    const { data: history = [], isLoading: isHistoryLoading, refetch: refetchHistory } = useQuery({
        queryKey: ['donationHistory', address, proposals.length],
        queryFn: async () => {
            if (!address || !publicClient) return [];
            console.log("QUERY_FETCHING_HISTORY...");

            const logs = await publicClient.getLogs({
                address: PROPOSAL_MANAGER_ADDRESS,
                event: parseAbiItem('event FundsDeposited(uint256 indexed proposalId, address indexed user, uint256 amount, bool isNoLoss)'),
                args: {
                    user: address
                },
                fromBlock: 'earliest'
            });

            const historyWithMeta = await Promise.all(logs.map(async (log: any) => {
                const blockNumber = Number(log.blockNumber);

                let timestamp: number;
                if (GLOBAL_BLOCK_TIME_CACHE[blockNumber]) {
                    timestamp = GLOBAL_BLOCK_TIME_CACHE[blockNumber];
                } else {
                    const block = await publicClient.getBlock({ blockNumber: log.blockNumber });
                    timestamp = Number(block.timestamp) * 1000;
                    GLOBAL_BLOCK_TIME_CACHE[blockNumber] = timestamp;
                }

                const pid = Number(log.args.proposalId);
                const point = proposals.find(p => parseInt(p.id) === pid);

                return {
                    hash: log.transactionHash,
                    proposalId: log.args.proposalId,
                    amount: log.args.amount,
                    isNoLoss: log.args.isNoLoss,
                    timestamp,
                    pointLabel: point?.label || `Project #${pid}`,
                    pointDescription: point?.description || 'Loading details...',
                    location: point ? `${point.lat.toFixed(2)}, ${point.lng.toFixed(2)}` : '...'
                };
            }));

            return historyWithMeta.sort((a, b) => b.timestamp - a.timestamp);
        },
        enabled: isOpen && !!address && !!publicClient,
        staleTime: 10000, // Consider data fresh for 10s
    });

    // Watch for new donations in real-time
    useWatchContractEvent({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        eventName: 'FundsDeposited',
        poll: true, // Local chain needs polling
        onLogs(logs) {
            console.log("WATCH_EVENT_FIRED", logs.length, "logs");
            const hasUserLog = logs.some(log => (log as any).args.user?.toLowerCase() === address?.toLowerCase());
            if (hasUserLog) {
                console.log("NEW_USER_LOG_DETECTED! Invalidating query...");
                refetchHistory();
            }
        },
    });

    // -------------------------------------------------------------------------
    // Portfolio Fetching (Bulk)
    // -------------------------------------------------------------------------
    const { data: portfolioItems, isLoading: isPortfolioLoading, refetch: refetchPortfolio } = useReadContract({
        address: PROPOSAL_MANAGER_ADDRESS,
        abi: GAIA_PROPOSAL_MANAGER_ABI,
        functionName: 'getUserPortfolio',
        args: [address!],
        query: {
            enabled: !!address && isOpen
        }
    });

    // Map bulk data to internal structure
    interface BalanceMap {
        directAmount: bigint;
        noLossAmount: bigint;
    }

    // Convert array to map for easy lookup by proposalId
    const balances = useMemo(() => {
        if (!portfolioItems) return [];
        return (portfolioItems as any[]).map((item) => ({
            result: {
                directAmount: item.directAmount,
                noLossAmount: item.noLossAmount
            }
        }));
    }, [portfolioItems]);

    // Helper to get balance for a specific PID (to keep existing logic working)
    const getBalance = (pid: number) => {
        if (!portfolioItems) return { direct: 0n, noLoss: 0n };
        const item = (portfolioItems as any[]).find((p: any) => Number(p.proposalId) === pid);
        return {
            direct: item ? item.directAmount : 0n,
            noLoss: item ? item.noLossAmount : 0n
        };
    };



    // -------------------------------------------------------------------------
    // Withdrawal Logic
    // -------------------------------------------------------------------------
    const handleWithdraw = async (point: any, amount: bigint, isNoLoss: boolean) => {
        try {
            const pid = BigInt(point.id);
            let hash: `0x${string}` | undefined;

            if (!point.accepted) {
                // Pending: Withdraw from ProposalManager
                hash = await writeContractAsync({
                    address: PROPOSAL_MANAGER_ADDRESS,
                    abi: GAIA_PROPOSAL_MANAGER_ABI,
                    functionName: 'withdrawFromProposal',
                    args: [pid]
                });
            } else if (isNoLoss && point.noLossVault && point.noLossVault !== '0x0000000000000000000000000000000000000000') {
                // Accepted No-Loss: Withdraw from Vault
                hash = await writeContractAsync({
                    address: point.noLossVault,
                    abi: GAIA_NO_LOSS_VAULT_ABI,
                    functionName: 'withdraw',
                    args: [amount]
                });
            }

            if (hash && publicClient) {
                console.log("Withdrawal submitted, waiting for confirmation:", hash);
                await publicClient.waitForTransactionReceipt({ hash });
                console.log("Withdrawal confirmed, refetching balances...");
                await Promise.all([
                    refetchPortfolio(),
                    refetchHistory()
                ]);
            }
        } catch (e) {
            console.error("Withdrawal failed:", e);
        }
    };

    // -------------------------------------------------------------------------
    // Yield Fetching (Batch)
    // -------------------------------------------------------------------------

    // 1. Fetch Strategy and Total Principal for all No-Loss Vaults
    const vaultCalls = useMemo(() => proposals.map((p) => {
        if (p.accepted && p.noLossVault && p.noLossVault !== '0x0000000000000000000000000000000000000000') {
            return [
                {
                    address: p.noLossVault as `0x${string}`,
                    abi: GAIA_NO_LOSS_VAULT_ABI,
                    functionName: 'strategy',
                },
                {
                    address: p.noLossVault as `0x${string}`,
                    abi: GAIA_NO_LOSS_VAULT_ABI,
                    functionName: 'totalPrincipal',
                }
            ];
        }
        return [];
    }).flat(), [proposals]);

    const { data: batchVaultData, isLoading: isVaultDataLoading } = useReadContracts({
        contracts: vaultCalls as any,
        query: { enabled: proposals.length > 0 && isOpen }
    });

    // 2. Fetch Total Assets for all Strategies
    const strategyCalls = useMemo(() => {
        if (!batchVaultData) return [];
        const calls: any[] = [];
        for (let i = 0; i < batchVaultData.length; i += 2) {
            const strategyAddr = batchVaultData[i]?.result as `0x${string}` | undefined;
            if (strategyAddr) {
                calls.push({
                    address: strategyAddr,
                    abi: GAIA_STRATEGY_ABI,
                    functionName: 'totalAssets',
                });
            }
        }
        return calls;
    }, [batchVaultData]);

    const { data: batchStrategyData, isLoading: isStrategyDataLoading } = useReadContracts({
        contracts: strategyCalls as any,
        query: { enabled: strategyCalls.length > 0 && isOpen }
    });

    // -------------------------------------------------------------------------
    // Render Functions
    // -------------------------------------------------------------------------

    // Helper to get yield for a specific proposal
    const getYieldData = (proposalId: string) => {
        const pointIndex = proposals.findIndex(p => p.id === proposalId);
        if (pointIndex === -1) return { globalYield: 0n, totalPrincipal: 0n, strategyAddr: undefined };

        // Find the index in vaultData/strategyData
        let vaultDataIndex = 0;
        let strategyDataIndex = 0;
        for (let i = 0; i < pointIndex; i++) {
            const p = proposals[i];
            if (p.accepted && p.noLossVault && p.noLossVault !== '0x0000000000000000000000000000000000000000') {
                vaultDataIndex += 2;
                strategyDataIndex += 1;
            }
        }

        const p = proposals[pointIndex];
        if (!(p.accepted && p.noLossVault && p.noLossVault !== '0x0000000000000000000000000000000000000000')) {
            return { globalYield: 0n, totalPrincipal: 0n, strategyAddr: undefined };
        }

        const strategyAddr = batchVaultData?.[vaultDataIndex]?.result as `0x${string}` | undefined;
        const totalPrincipal = batchVaultData?.[vaultDataIndex + 1]?.result as bigint | undefined;
        const totalAssets = batchStrategyData?.[strategyDataIndex]?.result as bigint | undefined;

        const globalYield = totalAssets && totalPrincipal ? (totalAssets > totalPrincipal ? totalAssets - totalPrincipal : 0n) : 0n;

        return { globalYield, totalPrincipal: totalPrincipal || 0n, strategyAddr };
    };

    // Calculate total yield share for the user across all donations
    const activeDonations = proposals.map((point, index) => {
        const balance = balances?.[index]?.result;
        if (!balance) return null;

        const direct = balance.directAmount as bigint;
        const noLoss = balance.noLossAmount as bigint;

        if (direct === 0n && noLoss === 0n) return null;

        const { globalYield, totalPrincipal } = getYieldData(point.id);

        let userYieldShare = 0n;
        if (noLoss > 0n && totalPrincipal > 0n) {
            userYieldShare = (noLoss * globalYield) / totalPrincipal;
        }

        return {
            point,
            direct,
            noLoss,
            userYieldShare,
            globalYield,
            isGlobalYieldLoading: (isVaultDataLoading || isStrategyDataLoading) && point.accepted && !!point.noLossVault
        };
    }).filter(Boolean) as any[];

    const totalUserYield = activeDonations.reduce((acc, item) => acc + (item.userYieldShare || 0n), 0n);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[70] flex items-center justify-center bg-black/90 backdrop-blur-xl p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    className="w-full max-w-lg relative overflow-hidden group"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Cyberpunk Border & Glow */}
                    <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/30 via-transparent to-pink-500/30 rounded-2xl opacity-50 blur-xl group-hover:opacity-70 transition-opacity duration-1000"></div>
                    <div className="absolute inset-[1px] bg-black/95 rounded-2xl z-0 backdrop-blur-md"></div>
                    <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-pink-600 rounded-2xl opacity-20 blur-sm pointer-events-none"></div>

                    {/* Content Container */}
                    <div className="relative z-10 flex flex-col h-[600px] max-h-[80vh] rounded-2xl border border-white/5">

                        {/* Header */}
                        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/5 relative overflow-hidden shrink-0">
                            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>
                            <div className="flex items-center gap-4">
                                <div className="p-2.5 bg-cyan-900/20 border border-cyan-500/30 rounded-lg text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                                    <Wallet size={20} className="drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-white tracking-wider uppercase font-mono">
                                        Neural Portfolio
                                    </h2>
                                    <p className="text-[10px] text-cyan-500/60 font-mono tracking-widest uppercase">
                                        ID: {address ? `${address.slice(0, 6)}...${address.slice(-4)}` : 'DISCONNECTED'}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="text-gray-500 hover:text-white transition hover:rotate-90 duration-300"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-white/5 bg-black/40 shrink-0">
                            <button
                                onClick={() => setActiveTab('portfolio')}
                                className={`flex-1 py-3 text-sm font-mono uppercase tracking-wider transition-colors ${activeTab === 'portfolio' ? 'text-cyan-400 bg-cyan-900/10 border-b-2 border-cyan-500' : 'text-gray-500 hover:text-white'}`}
                            >
                                Active Assets
                            </button>
                            <button
                                onClick={() => setActiveTab('history')}
                                className={`flex-1 py-3 text-sm font-mono uppercase tracking-wider transition-colors ${activeTab === 'history' ? 'text-cyan-400 bg-cyan-900/10 border-b-2 border-cyan-500' : 'text-gray-500 hover:text-white'}`}
                            >
                                History log
                            </button>
                        </div>

                        {/* Scroll Content */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar relative">
                            {!address ? (
                                <div className="text-center py-12 text-gray-600 font-mono text-sm">
                                    [SYSTEM ERROR]: UPLINK_DISCONNECTED
                                </div>
                            ) : activeTab === 'portfolio' ? (
                                // PORTFOLIO VIEW
                                isPortfolioLoading ? (
                                    <div className="text-center py-12">
                                        <div className="inline-block w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                                        <p className="mt-4 text-cyan-500/50 text-xs font-mono animate-pulse">SCANNING BLOCKCHAIN NODES...</p>
                                    </div>
                                ) : activeDonations.length === 0 ? (
                                    <div className="text-center py-12 space-y-4 border border-dashed border-white/10 rounded-xl bg-white/5">
                                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto text-gray-700">
                                            <ShieldCheck size={32} />
                                        </div>
                                        <div>
                                            <p className="text-gray-400 font-mono text-sm">NO_ACTIVE_SIGNALS_FOUND</p>
                                            <p className="text-xs text-gray-600 mt-1 max-w-[200px] mx-auto">
                                                Funds may have been bridged to Vaults or no contributions detected.
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {/* Total Summary Section */}
                                        <div className="p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-white/10 rounded-xl relative overflow-hidden group/summary">
                                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover/summary:opacity-30 transition-opacity">
                                                <TrendingUp size={64} className="text-cyan-400" />
                                            </div>
                                            <div className="relative z-10 flex justify-between items-center">
                                                <div>
                                                    <p className="text-[10px] text-cyan-500/60 font-mono uppercase tracking-widest mb-1">Total Bio-Yield Generated</p>
                                                    <div className="flex items-baseline gap-2">
                                                        <span className="text-3xl font-mono font-bold text-white tracking-tighter">
                                                            +{formatUnits(totalUserYield, 18)}
                                                        </span>
                                                        <span className="text-sm font-sans text-gray-400">USDC</span>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="p-2 bg-white/5 border border-white/10 rounded-lg backdrop-blur-md">
                                                        <div className="flex items-center gap-1.5 text-cyan-400 mb-0.5">
                                                            <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></div>
                                                            <span className="text-[9px] font-bold uppercase tracking-wider font-mono">Live Impact</span>
                                                        </div>
                                                        <p className="text-[8px] text-gray-500 max-w-[80px] leading-tight font-mono uppercase">Neural nodes syncing yield...</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {activeDonations.map((item: any, i: number) => {
                                            const isExpanded = expandedId === item.point.id;
                                            return (
                                                <motion.div
                                                    key={item.point.id}
                                                    initial={{ opacity: 0, x: -20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: i * 0.1 }}
                                                    className="group relative bg-[#0a0a0a] border border-white/10 hover:border-cyan-500/50 rounded-xl p-1 overflow-hidden transition-all hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] cursor-pointer"
                                                    onClick={() => setExpandedId(isExpanded ? null : item.point.id)}
                                                >
                                                    {/* Card Glow */}
                                                    <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-100 transition-opacity duration-500">
                                                        <div className="w-20 h-20 bg-cyan-500/20 rounded-full blur-xl"></div>

                                                    </div>

                                                    <div className="bg-[#111]/80 backdrop-blur-sm rounded-lg p-4 relative z-10 h-full">
                                                        <div className="flex justify-between items-start mb-4 border-b border-white/5 pb-3">
                                                            <div>
                                                                <h3 className="font-bold text-white text-lg font-sans">
                                                                    {item.point.label}
                                                                </h3>
                                                                <div className="flex items-center gap-2 mt-1.5">
                                                                    <span className={`text-[9px] px-1.5 py-0.5 rounded-sm font-bold uppercase tracking-widest border ${item.point.type === 'crisis'
                                                                        ? 'bg-red-900/20 border-red-500/30 text-red-400'
                                                                        : 'bg-blue-900/20 border-blue-500/30 text-blue-400'
                                                                        }`}>
                                                                        {item.point.type}
                                                                    </span>
                                                                    <span className="text-[10px] text-gray-500 font-mono uppercase">
                                                                        {item.point.accepted ? 'Accepted' : 'Pending'}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            {isExpanded ? <ChevronUp size={20} className="text-gray-500" /> : <ChevronDown size={20} className="text-gray-500" />}
                                                        </div>

                                                        <div className="grid grid-cols-2 gap-3">
                                                            {item.direct > 0n && (
                                                                <div className="p-3 bg-gradient-to-br from-blue-900/10 to-transparent border border-blue-500/20 rounded-lg">
                                                                    <div className="flex items-center gap-2 mb-1 text-blue-400">
                                                                        <Coins size={14} />
                                                                        <span className="text-[10px] font-bold uppercase tracking-wider">Direct</span>
                                                                    </div>
                                                                    <div className="text-xl font-mono font-bold text-white">
                                                                        {formatUnits(item.direct, 18)} <span className="text-[10px] text-gray-500 font-sans">USDC</span>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {item.noLoss > 0n && (
                                                                <div className="p-3 bg-gradient-to-br from-purple-900/10 to-transparent border border-purple-500/20 rounded-lg">
                                                                    <div className="flex items-center gap-2 mb-1 text-purple-400">
                                                                        <TrendingUp size={14} />
                                                                        <span className="text-[10px] font-bold uppercase tracking-wider">No-Loss</span>
                                                                    </div>
                                                                    <div className="text-xl font-mono font-bold text-white">
                                                                        {formatUnits(item.noLoss, 18)} <span className="text-[10px] text-gray-500 font-sans">USDC</span>
                                                                    </div>
                                                                    {item.userYieldShare > 0n && (
                                                                        <div className="mt-1 flex items-center gap-1 text-[10px] font-bold text-purple-400/80 animate-pulse">
                                                                            <TrendingUp size={10} />
                                                                            +{formatUnits(item.userYieldShare, 18)} YIELD
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>

                                                        <AnimatePresence>
                                                            {isExpanded && (
                                                                <motion.div
                                                                    initial={{ height: 0, opacity: 0 }}
                                                                    animate={{ height: 'auto', opacity: 1 }}
                                                                    exit={{ height: 0, opacity: 0 }}
                                                                    className="overflow-hidden"
                                                                >
                                                                    <div className="mt-4 pt-4 border-t border-white/5 space-y-4">
                                                                        {/* Yield Dashboard */}
                                                                        {(item.noLoss > 0n && item.point.accepted) && (
                                                                            <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                                                                                <div className="flex justify-between items-center mb-3">
                                                                                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest font-mono">Impact Dashboard</h4>
                                                                                    <span className="text-[10px] text-cyan-400/80 font-mono animate-pulse">LIVE_FEED</span>
                                                                                </div>
                                                                                <div className="grid grid-cols-2 gap-4">
                                                                                    <div>
                                                                                        <p className="text-[9px] text-gray-500 uppercase font-mono mb-1">Global Yield</p>
                                                                                        <div className="text-sm font-mono text-white flex items-center gap-1.5">
                                                                                            {item.isGlobalYieldLoading ? <Loader2 size={12} className="animate-spin text-gray-600" /> : formatUnits(item.globalYield, 18)}
                                                                                            <span className="text-[9px] text-gray-500">USDC</span>
                                                                                        </div>
                                                                                    </div>
                                                                                    <div className="text-right">
                                                                                        <p className="text-[9px] text-purple-400/80 uppercase font-mono mb-1">Your Contribution</p>
                                                                                        <div className="text-sm font-mono text-purple-400 font-bold flex items-center justify-end gap-1.5">
                                                                                            +{item.isGlobalYieldLoading ? '...' : formatUnits(item.userYieldShare, 18)}
                                                                                            <ArrowUpRight size={12} />
                                                                                        </div>
                                                                                    </div>
                                                                                </div>
                                                                                <div className="mt-3 pt-3 border-t border-white/5">
                                                                                    <p className="text-[9px] text-gray-600 font-mono italic">
                                                                                        Yield is automatically sent to {item.point.label}'s treasury.
                                                                                    </p>
                                                                                </div>
                                                                            </div>
                                                                        )}

                                                                        {/* Withdrawal Section */}
                                                                        <div className="space-y-3">
                                                                            <p className="text-[10px] text-gray-500 font-mono uppercase">Liquidity Management</p>
                                                                            <button
                                                                                onClick={(e) => {
                                                                                    e.stopPropagation();
                                                                                    handleWithdraw(item.point, item.noLoss + item.direct, item.noLoss > 0n);
                                                                                }}
                                                                                className="w-full py-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:border-red-500/50 text-white font-mono text-sm uppercase transition-all flex items-center justify-center gap-2 group/btn"
                                                                            >
                                                                                Withdraw All Principal
                                                                                <ArrowUpRight size={16} className="group-hover/btn:translate-x-1 group-hover/btn:-translate-y-1 transition-transform" />
                                                                            </button>
                                                                            {!item.point.accepted && (
                                                                                <p className="text-[9px] text-yellow-500/60 font-mono text-center">
                                                                                    Withdrawals are instant while proposal is pending.
                                                                                </p>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>
                                                    </div>
                                                </motion.div>
                                            );
                                        })}
                                    </div>
                                )
                            ) : (
                                // HISTORY VIEW
                                isHistoryLoading ? (
                                    <div className="text-center py-12">
                                        <div className="inline-block w-6 h-6 border-2 border-cyan-500 border-b-transparent rounded-full animate-spin"></div>
                                        <p className="mt-2 text-cyan-500/50 text-xs font-mono">DECRYPTING LOGS...</p>
                                    </div>
                                ) : history.length === 0 ? (
                                    <div className="text-center py-8">
                                        <p className="text-sm text-gray-500 font-mono">NO_TRANSACTIONS_FOUND</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {history.map((tx, i) => (
                                            <motion.div
                                                key={tx.hash + i}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: i * 0.05 }}
                                                className="bg-white/5 border border-white/5 rounded-lg p-3 hover:bg-white/10 transition-colors flex justify-between items-center"
                                            >
                                                <div>
                                                    <div className="text-sm font-bold text-gray-200">{tx.pointLabel}</div>
                                                    <div className="text-[10px] text-cyan-500/80 font-mono uppercase tracking-wider mt-0.5">
                                                        {tx.location} • {tx.pointDescription}
                                                    </div>
                                                    <div className="text-[10px] text-gray-600 font-mono mt-0.5">
                                                        {new Date(tx.timestamp).toLocaleString()}
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="font-mono text-cyan-400 font-bold">
                                                        +{formatUnits(tx.amount, 18)}
                                                    </div>
                                                    <div className={`text-[10px] uppercase font-bold tracking-wider ${tx.isNoLoss ? 'text-purple-500' : 'text-blue-500'}`}>
                                                        {tx.isNoLoss ? 'No-Loss' : 'Direct'}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                )
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-white/5 bg-black/40 text-center relative shrink-0">
                            <p className="text-[10px] text-gray-600 font-mono uppercase tracking-[0.2em]">
                                Secure Connection • Gaia Protocol v1.0
                            </p>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
