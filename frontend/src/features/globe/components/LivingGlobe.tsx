'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import type { CrisisPoint } from '@/lib/mockData';
import { getColorByType, getLabelSizeByType, getDotRadiusByType } from '../utils/globeUtils';

// Dynamically import Globe to avoid SSR issues
const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

export interface LivingGlobeProps {
    data: CrisisPoint[];
    onPointClick: (point: CrisisPoint) => void;
}

export default function LivingGlobe({ data, onPointClick }: LivingGlobeProps) {
    const globeEl = useRef<any>(undefined);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

    useEffect(() => {
        setDimensions({
            width: window.innerWidth,
            height: window.innerHeight
        });

        const handleResize = () => {
            setDimensions({
                width: window.innerWidth,
                height: window.innerHeight
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className="fixed inset-0 z-0 bg-black">
            <Globe
                ref={globeEl}
                width={dimensions.width}
                height={dimensions.height}
                globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
                backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"

                // Data Visualization - now uses injected data
                labelsData={data}
                labelLat={(d: any) => d.lat}
                labelLng={(d: any) => d.lng}
                labelText={(d: any) => d.label}
                labelSize={(d: any) => getLabelSizeByType(d.type)}
                labelDotRadius={(d: any) => getDotRadiusByType(d.type)}
                labelColor={(d: any) => getColorByType(d.type)}
                labelResolution={2}

                // Interaction
                onLabelClick={(d: any) => onPointClick(d)}

                // Atmosphere
                atmosphereColor="#3a228a"
                atmosphereAltitude={0.1}
            />
        </div>
    );
}
