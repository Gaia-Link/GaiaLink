'use client';

import React, { useEffect } from 'react';
import { motion, useMotionValue, useSpring, useMotionTemplate } from 'framer-motion';

export default function MouseGradientBackground() {
    // Mouse coordinates
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    // Smooth spring animation for the gradient center
    const springConfig = { damping: 25, stiffness: 150, mass: 0.5 };
    const springX = useSpring(mouseX, springConfig);
    const springY = useSpring(mouseY, springConfig);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            // Update raw mouse values
            mouseX.set(e.clientX);
            mouseY.set(e.clientY);
        };

        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, [mouseX, mouseY]);

    // Create a dynamic background gradient template
    // We use a large radial gradient that moves with the mouse
    const background = useMotionTemplate`
        radial-gradient(
            circle 500px at ${springX}px ${springY}px,
            rgba(255, 90, 0, 0.25),
            rgba(255, 0, 60, 0.2),
            rgba(120, 0, 255, 0.1),
            transparent 70%
        )
    `;

    return (
        <motion.div
            className="absolute inset-0 pointer-events-none z-0 mix-blend-screen"
            style={{ background }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1 }}
        />
    );
}
