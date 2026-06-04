import React, { useEffect, useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

export const BackgroundEffects: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Smooth mouse coordinates with Framer Motion spring inertia
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  const springConfig = { damping: 35, stiffness: 150 };
  const smoothX = useSpring(mouseX, springConfig);
  const smoothY = useSpring(mouseY, springConfig);

  // Custom template strings for CSS styling
  const radialBg = useTransform(
    [smoothX, smoothY],
    ([x, y]) => `radial-gradient(700px circle at ${x}px ${y}px, rgba(79, 140, 255, 0.08), rgba(123, 97, 255, 0.04) 40%, transparent 80%)`
  );

  useEffect(() => {
    // Initial mouse coordinate set to center of viewport
    mouseX.set(window.innerWidth / 2);
    mouseY.set(window.innerHeight / 2);

    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [mouseX, mouseY]);

  // Neural Network Canvas Particles
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Responsive particle count
    const particleCount = Math.min(Math.floor((width * height) / 25000), 70);
    const connectionDistance = 120;
    const particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
    }> = [];

    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.3, // slow speed
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 1.5 + 1,
      });
    }

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Mouse interactive position on canvas
      const currentMouseX = mouseX.get();
      const currentMouseY = mouseY.get();

      // Update & Draw Particles
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        // Boundary bounce
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        // Draw particle node
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(79, 140, 255, 0.25)';
        ctx.fill();
      });

      // Draw Connections (Neural Network lines)
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < connectionDistance) {
            const alpha = (1 - dist / connectionDistance) * 0.15;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(123, 97, 255, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }

        // Draw connection to cursor
        const dxMouse = p1.x - currentMouseX;
        const dyMouse = p1.y - currentMouseY;
        const distMouse = Math.sqrt(dxMouse * dxMouse + dyMouse * dyMouse);
        if (distMouse < 180) {
          const alphaMouse = (1 - distMouse / 180) * 0.18;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(currentMouseX, currentMouseY);
          ctx.strokeStyle = `rgba(79, 140, 255, ${alphaMouse})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, [mouseX, mouseY]);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 bg-[#0B0F19]">
      {/* Soft Blurred Gradient Blobs */}
      <motion.div
        animate={{
          x: [0, 80, -40, 0],
          y: [0, -60, 40, 0],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[#4F8CFF] opacity-[0.06] blur-[120px] pointer-events-none"
      />
      <motion.div
        animate={{
          x: [0, -60, 50, 0],
          y: [0, 80, -30, 0],
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute bottom-[-10%] right-[-10%] w-[55%] h-[55%] rounded-full bg-[#7B61FF] opacity-[0.05] blur-[140px] pointer-events-none"
      />

      {/* Grid Overlay with futuristic grid lines */}
      <div 
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
        }}
      />

      {/* Canvas for Neural Network */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-60" />

      {/* Smooth Radial Cursor Glow */}
      <motion.div
        style={{ background: radialBg }}
        className="absolute inset-0 w-full h-full pointer-events-none hidden md:block"
      />
    </div>
  );
};
