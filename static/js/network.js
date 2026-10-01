(() => {
  const canvas = document.getElementById("particles");
  if (!canvas) return;

  const ctx = canvas.getContext("2d", { alpha: true });
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const state = {
    width: 0,
    height: 0,
    dpr: 1,
    particles: [],
    mouse: { x: 0, y: 0, active: false },
    last: 0,
    raf: 0
  };

  // Deliberately lightweight: fewer particles, capped DPR and one connection pass.
  const config = () => window.innerWidth < 700
    ? { count: 14, distance: 95, radius: 115, speed: 0.22 }
    : window.innerWidth < 1100
      ? { count: 22, distance: 105, radius: 125, speed: 0.26 }
      : { count: 32, distance: 120, radius: 140, speed: 0.30 };

  const makeParticle = (cfg) => {
    const angle = Math.random() * Math.PI * 2;
    const speed = cfg.speed * (0.65 + Math.random() * 0.7);
    return {
      x: Math.random() * state.width,
      y: Math.random() * state.height,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      r: 0.7 + Math.random() * 0.8
    };
  };

  function resize() {
    state.dpr = Math.min(window.devicePixelRatio || 1, 1.25);
    state.width = window.innerWidth;
    state.height = window.innerHeight;

    canvas.width = Math.floor(state.width * state.dpr);
    canvas.height = Math.floor(state.height * state.dpr);
    canvas.style.width = state.width + "px";
    canvas.style.height = state.height + "px";

    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);

    const cfg = config();
    state.particles = Array.from(
      { length: cfg.count },
      () => makeParticle(cfg)
    );
  }

  function draw(now) {
    if (document.hidden) {
      state.raf = 0;
      return;
    }

    const delta = Math.min((now - state.last) / 16.67, 1.5);
    state.last = now;
    const cfg = config();

    ctx.clearRect(0, 0, state.width, state.height);

    // Move and draw particles.
    for (const p of state.particles) {
      p.x += p.vx * delta;
      p.y += p.vy * delta;

      if (p.x < -10) p.x = state.width + 10;
      else if (p.x > state.width + 10) p.x = -10;
      if (p.y < -10) p.y = state.height + 10;
      else if (p.y > state.height + 10) p.y = -10;

      // Mouse interaction is intentionally local and subtle.
      if (!reduced && state.mouse.active) {
        const dx = state.mouse.x - p.x;
        const dy = state.mouse.y - p.y;
        const d2 = dx * dx + dy * dy;
        const radius2 = cfg.radius * cfg.radius;

        if (d2 > 1 && d2 < radius2) {
          const distance = Math.sqrt(d2);
          const force = (1 - distance / cfg.radius) * 0.006;
          p.vx += (dx / distance) * force * delta;
          p.vy += (dy / distance) * force * delta;

          // Prevent mouse interaction from accelerating particles indefinitely.
          const maxSpeed = cfg.speed * 1.8;
          const speed = Math.hypot(p.vx, p.vy);
          if (speed > maxSpeed) {
            p.vx = (p.vx / speed) * maxSpeed;
            p.vy = (p.vy / speed) * maxSpeed;
          }
        }
      }

      ctx.beginPath();
      ctx.fillStyle = "rgba(238, 220, 155, .62)";
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Spatial grid: avoids the old O(n²) connection loop.
    const cellSize = cfg.distance;
    const grid = new Map();

    for (const p of state.particles) {
      const gx = Math.floor(p.x / cellSize);
      const gy = Math.floor(p.y / cellSize);
      const key = gx + "," + gy;
      const bucket = grid.get(key);
      if (bucket) bucket.push(p);
      else grid.set(key, [p]);
    }

    ctx.lineWidth = 0.55;

    for (const p of state.particles) {
      const gx = Math.floor(p.x / cellSize);
      const gy = Math.floor(p.y / cellSize);

      for (let ox = -1; ox <= 1; ox++) {
        for (let oy = -1; oy <= 1; oy++) {
          const bucket = grid.get((gx + ox) + "," + (gy + oy));
          if (!bucket) continue;

          for (const b of bucket) {
            if (b === p) continue;

            const dx = p.x - b.x;
            const dy = p.y - b.y;
            const distance = Math.hypot(dx, dy);

            // Draw each pair only once.
            if (distance < cfg.distance && (p.x < b.x || (p.x === b.x && p.y < b.y))) {
              const opacity = (1 - distance / cfg.distance) * 0.12;
              ctx.strokeStyle = "rgba(212,175,55," + opacity + ")";
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(b.x, b.y);
              ctx.stroke();
            }
          }
        }
      }
    }

    state.raf = requestAnimationFrame(draw);
  }

  function start() {
    if (reduced || state.raf) return;
    state.last = performance.now();
    state.raf = requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize, { passive: true });

  // pointermove is cheaper than doing work on every mouse event.
  window.addEventListener("pointermove", (event) => {
    state.mouse.x = event.clientX;
    state.mouse.y = event.clientY;
    state.mouse.active = true;
  }, { passive: true });

  window.addEventListener("pointerleave", () => {
    state.mouse.active = false;
  }, { passive: true });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (state.raf) cancelAnimationFrame(state.raf);
      state.raf = 0;
    } else {
      start();
    }
  });

  resize();

  if (reduced) {
    // Static fallback for users who disable motion.
    for (const p of state.particles) {
      ctx.beginPath();
      ctx.fillStyle = "rgba(238, 220, 155, .5)";
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
  } else {
    start();
  }
})();
