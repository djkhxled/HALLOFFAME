/* scroll.js — motion layer.
 *
 * Two hard guarantees:
 *   1. If the user asked for reduced motion, nothing here runs at all.
 *   2. If the GSAP CDN fails, nothing here runs and the page is unaffected.
 * All content is server-rendered, so both fallbacks are complete documents.
 */
(function () {
  "use strict";

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) return;

  if (typeof window.gsap === "undefined" || typeof window.ScrollTrigger === "undefined") {
    return;
  }

  var gsap = window.gsap;
  gsap.registerPlugin(window.ScrollTrigger);

  /* Shared: sections rise into place as they enter. ---------------------- */
  function reveals() {
    gsap.utils.toArray(".section").forEach(function (el) {
      gsap.from(el, {
        opacity: 0,
        y: 36,
        duration: 0.8,
        ease: "power2.out",
        scrollTrigger: { trigger: el, start: "top 85%" },
      });
    });
  }

  /* Landing: the ground colour travels with the countdown. --------------- */
  function countdown() {
    var entries = gsap.utils.toArray(".countdown__entry");
    if (!entries.length) return;

    entries.forEach(function (entry) {
      var field = entry.style.getPropertyValue("--field");
      var accent = entry.style.getPropertyValue("--accent");

      gsap.from(entry.querySelector(".countdown__name"), {
        opacity: 0,
        x: -28,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: { trigger: entry, start: "top 88%" },
      });

      if (!field) return;
      window.ScrollTrigger.create({
        trigger: entry,
        start: "top 60%",
        end: "bottom 40%",
        onToggle: function (self) {
          if (!self.isActive) return;
          gsap.to(document.body, {
            backgroundColor: field.trim(),
            duration: 0.9,
            ease: "power2.out",
            overwrite: "auto",
          });
          if (accent) {
            document.documentElement.style.setProperty("--accent", accent.trim());
          }
        },
      });
    });
  }

  /* Signature: orbit — layered bodies drift at different rates. ---------- */
  function orbit() {
    var stage = document.querySelector("[data-sig='orbit']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=180%",
        scrub: 0.8,
        pin: true,
      },
    });

    tl.to(stage.querySelectorAll("[data-depth='far']"), { yPercent: -8, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-depth='mid']"), { yPercent: -22, scale: 1.08, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-depth='near']"), { yPercent: -46, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-orbit-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.25, ease: "power2.out" },
        0.1
      );
  }

  /* Signature: glitch-assemble — the headline pulls itself together. ----- */
  function glitchAssemble() {
    var stage = document.querySelector("[data-sig='glitch-assemble']");
    if (!stage) return;

    var slices = stage.querySelectorAll("[data-slice]");
    if (!slices.length) return;

    gsap.set(slices, {
      xPercent: function (i) {
        return i % 2 === 0 ? -60 : 60;
      },
      opacity: 0.15,
    });

    gsap.to(slices, {
      xPercent: 0,
      opacity: 1,
      ease: "none",
      stagger: 0.04,
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=160%",
        scrub: 0.6,
        pin: true,
      },
    });

    gsap.to(stage.querySelectorAll("[data-flicker]"), {
      opacity: 0.9,
      duration: 0.09,
      repeat: -1,
      yoyo: true,
      ease: "steps(1)",
      stagger: { each: 0.11, from: "random" },
    });
  }

  reveals();
  countdown();

  var sig = document.documentElement.dataset.signature;
  if (sig === "orbit") orbit();
  if (sig === "glitch-assemble") glitchAssemble();
})();
