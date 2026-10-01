(() => {
  "use strict";

  const canvas = document.getElementById("particles");
  if (!canvas) return;

  const ctx = canvas.getContext("2d", { alpha: true });
  if (!ctx) return;

  const state = {
    width: 0,
    height: 0,
    dpr: 1,
    particles: [],
    mouse: { x: 0, y: 0, active: false },
    last: 0,
    raf: 0
  };

  function config() {
    if (window.innerWidth < 700) return { count: 20, distance: 100, radius: 120, speed: 0.18 };
    if (window.innerWidth < 1100) return { count: 30, distance: 110, radius: 130, speed: 0.21 };
    return { count: 42, distance: 125, radius: 145, speed: 0.24 };
  }

  function createParticle(cfg) {
    const angle = Math.random() * Math.PI * 2;
    const speed = cfg.speed * (0.7 + Math.random() * 0.6);
    return {
      x: Math.random() * state.width,
      y: Math.random() * state.height,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      r: 0.8 + Math.random() * 0.7
    };
  }

  function resize() {
    state.dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    state.width = Math.max(window.innerWidth, 1);
    state.height = Math.max(window.innerHeight, 1);

    canvas.width = Math.floor(state.width * state.dpr);
    canvas.height = Math.floor(state.height * state.dpr);
    canvas.style.width = state.width + "px";
    canvas.style.height = state.height + "px";

    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);

    const cfg = config();
    state.particles = Array.from({ length: cfg.count }, () => createParticle(cfg));
  }

  function draw(now) {
    state.raf = 0;

    if (document.hidden) return;

    const elapsed = state.last ? Math.min((now - state.last) / 16.67, 2) : 1;
    state.last = now;

    const cfg = config();
    ctx.clearRect(0, 0, state.width, state.height);

    for (const p of state.particles) {
      p.x += p.vx * elapsed;
      p.y += p.vy * elapsed;

      if (p.x < -20) p.x = state.width + 20;
      if (p.x > state.width + 20) p.x = -20;
      if (p.y < -20) p.y = state.height + 20;
      if (p.y > state.height + 20) p.y = -20;

      if (state.mouse.active) {
        const dx = state.mouse.x - p.x;
        const dy = state.mouse.y - p.y;
        const distance = Math.hypot(dx, dy);

        if (distance > 1 && distance < cfg.radius) {
          const force = (1 - distance / cfg.radius) * 0.004;
          p.vx += dx / distance * force * elapsed;
          p.vy += dy / distance * force * elapsed;

          const maxSpeed = cfg.speed * 1.6;
          const currentSpeed = Math.hypot(p.vx, p.vy);
          if (currentSpeed > maxSpeed) {
            p.vx = p.vx / currentSpeed * maxSpeed;
            p.vy = p.vy / currentSpeed * maxSpeed;
          }
        }
      }

      ctx.beginPath();
      ctx.fillStyle = "rgba(238,220,155,0.70)";
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Only compare nearby grid cells, keeping CPU usage low.
    const grid = new Map();
    const cell = cfg.distance;

    for (const p of state.particles) {
      const gx = Math.floor(p.x / cell);
      const gy = Math.floor(p.y / cell);
      const key = gx + ":" + gy;
      if (!grid.has(key)) grid.set(key, []);
      grid.get(key).push(p);
    }

    ctx.lineWidth = 0.55;

    for (const p of state.particles) {
      const gx = Math.floor(p.x / cell);
      const gy = Math.floor(p.y / cell);

      for (let ox = -1; ox <= 1; ox++) {
        for (let oy = -1; oy <= 1; oy++) {
          const bucket = grid.get((gx + ox) + ":" + (gy + oy));
          if (!bucket) continue;

          for (const other of bucket) {
            if (other === p) continue;

            const dx = p.x - other.x;
            const dy = p.y - other.y;
            const distance = Math.hypot(dx, dy);

            if (
              distance < cfg.distance &&
              (p.x < other.x || (p.x === other.x && p.y < other.y))
            ) {
              const opacity = (1 - distance / cfg.distance) * 0.16;
              ctx.strokeStyle = "rgba(212,175,55," + opacity + ")";
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(other.x, other.y);
              ctx.stroke();
            }
          }
        }
      }
    }

    state.raf = requestAnimationFrame(draw);
  }

  function start() {
    if (state.raf) return;
    state.last = performance.now();
    state.raf = requestAnimationFrame(draw);
  }

  window.addEventListener("resize", resize, { passive: true });

  window.addEventListener("pointermove", event => {
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
  start();
})();
