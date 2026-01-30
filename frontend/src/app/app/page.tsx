'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Overlay from '@/features/forum/components/Overlay';
import SpoonOSInterface from '@/features/spoon-os/components/SpoonOSInterface';
import DonationModal from '@/features/donation/components/DonationModal';
import LivingGlobe from '@/features/globe/components/LivingGlobe';
import { CrisisPoint, MOCK_DATA } from '@/lib/mockData';
import { ConnectButton } from '@rainbow-me/rainbowkit';

export default function Home() {
  const [selectedPoint, setSelectedPoint] = useState<CrisisPoint | null>(null);
  const [isSpoonActive, setIsSpoonActive] = useState(false); // Controls dimming
  const [triggerSpoon, setTriggerSpoon] = useState(false);   // Signal to wake up spoon
  const [isDonationOpen, setIsDonationOpen] = useState(false);
  const [data, setData] = useState<CrisisPoint[]>([]);

  // Toggle SpoonOS with Spacebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent triggering if typing in an input
      if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return;

      if (e.code === 'Space') {
        e.preventDefault();
        if (!e.repeat) {
          setTriggerSpoon(true); // Signal to wake
          setTimeout(() => setTriggerSpoon(false), 100); // Reset signal
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Fetch crisis data from our local API (which reads backend_data/data.json)
  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/crises');
        const json = await res.json();
        if (json.crises) {
          // Transform backend data format to frontend CrisisPoint format if needed
          // For now, assuming distinct fields map cleanly or we just use raw
          // We map 'location' { lat, lng } to top level lat/lng for LivingGlobe
          const mappedData = json.crises.map((c: any) => ({
            id: c.id,
            lat: c.location.lat,
            lng: c.location.lng,
            intensity: c.severity === 'CRITICAL' ? 1.0 : c.severity === 'HIGH' ? 0.8 : 0.5,
            label: c.title,
            type: 'crisis', // distinguish from 'voice' or others if needed
            description: c.description,
            hasVault: c.vaults && c.vaults.length > 0 // Map backend vault existence
          }));
          setData(mappedData);
        }
      } catch (e) {
        console.error("Failed to fetch crises", e);
      }
    }
    fetchData();
  }, []);

  const handleDonate = (point: CrisisPoint) => {
    setSelectedPoint(point);
    setIsDonationOpen(true);
  };

  const handleDiscuss = (point: CrisisPoint) => {
    // TODO: Implement discussion/forum logic
    console.log('Discussing:', point.label);
  };

  const handleSpoonAction = (action: string, data?: any) => {
    if (action === 'OPEN_DONATION') {
      // setIsSpoonActive(false); // Let component handle its own state
      setIsDonationOpen(true);
      if (data) setSelectedPoint(data);
    }
  };

  return (
    <main className="relative h-screen w-full overflow-hidden bg-black">
      {/* 1. The Living Globe (Background Layer) */}
      <div className={`absolute inset-0 z-0 transition-all duration-700 ${isSpoonActive ? 'scale-95 opacity-50 blur-sm rounded-3xl overflow-hidden' : 'scale-100 opacity-100 blur-0'}`}>
        <LivingGlobe data={data} onPointClick={setSelectedPoint} />
      </div>

      {/* 2. UI Overlay Layer (Foreground) */}
      <div className={`absolute top-0 left-0 w-full p-6 flex justify-between items-start z-10 pointer-events-none transition-opacity duration-500 ${isSpoonActive ? 'opacity-20' : 'opacity-100'}`}>
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

      {/* 3. Interaction Components */}
      <Overlay
        point={selectedPoint}
        onClose={() => setSelectedPoint(null)}
        onDonate={handleDonate}
        onDiscuss={handleDiscuss}
      />

      <SpoonOSInterface
        isOpen={triggerSpoon}
        onClose={() => setTriggerSpoon(false)}
        selectedPoint={selectedPoint}
        onAction={handleSpoonAction}
        onStateChange={setIsSpoonActive}
      />

      <DonationModal
        isOpen={isDonationOpen}
        onClose={() => setIsDonationOpen(false)}
        point={selectedPoint}
      />

      {/* Instructions / Footer */}
      <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 text-white/50 text-xs pointer-events-none z-0 transition-opacity ${isSpoonActive ? 'opacity-0' : 'opacity-100'}`}>
        Click on Red Zones to view requests. Press <span className="font-bold text-white">SPACE</span> to speak to SpoonOS.
      </div>
    </main>
  );
}
