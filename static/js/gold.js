(() => {
  function run() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const elements = [...document.querySelectorAll(".gold-shimmer")];
    if (!elements.length) return;
    setInterval(() => {
      const element = elements[Math.floor(Math.random() * elements.length)];
      if (!element) return;
      element.classList.add("is-shimmering");
      window.setTimeout(() => element.classList.remove("is-shimmering"), 1000);
    }, 15000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run, { once: true });
  else run();
})();
