(() => {
  const canvas = document.getElementById("particles");
  if (!canvas) return;
  const ctx = canvas.getContext("2d", { alpha: true });
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = {
    width: 0, height: 0, dpr: 1, particles: [],
    mouse: { x: 0, y: 0, active: false },
    last: performance.now()
  };

  const config = () => window.innerWidth < 700
    ? { count: 24, distance: 105, radius: 125, speed: .34 }
    : window.innerWidth < 1100
      ? { count: 38, distance: 125, radius: 150, speed: .42 }
      : { count: 58, distance: 145, radius: 175, speed: .50 };

  const particle = (cfg) => {
    const angle = Math.random() * Math.PI * 2;
    const speed = cfg.speed * (.55 + Math.random() * .8);
    return {
      x: Math.random() * state.width,
      y: Math.random() * state.height,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      r: .65 + Math.random() * 1.15,
      phase: Math.random() * Math.PI * 2
    };
  };

  function resize() {
    state.dpr = Math.min(window.devicePixelRatio || 1, 2);
    state.width = window.innerWidth;
    state.height = window.innerHeight;
    canvas.width = state.width * state.dpr;
    canvas.height = state.height * state.dpr;
    canvas.style.width = state.width + "px";
    canvas.style.height = state.height + "px";
    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    const cfg = config();
    state.particles = Array.from({ length: cfg.count }, () => particle(cfg));
  }

  function frame(now) {
    const delta = Math.min((now - state.last) / 16.67, 2);
    state.last = now;
    const cfg = config();
    ctx.clearRect(0, 0, state.width, state.height);

    for (const p of state.particles) {
      p.phase += .018 * delta;
      p.x += (p.vx + Math.cos(p.phase) * .045) * delta;
      p.y += (p.vy + Math.sin(p.phase * .8) * .045) * delta;

      if (p.x < -20) p.x = state.width + 20;
      if (p.x > state.width + 20) p.x = -20;
      if (p.y < -20) p.y = state.height + 20;
      if (p.y > state.height + 20) p.y = -20;

      if (!reduced && state.mouse.active) {
        const dx = state.mouse.x - p.x;
        const dy = state.mouse.y - p.y;
        const distance = Math.hypot(dx, dy);
        if (distance < cfg.radius) {
          const force = (1 - distance / cfg.radius) * .012;
          p.vx += dx * force * delta;
          p.vy += dy * force * delta;
          const velocity = Math.hypot(p.vx, p.vy);
          if (velocity > 1.2) {
            p.vx *= .98;
            p.vy *= .98;
          }
        }
      }

      ctx.beginPath();
      ctx.fillStyle = "rgba(238, 220, 155, .72)";
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }    for (let i = 0; i < state.particles.length; i++) {
      for (let j = i + 1; j < state.particles.length; j++) {
        const a = state.particles[i];
        const b = state.particles[j];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        if (distance < cfg.distance) {
          const opacity = (1 - distance / cfg.distance) * .13;
          ctx.strokeStyle = `rgba(212,175,55,${opacity})`;
          ctx.lineWidth = .7;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    if (!document.hidden) {
      requestAnimationFrame(frame);
    }
  }

  window.addEventListener("resize", resize, { passive: true });
  window.addEventListener("mousemove", (event) => {
    state.mouse.x = event.clientX;
    state.mouse.y = event.clientY;
    state.mouse.active = true;
  }, { passive: true });
  window.addEventListener("mouseleave", () => {
    state.mouse.active = false;
  }, { passive: true });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      state.last = performance.now();
      requestAnimationFrame(frame);
    }
  });

  resize();
  requestAnimationFrame(frame);
})();