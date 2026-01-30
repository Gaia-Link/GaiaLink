'use client';

import { useBlockNumber, useAccount, useBalance } from 'wagmi';
import { sepolia } from 'wagmi/chains';

export default function RpcTester() {
    const { address } = useAccount();
    const { data: blockNumber, isError: isBlockError, error: blockError } = useBlockNumber({
        chainId: sepolia.id,
    });
    const { data: balance, isError: isBalanceError, error: balanceError, isLoading: isBalanceLoading } = useBalance({
        address,
        chainId: sepolia.id,
    });

    return (
        <div className="fixed top-24 right-4 p-4 bg-black/90 border border-yellow-500 rounded-lg z-50 text-xs text-white max-w-sm pointer-events-auto shadow-xl">
            <h3 className="font-bold text-yellow-500 mb-2">⚡️ RPC Debugger (Sepolia)</h3>

            <div className="space-y-2">
                {/* Block Status */}
                <div>
                    <span className="text-gray-400">Block Height:</span>{' '}
                    {blockNumber ? <span className="text-green-400 font-mono">{blockNumber.toString()}</span> : 'Loading...'}
                    {isBlockError && <span className="text-red-400">Error fetching block</span>}
                </div>

                {/* Account Status */}
                <div className="border-t border-white/10 pt-2">
                    <p className="text-gray-400">Address:</p>
                    <p className="font-mono truncate w-full opacity-80">{address || 'Not Connected'}</p>
                </div>

                {/* Balance Status */}
                <div className="border-t border-white/10 pt-2">
                    <p className="text-gray-400">Balance (Raw):</p>
                    {isBalanceLoading ? (
                        <span className="text-yellow-500">Fetching...</span>
                    ) : isBalanceError ? (
                        <div className="text-red-400 break-all bg-red-900/20 p-1 rounded mt-1">
                            {balanceError?.message}
                        </div>
                    ) : (
                        <div>
                            <span className="text-green-400 font-bold text-lg block">
                                {balance ? `${balance.value.toString()} wei` : 'N/A'}
                            </span>
                            {balance && <span className="text-gray-400 font-mono text-[10px]">{balance.formatted} {balance.symbol}</span>}
                        </div>
                    )}
                </div>
            </div>

            <div className="mt-2 pt-2 border-t border-white/20 text-[10px] text-gray-500 flex justify-between">
                <span>Target: 1rpc.io</span>
                <span>Sepolia</span>
            </div>
        </div>
    );
}
