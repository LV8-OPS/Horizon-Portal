(() => {
  const canvas = document.getElementById("particles");
  if (!canvas) return;
  const ctx = canvas.getContext("2d", { alpha: true });
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { width: 0, height: 0, dpr: 1, particles: [], mouse: { x: 0, y: 0, active: false } };

  const config = () => window.innerWidth < 700
    ? { count: 18, distance: 88, radius: 92 }
    : window.innerWidth < 1100
      ? { count: 30, distance: 108, radius: 126 }
      : { count: 44, distance: 124, radius: 144 };

  const particle = () => ({
    x: Math.random() * state.width,
    y: Math.random() * state.height,
    vx: (Math.random() - 0.5) * 0.12,
    vy: (Math.random() - 0.5) * 0.12,
    r: Math.random() * 1 + 0.55,
  });

  function resize() {
    state.dpr = Math.min(window.devicePixelRatio || 1, 2);
    state.width = window.innerWidth;
    state.height = window.innerHeight;
    canvas.width = state.width * state.dpr;
    canvas.height = state.height * state.dpr;
    canvas.style.width = `${state.width}px`;
    canvas.style.height = `${state.height}px`;
    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    state.particles = Array.from({ length: config().count }, particle);
  }

  let animationId = 0;
  function frame() {
    const cfg = config();
    ctx.clearRect(0, 0, state.width, state.height);

    for (const p of state.particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < -10) p.x = state.width + 10;
      if (p.x > state.width + 10) p.x = -10;
      if (p.y < -10) p.y = state.height + 10;
      if (p.y > state.height + 10) p.y = -10;

      if (!reduced && state.mouse.active) {
        const dx = state.mouse.x - p.x;
        const dy = state.mouse.y - p.y;
        const distance = Math.hypot(dx, dy);
        if (distance < cfg.radius) {
          const force = (1 - distance / cfg.radius) * 0.004;
          p.vx += dx * force;
          p.vy += dy * force;
        }
      }

      ctx.beginPath();
      ctx.fillStyle = "rgba(235, 235, 235, .55)";
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }

    for (let i = 0; i < state.particles.length; i++) {
      for (let j = i + 1; j < state.particles.length; j++) {
        const a = state.particles[i];
        const b = state.particles[j];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        if (distance < cfg.distance) {
          const opacity = (1 - distance / cfg.distance) * 0.09;
          ctx.strokeStyle = `rgba(212,175,55,${opacity})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    if (!reduced && !document.hidden) animationId = requestAnimationFrame(frame);
  }

  function restartAnimation() {
    if (reduced || document.hidden) return;
    cancelAnimationFrame(animationId);
    animationId = requestAnimationFrame(frame);
  }

  window.addEventListener("resize", resize, { passive: true });
  document.addEventListener("visibilitychange", restartAnimation);
  window.addEventListener("mousemove", (event) => {
    state.mouse.x = event.clientX;
    state.mouse.y = event.clientY;
    state.mouse.active = true;
  }, { passive: true });
  window.addEventListener("mouseleave", () => { state.mouse.active = false; }, { passive: true });
  resize();
  frame();
})();
