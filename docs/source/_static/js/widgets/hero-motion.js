/**
 * ⑦ Landing hero motion: counters + P–h sketch fade-in.
 *
 * Runs only on the landing page (detects #hero-motion-root). Honours
 * prefers-reduced-motion by skipping the animation and rendering the
 * final state immediately.
 */
(function () {
  "use strict";
  const root = document.getElementById("hero-motion-root");
  if (!root) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const counters = root.querySelectorAll(".hero-metric");
  const sketch = root.querySelector(".hero-sketch");

  function animateCount(el) {
    const target = +el.dataset.target;
    if (reduceMotion || target === 0) {
      el.textContent = target;
      return;
    }
    const duration = 800;
    const start = performance.now();
    function tick(now) {
      const k = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(target * ease);
      if (k < 1) requestAnimationFrame(tick);
      else el.textContent = target;
    }
    requestAnimationFrame(tick);
  }

  function reveal() {
    if (sketch && !reduceMotion) sketch.classList.add("is-visible");
    counters.forEach(animateCount);
  }

  if ("IntersectionObserver" in window && !reduceMotion) {
    const obs = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) { reveal(); obs.disconnect(); break; }
      }
    }, { threshold: 0.2 });
    obs.observe(root);
  } else {
    reveal();
  }
})();
