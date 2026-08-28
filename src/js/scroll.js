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

    /* The whole palette travels together, not just the background. Some
       levels are light-on-dark and some are dark-on-light, so shifting the
       field without the ink would leave text unreadable mid-scroll. CSS
       transitions on body handle the easing. */
    var ROOT = document.documentElement;
    var TRAVELS = ["--field", "--ink", "--muted", "--accent", "--accent2"];
    var base = {};
    TRAVELS.forEach(function (name) {
      base[name] = getComputedStyle(ROOT).getPropertyValue(name);
    });

    function wear(entry) {
      TRAVELS.forEach(function (name) {
        var value = entry ? entry.style.getPropertyValue(name) : "";
        ROOT.style.setProperty(name, (value || base[name]).trim());
      });
    }

    entries.forEach(function (entry) {
      gsap.from(entry.querySelector(".countdown__name"), {
        opacity: 0,
        x: -28,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: { trigger: entry, start: "top 88%" },
      });

      if (!entry.style.getPropertyValue("--field")) return;
      window.ScrollTrigger.create({
        trigger: entry,
        start: "top 60%",
        end: "bottom 40%",
        onToggle: function (self) {
          if (self.isActive) wear(entry);
        },
      });
    });

    /* Back above the countdown, the site returns to its own palette. */
    window.ScrollTrigger.create({
      trigger: ".countdown",
      start: "top 60%",
      onToggle: function (self) {
        if (!self.isActive) wear(null);
      },
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

  /* Signature: eclipse — the disc swells while the ridges close in. ------ */
  function eclipse() {
    var stage = document.querySelector("[data-sig='eclipse']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=190%",
        scrub: 0.8,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-depth='orb']"),
      { scale: 0.72, opacity: 0.75 },
      { scale: 1.18, opacity: 1, ease: "none" },
      0
    )
      .to(stage.querySelector("[data-depth='far']"), { yPercent: -14, ease: "none" }, 0)
      .to(stage.querySelector("[data-depth='near']"), { yPercent: -34, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-ecl-line]"),
        { opacity: 0, y: 34 },
        { opacity: 1, y: 0, stagger: 0.22, ease: "power2.out" },
        0.12
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

  /* Signature: slash — the swash wipes across and the title cuts in. ---- */
  function slash() {
    var stage = document.querySelector("[data-sig='slash']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=170%",
        scrub: 0.7,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-swash]"),
      { scaleX: 0, transformOrigin: "left center" },
      { scaleX: 1, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelectorAll("[data-cut]"),
        { xPercent: -14, opacity: 0, skewX: 14 },
        { xPercent: 0, opacity: 1, skewX: 0, stagger: 0.16, ease: "power3.out" },
        0.18
      )
      .to(stage.querySelectorAll("[data-hand]"), { rotate: 220, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-hand-slow]"), { rotate: 74, ease: "none" }, 0);
  }

  /* Signature: prism — the beam sweeps, the lattice drifts apart. ------- */
  function prism() {
    var stage = document.querySelector("[data-sig='prism']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=180%",
        scrub: 0.7,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-beam]"),
      { xPercent: -60, opacity: 0 },
      { xPercent: 60, opacity: 1, ease: "none" },
      0
    )
      .to(stage.querySelectorAll("[data-drift='a']"), { yPercent: -26, xPercent: -8, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-drift='b']"), { yPercent: 22, xPercent: 10, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-split]"),
        { opacity: 0, letterSpacing: "0.4em" },
        { opacity: 1, letterSpacing: "0.02em", ease: "power2.out" },
        0.1
      );
  }

  /* Signature: descend — the camera falls, the world rises past it. ----- */
  function descend() {
    var stage = document.querySelector("[data-sig='descend']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=200%",
        scrub: 0.9,
        pin: true,
      },
    });

    tl.to(stage.querySelectorAll("[data-fall='far']"), { yPercent: -30, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-fall='mid']"), { yPercent: -62, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-fall='near']"), { yPercent: -104, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-chain]"), { yPercent: -140, ease: "none" }, 0)
      .fromTo(
        stage.querySelector("[data-dark]"),
        { opacity: 0 },
        { opacity: 0.72, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelectorAll("[data-desc-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.15
      );
  }

  /* Signature: surge — the wave rears and the water pans past. --------- */
  function surge() {
    var stage = document.querySelector("[data-sig='surge']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=190%",
        scrub: 0.8,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-swell]"),
      { yPercent: 34, scale: 1.16 },
      { yPercent: -8, scale: 1, ease: "none" },
      0
    )
      .to(stage.querySelectorAll("[data-current='a']"), { xPercent: -30, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-current='b']"), { xPercent: 22, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-foam]"), { xPercent: -46, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-surge-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.12
      );
  }

  /* Signature: ignite — exposure ramps and the corona opens. ------------ */
  function ignite() {
    var stage = document.querySelector("[data-sig='ignite']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=190%",
        scrub: 0.75,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-core]"),
      { scale: 0.42, opacity: 0.5 },
      { scale: 1.15, opacity: 1, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelector("[data-rays]"),
        { scale: 0.6, opacity: 0, rotate: -22 },
        { scale: 1.3, opacity: 0.9, rotate: 14, ease: "none" },
        0
      )
      .to(stage.querySelectorAll("[data-cog]"), { rotate: 150, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-cog-rev]"), { rotate: -120, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-ignite-line]"),
        { opacity: 0, y: 26 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.15
      );
  }

  /* Signature: pulse — the whole frame breathes, hard and on beat. ------ */
  function pulse() {
    var stage = document.querySelector("[data-sig='pulse']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=180%",
        scrub: 0.6,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-loom]"),
      { scale: 0.72, opacity: 0.35 },
      { scale: 1.08, opacity: 1, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelectorAll("[data-pulse-line]"),
        { opacity: 0, y: 28 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.18
      );

    /* the heartbeat itself is time-based, not scroll-based */
    gsap.to(stage.querySelectorAll("[data-beat]"), {
      opacity: 0.95,
      scale: 1.06,
      duration: 0.42,
      repeat: -1,
      yoyo: true,
      ease: "power1.inOut",
      transformOrigin: "50% 50%",
    });
  }

  reveals();
  countdown();

  var sig = document.documentElement.dataset.signature;
  if (sig === "surge") surge();
  if (sig === "ignite") ignite();
  if (sig === "pulse") pulse();
  if (sig === "orbit") orbit();
  if (sig === "eclipse") eclipse();
  if (sig === "glitch-assemble") glitchAssemble();
  if (sig === "slash") slash();
  if (sig === "prism") prism();
  if (sig === "descend") descend();
})();
