'use client';

import React, { useMemo, useState, useEffect } from 'react';
import Map, { Marker, NavigationControl } from 'react-map-gl/maplibre';
import type { CrisisPoint } from '@/lib/mockData';

export interface LivingGlobeProps {
    data: CrisisPoint[];
    onPointClick: (point: CrisisPoint) => void;
    onMapClick?: (coords: { lat: number, lng: number }) => void;
    isLaunched?: boolean;
    activeSection?: number;
    scrollProgress?: number;
    flyToLocation?: { lng: number, lat: number } | null;
}

export default function LivingGlobe({ data, onPointClick, onMapClick, isLaunched = true, activeSection = 0, scrollProgress = 0, flyToLocation }: LivingGlobeProps) {
    const mapRef = useRef<any>(null); // Reference to map instance
    const [viewState, setViewState] = useState({
        longitude: 0,
        latitude: 0, // Center the globe vertically
        zoom: 2.3, // Larger globe size
        pitch: 0, // Flat view for initial landing
        bearing: 0,
        padding: { left: 0, right: 0, top: 0, bottom: 0 } as any
    });
    const [selectedId, setSelectedId] = useState<string | null>(null);

    // Effect: Handle Cinematic Transitions & Scroll Rotation
    useEffect(() => {
        if (isLaunched) {
            setViewState(prev => ({
                ...prev,
                padding: { left: 0, right: 0, top: 0, bottom: 0 },
                transitionDuration: 1000,
            }));
            return;
        }

        // Calculate rotation based on scroll progress
        // Start at longitude 0 (center), rotate smoothly as user scrolls
        let targetLong = scrollProgress * 360; // Start centered, rotate 360° through scroll
        let targetLat = 0; // Keep globe centered vertically
        let targetZoom = 2.3; // Larger globe size
        let targetPitch = 0; // Keep flat for consistent view
        let targetBearing = 0; // No camera rotation, only globe spins

        console.log('🌍 Globe Rotation - scrollProgress:', scrollProgress, 'targetLong:', targetLong);

        // Note: Removed section-based zoom/pitch changes to maintain consistent globe size/position

        // Update viewState with minimal transition for smooth scroll-linked rotation
        setViewState(prev => ({
            ...prev,
            longitude: targetLong,
            latitude: targetLat,
            zoom: targetZoom,
            pitch: targetPitch,
            bearing: targetBearing,
            padding: { left: 0, right: 0, top: 0, bottom: 0 },
            // Very small duration for real-time scroll response
            transitionDuration: 50,
            transitionEasing: (t: number) => t // Linear for predictable motion
        } as any));

    }, [activeSection, isLaunched, scrollProgress]);

    // Effect: Handle Agent FlyTo Commands
    useEffect(() => {
        if (flyToLocation) {
            console.log("✈️ Flying to location:", flyToLocation);
            setViewState(prev => ({
                ...prev,
                longitude: flyToLocation.lng,
                latitude: flyToLocation.lat,
                zoom: 4, // Closer zoom for specific locations
                transitionDuration: 2000,
                transitionEasing: (t: number) => t * (2 - t) // Ease-out
            }));
        }
    }, [flyToLocation]);


    const getMarkerColor = (point: CrisisPoint) => {
        if (point.type === 'voice') return '#4FD1C5'; // Teal for voice
        if (point.type === 'node') return '#63B3ED'; // Blue for nodes
        if (point.type === 'warning') return '#F6E05E'; // Yellow for warnings

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
                    if (isLaunched) { // Only clickable when launched
                        onPointClick(point);
                        setSelectedId(point.id);
                    }
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
                    <div className={`absolute top-full mt-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/80 px-2 py-1 rounded text-xs text-white whitespace-nowrap pointer-events-none z-50 ${!isLaunched ? 'hidden' : ''}`}>
                        {point.label}
                    </div>
                </div>
            </Marker>
        );
    }), [data, onPointClick, selectedId, isLaunched]);

    return (
        <div className="w-full h-full bg-black relative">
            <style jsx global>{`
                @keyframes pulse {
                    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 60, 60, 0.7); }
                    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 60, 60, 0); }
                    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 60, 60, 0); }
                }
            `}</style>

            {/* Visual Overlays for Scrollytelling */}
            {!isLaunched && activeSection === 1 && (
                <div className="absolute inset-0 z-10 pointer-events-none mix-blend-overlay bg-red-900/40 backdrop-contrast-125 transition-all duration-1000"></div>
            )}
            {!isLaunched && activeSection === 1 && (
                <div className="absolute inset-0 z-10 pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
            )}


            <Map
                {...viewState}
                onMove={evt => {
                    if (isLaunched) setViewState(evt.viewState); // Only allow manual move if launched
                }}
                style={{ width: '100%', height: '100%' }}
                mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
                projection="globe"
                terrain={{ source: 'raster-dem', exaggeration: 1.5 }}
                // Disable interactions if not launched
                scrollZoom={isLaunched}
                dragPan={isLaunched}
                dragRotate={isLaunched}
                doubleClickZoom={isLaunched}
                touchZoomRotate={isLaunched}
                onClick={(e) => {
                    if (isLaunched && onMapClick) {
                        onMapClick({ lat: e.lngLat.lat, lng: e.lngLat.lng });
                    }
                }}
            >
                {markers}
                {isLaunched && <NavigationControl position="bottom-right" />}
            </Map>
        </div>
    );
}
