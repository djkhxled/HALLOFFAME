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
      /* Never transform a section that contains triggers of its own. A
         transformed ancestor corrupts how ScrollTrigger measures everything
         inside it — this is what left the countdown's starts thousands of
         pixels negative and its palette stuck on one level. */
      if (el.querySelector(".countdown, [data-sig]")) return;

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

    /* Pick the entry nearest the viewport centre, read live on every frame.

       This deliberately does not use ScrollTrigger. Its ranges are computed
       once and cached, and on this page they were being computed before the
       hero art and webfonts settled — leaving starts thousands of pixels
       negative, 34 of 50 triggers "active" at scroll 0, and the palette stuck
       on whichever level won the race. Reading geometry live cannot go stale,
       and this is one cheap measurement per frame while scrolling. */
    var ticking = false;
    var worn = null;

    function pick() {
      ticking = false;
      var mid = window.innerHeight / 2;
      var best = null;
      var bestDist = Infinity;

      for (var i = 0; i < entries.length; i++) {
        var r = entries[i].getBoundingClientRect();
        if (r.bottom < 0 || r.top > window.innerHeight) continue;
        var d = Math.abs((r.top + r.bottom) / 2 - mid);
        if (d < bestDist) {
          bestDist = d;
          best = entries[i];
        }
      }

      if (best !== worn) {
        worn = best;
        wear(best);
      }
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(pick);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    pick();

    /* The name reveals can stay on ScrollTrigger: if one fires a little early
       or late it is invisible, unlike the page changing colour. */
    entries.forEach(function (entry) {
      gsap.from(entry.querySelector(".countdown__name"), {
        opacity: 0,
        x: -28,
        duration: 0.7,
        ease: "power3.out",
        scrollTrigger: { trigger: entry, start: "top 88%" },
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
      /* exactly one tile of the two-tile band, or the loop shows a seam */
      .to(stage.querySelectorAll("[data-foam]"), { xPercent: -50, ease: "none" }, 0)
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

  /* Signature: fracture — the frame shatters apart and reassembles. ----- */
  function fracture() {
    var stage = document.querySelector("[data-sig='fracture']");
    if (!stage) return;

    var shards = stage.querySelectorAll("[data-shard]");
    if (!shards.length) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=185%",
        scrub: 0.7,
        pin: true,
      },
    });

    tl.fromTo(
      shards,
      {
        xPercent: function (i) { return (i % 3 - 1) * 62; },
        yPercent: function (i) { return (i % 2 ? -1 : 1) * 44; },
        rotate: function (i) { return (i % 2 ? -1 : 1) * 26; },
        opacity: 0.15,
      },
      {
        xPercent: 0, yPercent: 0, rotate: 0, opacity: 1,
        ease: "none", stagger: 0.05,
      },
      0
    ).fromTo(
      stage.querySelectorAll("[data-frac-line]"),
      { opacity: 0, y: 28 },
      { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
      0.2
    );
  }

  /* Signature: aurora — curtains drift while the peaks hold. ------------ */
  function aurora() {
    var stage = document.querySelector("[data-sig='aurora']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=190%",
        scrub: 1,
        pin: true,
      },
    });

    tl.to(stage.querySelectorAll("[data-veil='a']"),
          { xPercent: 16, yPercent: -12, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-veil='b']"),
          { xPercent: -20, yPercent: -6, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-ridge='far']"), { yPercent: -8, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-ridge='near']"), { yPercent: -22, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-aurora-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.22, ease: "power2.out" },
        0.12
      );

    /* the curtains keep breathing on their own */
    gsap.to(stage.querySelectorAll("[data-shimmer]"), {
      opacity: 0.35,
      duration: 3.2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
      stagger: { each: 0.7, from: "random" },
    });
  }

  /* ---------------------------------------------------------------------
     Signatures written for the themed tier.

     Ranks 11-25 each declared a signature that drove nothing at all: every
     function above opens by querying for a [data-sig] stage, and only the
     ten bespoke fragments ever contained one. tools/gen_setpiece.py now
     writes that stage for all fifteen, so seven of the timelines above
     drive themed pages unchanged. These six are new, for levels the bespoke
     vocabulary had no way to describe.
     ------------------------------------------------------------------- */

  /* Signature: flood — the tide climbs the pillars. Freedom08. ---------- */
  function flood() {
    var stage = document.querySelector("[data-sig='flood']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=200%",
        scrub: 0.85,
        pin: true,
      },
    });

    /* The tide is the whole point: four and a quarter minutes of the level
       is holding a line while the water comes up. */
    tl.fromTo(
      stage.querySelector("[data-tide]"),
      { yPercent: 100 },
      { yPercent: 8, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelectorAll("[data-pillar]"),
        { yPercent: 26, opacity: 0.3 },
        { yPercent: 0, opacity: 1, stagger: 0.04, ease: "none" },
        0
      )
      .to(stage.querySelectorAll("[data-banner]"), { yPercent: -22, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-flood-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.12
      );
  }

  /* Signature: twin — two halves close on the seam. Codependence. ------- */
  function twin() {
    var stage = document.querySelector("[data-sig='twin']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=185%",
        scrub: 0.7,
        pin: true,
      },
    });

    /* Deliberately not mirrored. The level's gameplay is unsymmetrical, and
       two halves sliding in by the same amount would say the opposite. */
    tl.fromTo(
      stage.querySelectorAll("[data-twin='a']"),
      { xPercent: -18, yPercent: -10 },
      { xPercent: 0, yPercent: 0, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelectorAll("[data-twin='b']"),
        { xPercent: 24, yPercent: 12 },
        { xPercent: 0, yPercent: 0, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelector("[data-seam]"),
        { scaleX: 0.1, opacity: 0 },
        { scaleX: 1, opacity: 1, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelectorAll("[data-link]"),
        { scaleY: 0, transformOrigin: "top center" },
        { scaleY: 1, stagger: 0.03, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelectorAll("[data-twin-line]"),
        { opacity: 0, y: 28 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.15
      );
  }

  /* Signature: whiteout — the funnel turns and the debris flies past.
     Black Blizzard. ----------------------------------------------------- */
  function whiteout() {
    var stage = document.querySelector("[data-sig='whiteout']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=195%",
        scrub: 0.9,
        pin: true,
      },
    });

    tl.fromTo(
      stage.querySelector("[data-funnel]"),
      { rotate: -9, scale: 0.82, opacity: 0.4 },
      { rotate: 7, scale: 1.12, opacity: 1, ease: "none" },
      0
    )
      .to(stage.querySelectorAll("[data-gust]"), { xPercent: 60, ease: "none" }, 0)
      .to(stage.querySelectorAll("[data-debris]"), { xPercent: 130, ease: "none" }, 0)
      .fromTo(
        stage.querySelectorAll("[data-white-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.22, ease: "power2.out" },
        0.14
      );
  }

  /* Signature: overgrow — growth closes in from every edge. The Golden. -- */
  function overgrow() {
    var stage = document.querySelector("[data-sig='overgrow']");
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

    /* Scaling from the left edge of each vine, so they read as creeping out
       from where they are anchored rather than inflating in place. */
    tl.fromTo(
      stage.querySelectorAll("[data-creep='a']"),
      { scaleX: 0.08, transformOrigin: "left center" },
      { scaleX: 1, stagger: 0.05, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelectorAll("[data-creep='b']"),
        { scaleX: 0.08, transformOrigin: "right center" },
        { scaleX: 1, stagger: 0.05, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelectorAll("[data-frond]"),
        { scale: 0.2, opacity: 0 },
        { scale: 1, opacity: 1, stagger: 0.02, ease: "none" },
        0.05
      )
      .fromTo(
        stage.querySelectorAll("[data-grow-line]"),
        { opacity: 0, y: 28 },
        { opacity: 1, y: 0, stagger: 0.2, ease: "power2.out" },
        0.18
      );
  }

  /* Signature: iris — the eye opens. Ocular Miracle. -------------------- */
  function iris() {
    var stage = document.querySelector("[data-sig='iris']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=200%",
        scrub: 0.8,
        pin: true,
      },
    });

    /* The lids retract first and the pupil dilates behind them, so the
       reveal is the eye opening rather than two bars sliding away. */
    tl.fromTo(
      stage.querySelector("[data-lid='t']"),
      { yPercent: 0 },
      { yPercent: -78, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelector("[data-lid='b']"),
        { yPercent: 0 },
        { yPercent: 78, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelector("[data-pupil]"),
        { scale: 0.28 },
        { scale: 1.1, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelector("[data-iris]"),
        { scale: 0.86, rotate: -8 },
        { scale: 1.04, rotate: 6, ease: "none" },
        0
      )
      .fromTo(
        stage.querySelectorAll("[data-iris-line]"),
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, stagger: 0.22, ease: "power2.out" },
        0.3
      );
  }

  /* Signature: corrupt — the channels separate and the rows tear.
     Killbot. ------------------------------------------------------------ */
  function corrupt() {
    var stage = document.querySelector("[data-sig='corrupt']");
    if (!stage) return;

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: stage,
        start: "top top",
        end: "+=180%",
        scrub: 0.5,
        pin: true,
      },
    });

    /* Channels pull apart in opposite directions: the level's whole trick is
       that what you are looking at is not where the gameplay is. */
    tl.fromTo(
      stage.querySelector("[data-chan='r']"),
      { xPercent: -7, yPercent: 2 },
      { xPercent: 6, yPercent: -3, ease: "none" },
      0
    )
      .fromTo(
        stage.querySelector("[data-chan='g']"),
        { xPercent: 7, yPercent: -2 },
        { xPercent: -6, yPercent: 3, ease: "none" },
        0
      )
      .to(
        stage.querySelectorAll("[data-tear]"),
        {
          xPercent: function (i) { return (i % 5 - 2) * 26; },
          ease: "none",
        },
        0
      )
      .fromTo(
        stage.querySelectorAll("[data-corrupt-line]"),
        { opacity: 0, y: 26 },
        { opacity: 1, y: 0, stagger: 0.18, ease: "power2.out" },
        0.12
      );

    /* Hazard plates blink on their own clock, not the scroll's. */
    gsap.to(stage.querySelectorAll("[data-flicker]"), {
      opacity: 0.05,
      duration: 0.12,
      repeat: -1,
      yoyo: true,
      ease: "steps(1)",
      stagger: { each: 0.19, from: "random" },
    });
  }

  /* Shared: the hero gains depth as you leave it. ------------------------

     Deliberately on the copy, not on the art. The art already carries its
     own slow drift (art.css, [data-art-drift]) as a CSS animation on the
     <svg>, and a scroll-driven transform on the same element would simply
     replace it. The art is also sized exactly to its clipping box, so
     lifting it would expose the field underneath. Moving the words instead
     costs nothing and reads as the same parallax. */
  function heroDepth() {
    var hero = document.querySelector(".hero");
    if (!hero) return;
    var title = hero.querySelector(".hero__title");
    var foot = hero.querySelector(".hero__foot");
    var eyebrow = hero.querySelector(".hero__eyebrow");

    var tl = gsap.timeline({
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "bottom top",
        scrub: 0.5,
      },
    });

    if (eyebrow) tl.to(eyebrow, { yPercent: -140, opacity: 0.2, ease: "none" }, 0);
    if (title) tl.to(title, { yPercent: -34, opacity: 0.55, ease: "none" }, 0);
    if (foot) tl.to(foot, { yPercent: -14, opacity: 0.4, ease: "none" }, 0);
  }

  reveals();
  heroDepth();
  countdown();

  /* Triggers are created from a layout that has not settled: the hero art is
     a large inline SVG and the display faces are webfonts, both of which
     change the page height after this script runs. Stale measurements are not
     cosmetic - on the landing page they left 34 of 50 triggers reporting
     active at scroll 0, so the countdown's palette stuck on whichever level
     won the race.

     Firing on load and on fonts.ready is not enough on its own, because both
     can resolve before the art has finished laying out. Watching the document
     height instead means we re-measure whenever the page actually moves,
     whatever caused it. */
  function settle() {
    window.ScrollTrigger.refresh();
  }

  if (document.readyState === "complete") {
    settle();
  } else {
    window.addEventListener("load", settle, { once: true });
  }
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(settle);
  }

  if (window.ResizeObserver) {
    var lastHeight = document.documentElement.scrollHeight;
    var pending;
    new ResizeObserver(function () {
      var h = document.documentElement.scrollHeight;
      if (Math.abs(h - lastHeight) < 4) return;
      lastHeight = h;
      clearTimeout(pending);
      pending = setTimeout(settle, 60);
    }).observe(document.body);
  }

  /* Spotlight — the themed tier's one full-size moment. --------------------

     Those fifteen levels each declare a theme.signature that drove no markup
     and no motion at all; every signature function below looks for a
     [data-sig] element that only bespoke fragments contain.

     Reveal and parallax both run off live geometry read on scroll, which is
     the same approach that fixed the countdown palette. Two earlier attempts
     failed in ways worth recording: gsap.from left the panel at opacity 0
     when its ScrollTrigger did not fire, and IntersectionObserver never
     reports at all in an offscreen or zero-height viewport. Reading the rect
     each frame cannot go stale and cannot depend on the page being visible
     to some other API.

     The hidden state lives behind [data-enter], set here, so a page whose
     JavaScript never runs simply shows the panel. */
  function spotlight() {
    var stage = document.querySelector(".spotlight");
    if (!stage) return;

    var inner = stage.querySelector(".spotlight__inner");
    stage.setAttribute("data-enter", "");

    var shown = false;
    var ticking = false;
    var seenScroll = false;

    /* The reveal runs synchronously in the scroll handler, not inside the
       rAF callback with the parallax. requestAnimationFrame is throttled or
       suspended entirely for a document the browser considers not visible,
       and a reveal that never runs leaves the panel invisible. It costs one
       rect read per scroll and stops entirely once the panel has appeared. */
    function reveal() {
      if (shown) return;
      var vh = window.innerHeight || document.documentElement.clientHeight;
      if (!vh) return;
      var r = stage.getBoundingClientRect();
      if (r.top < vh * 0.82 && r.bottom > 0) {
        shown = true;
        stage.setAttribute("data-enter", "in");
      }
    }

    function frame() {
      ticking = false;
      var vh = window.innerHeight || document.documentElement.clientHeight;
      if (!vh) return;
      var r = stage.getBoundingClientRect();
      if (r.bottom < 0 || r.top > vh) return;
      var off = ((r.top + r.bottom) / 2 - vh / 2) / vh;
      inner.style.transform =
        "translate3d(0," + (off * -34).toFixed(1) + "px,0)";
    }

    function onScroll() {
      seenScroll = true;
      reveal();
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(frame);
      }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    reveal();
    frame();

    /* Failsafe. Everything above depends on scroll events arriving, and there
       are real conditions where they never do -- a background or offscreen
       document has its scroll events and animation frames suspended
       entirely. If not one scroll event has landed after a few seconds, the
       page is not being driven the way this assumes, so show the panel
       rather than leave it invisible. Losing an animation is a far cheaper
       failure than losing the content. */
    setTimeout(function () {
      if (!shown && !seenScroll) stage.setAttribute("data-enter", "in");
    }, 2500);
  }

  var sig = document.documentElement.dataset.signature;
  if (sig === "fracture") fracture();
  if (sig === "aurora") aurora();
  if (sig === "surge") surge();
  if (sig === "ignite") ignite();
  if (sig === "pulse") pulse();
  if (sig === "orbit") orbit();
  if (sig === "eclipse") eclipse();
  if (sig === "glitch-assemble") glitchAssemble();
  if (sig === "slash") slash();
  if (sig === "prism") prism();
  if (sig === "descend") descend();
  if (sig === "flood") flood();
  if (sig === "twin") twin();
  if (sig === "whiteout") whiteout();
  if (sig === "overgrow") overgrow();
  if (sig === "iris") iris();
  if (sig === "corrupt") corrupt();
  spotlight();
})();
