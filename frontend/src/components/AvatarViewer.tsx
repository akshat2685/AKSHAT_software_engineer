import React, { useEffect, useRef, useState, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, MeshDistortMaterial, useGLTF } from '@react-three/drei';
import { useStore } from '../store/useStore';
import * as THREE from 'three';

// Procedural 3D mesh fallback that animates based on active agent status
const FloatingOrb: React.FC<{ state: string }> = ({ state }) => {
  const colorMap: Record<string, string> = {
    idle: '#38d5ff', // Cyan
    thinking: '#a78bfa', // Violet
    talking: '#4cf2a1', // Green
    coding: '#ffd166', // Amber
    reviewing: '#ff6b7d', // Danger / Red
    testing: '#818cf8', // Indigo
    debugging: '#fb923c', // Orange
    celebrating: '#34d399', // Emerald
  };

  const cleanState = state.toLowerCase();
  let color = colorMap.idle;
  
  if (cleanState.includes('think')) color = colorMap.thinking;
  else if (cleanState.includes('speak') || cleanState.includes('talk')) color = colorMap.talking;
  else if (cleanState.includes('code') || cleanState.includes('dev')) color = colorMap.coding;
  else if (cleanState.includes('test')) color = colorMap.testing;
  else if (cleanState.includes('review')) color = colorMap.reviewing;
  else if (cleanState.includes('debug') || cleanState.includes('improve')) color = colorMap.debugging;
  else if (cleanState.includes('celebrate') || cleanState.includes('success')) color = colorMap.celebrating;

  const coreRef = useRef<THREE.Mesh>(null);
  const outerRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((stateFrame) => {
    const t = stateFrame.clock.getElapsedTime();
    if (coreRef.current) {
      coreRef.current.rotation.y = t * 0.2;
    }
    if (outerRef.current) {
      outerRef.current.rotation.y = -t * 0.15;
      outerRef.current.rotation.x = t * 0.1;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.5;
      ringRef.current.rotation.x = Math.PI / 3 + Math.sin(t * 0.25) * 0.12;
    }
  });

  return (
    <group>
      {/* Inner glowing core */}
      <mesh ref={coreRef}>
        <sphereGeometry args={[0.78, 64, 64]} />
        <MeshDistortMaterial
          color={color}
          distort={0.4}
          speed={2.2}
          roughness={0.05}
          metalness={0.95}
          clearcoat={1.0}
        />
      </mesh>

      {/* Cybernetic wireframe outer shell */}
      <mesh ref={outerRef}>
        <icosahedronGeometry args={[1.15, 2]} />
        <meshBasicMaterial
          color={color}
          wireframe
          transparent
          opacity={0.22}
        />
      </mesh>

      {/* Pulsing orbital rings */}
      <mesh ref={ringRef}>
        <ringGeometry args={[1.3, 1.34, 64]} />
        <meshBasicMaterial
          color={color}
          side={THREE.DoubleSide}
          transparent
          opacity={0.35}
        />
      </mesh>
    </group>
  );
};

// Error boundary to catch GLTF loading failures (e.g. network offline)
class AvatarErrorBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: any) {
    console.warn("Avatar GLTF loading failed, falling back to procedural orb:", error);
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

// 3D Ready Player Me Avatar loader with custom breathing animations
const ReadyPlayerMeAvatar: React.FC<{ state: string }> = ({ state: _state }) => {
  // Use a generic, highly detailed Ready Player Me developer avatar GLB
  const { scene } = useGLTF('https://models.readyplayer.me/64db624f8d6fb246d84a7e93.glb');
  const groupRef = useRef<THREE.Group>(null);

  // Subtle breathing and head-nod idling animations
  useFrame((stateFrame) => {
    if (!groupRef.current) return;
    const t = stateFrame.clock.getElapsedTime();
    // Simulate breathing
    groupRef.current.position.y = -2.0 + Math.sin(t * 1.6) * 0.025;
    // Simulate slight natural head/upper torso rotation
    groupRef.current.rotation.y = Math.sin(t * 0.65) * 0.04;
    groupRef.current.rotation.x = Math.sin(t * 0.35) * 0.02;
  });

  return (
    <group ref={groupRef} position={[0, -2.0, 0]} scale={2.2}>
      <primitive object={scene} />
    </group>
  );
};

export const AvatarViewer: React.FC = () => {
  const systemState = useStore((state) => state.systemState);
  const avatarState = systemState?.avatar_state || 'Idle';
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [glError, setGlError] = useState(false);

  // Fallback 2D Neural Grid Animation
  useEffect(() => {
    if (glError || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; r: number }> = [];

    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || 300;
      canvas.height = canvas.parentElement?.clientHeight || 300;
      particles = Array.from({ length: 45 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.8,
        vy: (Math.random() - 0.5) * 0.8,
        r: 1 + Math.random() * 2,
      }));
    };

    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.globalAlpha = 0.25;

      // Draw lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 85) {
            ctx.strokeStyle = dist < 45 ? '#4cf2a1' : '#38d5ff';
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      ctx.globalAlpha = 0.7;
      // Update particles
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.fillStyle = p.r > 2.2 ? '#4cf2a1' : '#38d5ff';
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }

      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
    };
  }, [glError]);

  return (
    <div className="relative w-full h-[360px] flex flex-col items-center justify-between rounded-xl bg-slate-950/40 p-4 border border-line overflow-hidden">
      <div className="absolute top-3 left-3 text-xs tracking-wider uppercase text-cyan font-display">
        AI Vitals Node
      </div>

      <div className="flex-1 w-full flex items-center justify-center relative">
        {!glError ? (
          <div className="w-full h-full" style={{ minHeight: '220px' }}>
            <Canvas
              onError={() => setGlError(true)}
              camera={{ position: [0, 0, 2.5], fov: 45 }}
            >
              <ambientLight intensity={0.8} />
              <pointLight position={[10, 10, 10]} intensity={1.5} />
              <directionalLight position={[-5, 5, -5]} intensity={0.6} />
              <Suspense fallback={<FloatingOrb state={avatarState} />}>
                <AvatarErrorBoundary fallback={<FloatingOrb state={avatarState} />}>
                  <ReadyPlayerMeAvatar state={avatarState} />
                </AvatarErrorBoundary>
              </Suspense>
              <OrbitControls enableZoom={false} enablePan={false} autoRotate={false} />
            </Canvas>
          </div>
        ) : (
          <canvas ref={canvasRef} className="w-full h-full block" />
        )}
      </div>

      <div className="w-full text-center mt-3 z-10">
        <h3 className="text-white font-display font-semibold text-lg">{avatarState}</h3>
      </div>
    </div>
  );
};
