'use client';

import { useMemo, useState } from 'react';
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

    const markers = useMemo(() => data.map((point, index) => {
        const size = getLabelSizeByType(point.type) * 20; // Scale base size suitable for markers
        const color = getColorByType(point.type);

        return (
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
                    }}
                    title={point.label}
                />
            </Marker>
        );
    }), [data, onPointClick]);

    return (
        <div className="fixed inset-0 z-0 bg-black">
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
                fog={{
                    range: [0.5, 10],
                    color: '#3a228a', // Same atmosphere color as before
                    'horizon-blend': 0.1,
                    // Note: 'star-intensity' might not be standard in all maplibre versions but let's try
                }}
                terrain={{ source: 'raster-dem', exaggeration: 1.5 }}
            >
                {markers}
                <NavigationControl position="bottom-right" />
            </Map>
        </div>
    );
}
