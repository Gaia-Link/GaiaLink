'use client';

import React, { useMemo, useState } from 'react';
import Map, { Marker, NavigationControl } from 'react-map-gl/maplibre';
import maplibregl from 'maplibre-gl';
import type { CrisisPoint } from '@/lib/mockData';
import { getColorByType, getLabelSizeByType } from '../utils/globeUtils';

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

    const markers = useMemo(() => {
        const allMarkers: React.ReactNode[] = [];

        data.forEach((point, index) => {
            const size = getLabelSizeByType(point.type) * 8;
            const color = getColorByType(point.type);

            // 1. Main Marker
            allMarkers.push(
                <Marker
                    key={`marker-${index}`}
                    longitude={point.lng}
                    latitude={point.lat}
                    anchor="center"
                    onClick={(e) => {
                        e.originalEvent.stopPropagation();
                        onPointClick(point);
                    }}
                >
                    <div
                        style={{
                            width: `${size}px`,
                            height: `${size}px`,
                            backgroundColor: color,
                            borderRadius: '50%',
                            cursor: 'pointer',
                            boxShadow: `0 0 ${point.intensity ? point.intensity * 20 : 10}px ${color}`,
                            animation: point.type === 'crisis' ? 'pulse 2s infinite' : 'none',
                            zIndex: 10
                        }}
                        title={point.label}
                    />
                </Marker>
            );

            // 2. Satellite Dots for Density/Urgency (Only for Crisis)
            if (point.type === 'crisis' && point.intensity && point.intensity > 0.5) {
                const count = Math.floor(point.intensity * 8); // More dots = higher urgency/need
                for (let i = 0; i < count; i++) {
                    const angle = (Math.PI * 2 * i) / count;
                    const radius = (0.2 + Math.random() * 0.3); // Reduced radius (approx 20-50km spread depending on lat)
                    const latOffset = (Math.cos(angle) * radius);
                    const lngOffset = (Math.sin(angle) * radius);

                    allMarkers.push(
                        <Marker
                            key={`marker-${index}-sat-${i}`}
                            longitude={point.lng + lngOffset}
                            latitude={point.lat + latOffset}
                            anchor="center"
                        >
                            <div
                                style={{
                                    width: '6px',
                                    height: '6px',
                                    backgroundColor: color,
                                    borderRadius: '50%',
                                    opacity: 0.6,
                                    animation: `pulse ${1 + Math.random()}s infinite alternate`
                                }}
                            />
                        </Marker>
                    );
                }
            }
        });

        return allMarkers;
    }, [data, onPointClick]);

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
