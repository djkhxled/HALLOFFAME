/* attempt.js — the run readout.
 *
 * Geometry Dash shows you one number while you play: how far through you
 * are. The whole site is built as a countdown, so every page carries the
 * same readout — a fill across the top and a percentage in the corner.
 *
 * Deliberately NOT in scroll.js. That file returns early when the user asks
 * for reduced motion and again if GSAP failed to load, and both are the
 * wrong call here: a progress indicator is information, not decoration, and
 * it should survive a blocked CDN. It also means this runs with no
 * dependency at all.
 *
 * The bar does move, so a reduced-motion reader gets the readout without the
 * transition — handled in CSS, not here, because the media query can change
 * while the page is open.
 */
(function () {
  "use strict";

  var bar = document.querySelector("[data-attempt-fill]");
  var out = document.querySelector("[data-attempt-pct]");
  if (!bar && !out) return;

  var ticking = false;
  var last = -1;

  function measure() {
    ticking = false;
    var doc = document.documentElement;
    /* scrollHeight includes the viewport, so the travel is what is left
       after it. A page shorter than the viewport has zero travel and would
       divide by zero. */
    var travel = doc.scrollHeight - window.innerHeight;
    var pct = travel > 8 ? (window.scrollY / travel) * 100 : 0;
    pct = Math.max(0, Math.min(100, pct));

    var whole = Math.round(pct);
    if (bar) bar.style.transform = "scaleX(" + (pct / 100).toFixed(4) + ")";
    /* Only touch the text when the integer actually changes: this runs on
       every scroll frame and rewriting an unchanged string still costs a
       layout pass on the readout. */
    if (out && whole !== last) {
      last = whole;
      out.textContent = whole + "%";
    }
    if (whole >= 100) {
      document.documentElement.setAttribute("data-run", "complete");
    } else {
      document.documentElement.removeAttribute("data-run");
    }
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(measure);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  /* The document grows as art and webfonts settle, which changes the
     denominator. Same reasoning as scroll.js's settle(). */
  if (window.ResizeObserver) {
    new ResizeObserver(onScroll).observe(document.body);
  }
  measure();
})();
