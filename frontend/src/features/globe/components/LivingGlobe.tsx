'use client';

import React, { useMemo, useState } from 'react';
import Map, { Marker, NavigationControl } from 'react-map-gl/maplibre';
import type { CrisisPoint } from '@/lib/mockData';

export interface LivingGlobeProps {
    data: CrisisPoint[];
    onPointClick: (point: CrisisPoint) => void;
}

export default function LivingGlobe({ data, onPointClick }: LivingGlobeProps) {
    const [viewState, setViewState] = useState({
        longitude: 0,
        latitude: 20,
        zoom: 1.5
    });
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const getMarkerColor = (point: CrisisPoint) => {
        if (point.type === 'voice') return '#4FD1C5'; // Teal for voice
        if (point.type === 'node') return '#63B3ED'; // Blue for nodes

        // Crisis logic:
        if (point.hasVault) {
            return '#F6E05E'; // Golden/Yellow for Active Vaults (Money!)
        } else {
            return '#F56565'; // Red for Needs/Alerts (No Vault yet)
        }
    };

    const markers = useMemo(() => data.map((point) => {
        const size = point.hasVault ? 24 : 12 + (point.intensity * 10); // Reduced size: 24px for Vault, 12-22px for others
        const color = getMarkerColor(point);
        const isSelected = selectedId === point.id;

        return (
            <Marker
                key={point.id}
                longitude={point.lng}
                latitude={point.lat}
                anchor="center"
                onClick={e => {
                    e.originalEvent.stopPropagation();
                    onPointClick(point);
                    setSelectedId(point.id);
                }}
            >
                <div
                    className="flex flex-col items-center justify-center cursor-pointer transition-all duration-300 group"
                    style={{
                        transform: isSelected ? 'scale(1.2)' : 'scale(1)',
                        zIndex: isSelected ? 50 : 1
                    }}
                >
                    {/* Main Dot */}
                    <div
                        style={{
                            width: `${size}px`,
                            height: `${size}px`,
                            borderRadius: '50%',
                            backgroundColor: color,
                            boxShadow: `0 0 ${isSelected ? 20 : 10}px ${color}`,
                            border: '2px solid rgba(0,0,0,0.5)',
                            transition: 'all 0.3s ease',
                            animation: point.intensity > 0.7 ? 'pulse 2s infinite' : 'none'
                        }}
                        className="relative flex items-center justify-center"
                    >
                        {/* Icon or Inner Dot */}
                        {point.hasVault && (
                            <div className="text-black font-bold text-[10px]">$</div>
                        )}
                    </div>

                    {/* Hover Label */}
                    <div className="absolute top-full mt-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/80 px-2 py-1 rounded text-xs text-white whitespace-nowrap pointer-events-none z-50">
                        {point.label}
                    </div>
                </div>
            </Marker>
        );
    }), [data, onPointClick, selectedId]);

    return (
        <div className="w-full h-full bg-black">
            <style jsx global>{`
                @keyframes pulse {
                    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 60, 60, 0.7); }
                    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 60, 60, 0); }
                    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 60, 60, 0); }
                }
            `}</style>
            <Map
                {...viewState}
                onMove={evt => setViewState(evt.viewState)}
                style={{ width: '100%', height: '100%' }}
                mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
                projection="globe"
                terrain={{ source: 'raster-dem', exaggeration: 1.5 }}
            >
                {markers}
                <NavigationControl position="bottom-right" />
            </Map>
        </div>
    );
}
