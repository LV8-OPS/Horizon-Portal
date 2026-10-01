(() => {
  const GOLD = [212, 175, 55];
  const GOLD_SOFT = [240, 212, 119];

  function distanceToGold(rgb) {
    return Math.min(
      Math.hypot(rgb[0] - GOLD[0], rgb[1] - GOLD[1], rgb[2] - GOLD[2]),
      Math.hypot(rgb[0] - GOLD_SOFT[0], rgb[1] - GOLD_SOFT[1], rgb[2] - GOLD_SOFT[2])
    );
  }

  function isGoldColor(value) {
    const match = String(value || '').match(/rgba?\(([^)]+)\)/i);
    if (!match) return false;
    const rgb = match[1].split(',').slice(0, 3).map(v => Number.parseFloat(v.trim()));
    return rgb.length === 3 && rgb.every(Number.isFinite) && distanceToGold(rgb) < 95;
  }

  function collectGoldElements() {
    const candidates = [...document.querySelectorAll('*')];
    const found = new Set();

    candidates.forEach(element => {
      if (element.matches('.gold-shimmer, .release-dot')) {
        found.add(element);
        return;
      }

      const style = getComputedStyle(element);
      if (
        isGoldColor(style.color) ||
        isGoldColor(style.backgroundColor) ||
        isGoldColor(style.borderTopColor) ||
        isGoldColor(style.borderRightColor) ||
        isGoldColor(style.borderBottomColor) ||
        isGoldColor(style.borderLeftColor)
      ) {
        found.add(element);
      }
    });

    return [...found];
  }

  function shimmer(element) {
    if (!element || element.dataset.goldShimmerActive === '1') return;

    element.dataset.goldShimmerActive = '1';
    element.classList.add('gold-shimmer-active');

    window.setTimeout(() => {
      element.classList.remove('gold-shimmer-active');
      delete element.dataset.goldShimmerActive;
    }, 1150);
  }

  function schedule(element) {
    const delay = 15000 + Math.random() * 105000;
    window.setTimeout(() => {
      shimmer(element);
      schedule(element);
    }, delay);
  }

  function run() {
    const elements = collectGoldElements();
    if (!elements.length) return;

    elements.forEach((element, index) => {
      window.setTimeout(() => shimmer(element), 500 + Math.random() * 45000 + index * 180);
      schedule(element);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }
})();