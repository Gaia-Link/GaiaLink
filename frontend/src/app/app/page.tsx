'use client';

import { useState } from 'react';
import LivingGlobe from '@/features/globe/components/LivingGlobe';
import Overlay from '@/features/forum/components/Overlay';
import { CrisisPoint, MOCK_DATA } from '@/lib/mockData';
import { ConnectButton } from '@rainbow-me/rainbowkit';

export default function Home() {
  const [selectedPoint, setSelectedPoint] = useState<CrisisPoint | null>(null);

  const handleDonate = (point: CrisisPoint) => {
    // TODO: Implement donation logic with SpoonOS Agent
    console.log('Donating to:', point.label);
  };

  const handleDiscuss = (point: CrisisPoint) => {
    // TODO: Implement discussion/forum logic
    console.log('Discussing:', point.label);
  };

  return (
    <main className="relative h-screen w-full overflow-hidden">
      {/* 1. The Living Globe (Background Layer) - data is now explicitly passed */}
      <LivingGlobe data={MOCK_DATA} onPointClick={setSelectedPoint} />

      {/* 2. UI Overlay Layer (Foreground) */}
      <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-start z-10 pointer-events-none">
        {/* Brand / Title */}
        <div className="pointer-events-auto">
          <h1 className="text-4xl font-black text-white tracking-tighter drop-shadow-lg">
            GAIA<span className="text-blue-400">LINK</span>
          </h1>
          <p className="text-white/70 text-sm max-w-xs mt-2 drop-shadow-md">
            Decentralized Humanitarian Aid Network. <br />
            Visualize. Verify. Act.
          </p>
        </div>

        {/* Wallet Connect */}
        <div className="pointer-events-auto">
          <ConnectButton />
        </div>
      </div>

      {/* 3. Interaction Layer (Geo-Forum) */}
      <Overlay
        point={selectedPoint}
        onClose={() => setSelectedPoint(null)}
        onDonate={handleDonate}
        onDiscuss={handleDiscuss}
      />

      {/* Instructions / Footer */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/50 text-xs pointer-events-none z-0">
        Click on Red Zones to view requests. Hold Space to speak to SpoonOS.
      </div>
    </main>
  );
}
