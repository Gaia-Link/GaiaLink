'use client';

import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

// --- Shader Code ---

const vertexShader = `
varying vec2 vUv;
void main() {
    vUv = uv;
    gl_Position = vec4(position, 1.0);
}
`;

const fragmentShader = `
uniform float u_time;
uniform vec2 u_mouse;
uniform vec2 u_resolution;

varying vec2 vUv;

// Simplex noise function
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }
float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
    vec2 i = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);
    vec2 i1;
    i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod289(i);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
    vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
    m = m * m;
    m = m * m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
    vec3 g;
    g.x = a0.x * x0.x + h.x * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
}

void main() {
    vec2 st = vUv;
    // Correct aspect ratio
    st.x *= u_resolution.x / u_resolution.y;
    
    // Mouse interaction - mapped to aspect corrected space roughly
    vec2 mse = u_mouse;
    mse.x *= u_resolution.x / u_resolution.y;
    
    float dist = distance(st, mse);
    
    // Time variation
    float t = u_time * 0.2;
    
    // Domain warping
    vec2 q = vec2(0.0);
    q.x = snoise(st + vec2(t * 0.5, t * 0.3));
    q.y = snoise(st + vec2(t * 0.4, t * 0.6));

    vec2 r = vec2(0.0);
    r.x = snoise(st + q + vec2(t * 0.5, t * 0.2) + vec2(mse.x - 0.5, mse.y - 0.5) * 0.5);
    r.y = snoise(st + q + vec2(t * 0.3, t * 0.1));

    float f = snoise(st + r);

    // Color mixing (Warm Aurora: Orange, Pink, Purple, Deep Blue)
    vec3 color1 = vec3(1.0, 0.3, 0.0); // Orange
    vec3 color2 = vec3(1.0, 0.0, 0.5); // Pink
    vec3 color3 = vec3(0.4, 0.0, 0.9); // Purple
    vec3 color4 = vec3(0.0, 0.0, 0.2); // Deep Blue

    vec3 color = mix(color1, color2, clamp(f * f * 4.0, 0.0, 1.0));
    color = mix(color, color3, clamp(length(q), 0.0, 1.0));
    color = mix(color, color4, clamp(length(r.x), 0.0, 1.0));
    
    gl_FragColor = vec4(color, 1.0);
}
`;

const FluidMesh = () => {
    const meshRef = useRef<THREE.Mesh>(null);
    const { viewport, size } = useThree();
    const mouseRef = useRef({ x: 0, y: 0 });

    const uniforms = useMemo(
        () => ({
            u_time: { value: 0 },
            u_mouse: { value: new THREE.Vector2() },
            u_resolution: { value: new THREE.Vector2(size.width, size.height) }
        }),
        [] // Initial only
    );

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            // Normalize mouse to 0..1
            mouseRef.current = {
                x: e.clientX / window.innerWidth,
                y: 1.0 - (e.clientY / window.innerHeight) // GLSL y is inverted relative to value
            };
        };
        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    useFrame((state) => {
        const { clock, size } = state;
        if (meshRef.current) {
            const material = meshRef.current.material as THREE.ShaderMaterial;
            material.uniforms.u_time.value = clock.getElapsedTime();
            material.uniforms.u_resolution.value.set(size.width, size.height);

            // Smoothly interpolate mouse value
            material.uniforms.u_mouse.value.lerp(
                new THREE.Vector2(mouseRef.current.x, mouseRef.current.y),
                0.1
            );
        }
    });

    return (
        <mesh ref={meshRef} scale={[viewport.width, viewport.height, 1]}>
            <planeGeometry args={[1, 1]} />
            <shaderMaterial
                fragmentShader={fragmentShader}
                vertexShader={vertexShader}
                uniforms={uniforms}
                transparent={true}
            />
        </mesh>
    );
};

export default function FluidBackground() {
    return (
        <div className="absolute inset-0 w-full h-full z-1 pointer-events-none mix-blend-screen">
            <Canvas
                camera={{ position: [0, 0, 1], fov: 75 }}
                dpr={[1, 2]}
                gl={{ antialias: true, alpha: true }}
            >
                <FluidMesh />
            </Canvas>
        </div>
    );
}
