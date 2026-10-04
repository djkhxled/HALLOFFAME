/* gg.js — the interface for GeometryGuessr.
 *
 * Rules live in gg-core.js (checked in tests/gg.check.html); this file draws, listens
 * and plays sounds, and decides nothing. No network of any kind: the data is in the
 * page, the images are this site's own, and the best run is kept in localStorage.
 */
(function () {
  "use strict";

  var G = window.GGCore;
  var root = document.querySelector("[data-gg]");
  var dataEl = document.getElementById("gg-data");
  if (!G || !root || !dataEl) return;

  var data = JSON.parse(dataEl.textContent);
  var levels = data.levels, shots = data.shots;
  var byId = {};
  levels.forEach(function (l) { byId[l.id] = l; });
  var BASE = root.getAttribute("data-shots") || "";
  var SHARE_URL = root.getAttribute("data-share-url") || "";

  function $(sel) { return root.querySelector(sel); }
  var docEl = document.documentElement;
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var el = {
    bg: $("[data-bg]"), start: $("[data-start]"), best: $("[data-best]"),
    bestNamed: $("[data-best-named]"), bestScore: $("[data-best-score]"),
    round: $("[data-round]"), named: $("[data-named]"), score: $("[data-score]"),
    frame: $("[data-frame]"), shot: $("[data-shot]"), flash: $("[data-flash]"), stamp: $("[data-stamp]"),
    burst: $("[data-burst]"),
    ask: $("[data-ask]"), input: $("[data-input]"), options: $("[data-options]"), guess: $("[data-guess]"), hint: $("[data-hint]"),
    spot: $("[data-spot]"), spotLevel: $("[data-spot-level]"), spotQ: $("[data-spot-q]"), track: $("[data-track]"),
    gap: $("[data-gap]"), truth: $("[data-truth]"), truthLabel: $("[data-truth-label]"),
    cube: $("[data-cube]"), cubeLabel: $("[data-cube-label]"), lock: $("[data-lock]"),
    reveal: $("[data-reveal]"), revealK: $("[data-reveal-k]"), revealName: $("[data-reveal-name]"),
    revealBy: $("[data-reveal-by]"), revealSaid: $("[data-reveal-said]"), revealPts: $("[data-reveal-pts]"), next: $("[data-next]"),
    over: root.querySelector('[data-screen="over"]'), overTitle: $("[data-over-title]"), overNamed: $("[data-over-named]"),
    overScore: $("[data-over-score]"), overBest: $("[data-over-best]"), strip: $("[data-strip]"),
    again: $("[data-again]"), share: $("[data-share]"), copied: $("[data-copied]"),
    sound: $("[data-sound]"), live: $("[data-live]")
  };

  function fmt(n) { return Number(n).toLocaleString("en-US"); }
  function say(text) { el.live.textContent = ""; setTimeout(function () { el.live.textContent = text; }, 30); }
  function restart(node, cls) { node.classList.remove(cls); void node.offsetWidth; node.classList.add(cls); }

  /* Storage: one key, the best run and the sound setting ----------------------- */

  var KEY = "hall-of-extremes.gg.v1";
  var store = { v: 1, best: null, runs: 0, sound: true, name: "" };
  try {
    var saved = JSON.parse(window.localStorage.getItem(KEY) || "null");
    if (saved && saved.v === 1) {
      if (saved.best && typeof saved.best.named === "number" && typeof saved.best.score === "number") store.best = saved.best;
      if (typeof saved.runs === "number") store.runs = saved.runs;
      if (typeof saved.sound === "boolean") store.sound = saved.sound;
      if (typeof saved.name === "string") store.name = saved.name.slice(0, 20);
    }
  } catch (e) { /* private mode, or nothing saved: play on without */ }
  function save() {
    try { window.localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* not saved, nothing breaks */ }
  }

  /* Sound: synthesised, no files ------------------------------------------------ */

  var ctx = null, master = null;
  function unlock() {
    try {
      if (!ctx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        ctx = new AC();
        master = ctx.createGain();
        master.gain.value = 0.16;
        master.connect(ctx.destination);
      }
      if (ctx.state === "suspended") ctx.resume();
    } catch (e) { ctx = null; }
  }
  function tone(freq, at, dur, type, gain, slideTo) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, at);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, at + dur);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(gain, at + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g); g.connect(master); o.start(at); o.stop(at + dur + 0.03);
  }
  function play(fn) {
    if (!store.sound) return;
    try { unlock(); if (ctx && ctx.state === "running") fn(ctx.currentTime + 0.005); } catch (e) { /* never break over a beep */ }
  }
  var SFX = {
    start: function (t) { tone(220, t, 0.35, "sawtooth", 0.25, 880); tone(440, t + 0.12, 0.3, "triangle", 0.4, 1320); },
    tick: function (t) { tone(1240, t, 0.03, "square", 0.12); },
    pick: function (t) { tone(760, t, 0.06, "triangle", 0.4); },
    right: function (t) { [523.25, 659.25, 783.99, 1046.5].forEach(function (n, k) { tone(n, t + k * 0.07, 0.25, "triangle", 0.6); }); },
    wrong: function (t) { tone(180, t, 0.28, "sawtooth", 0.45, 90); tone(120, t + 0.18, 0.35, "square", 0.3, 70); },
    lock: function (t) { tone(520, t, 0.05, "square", 0.3); tone(1040, t + 0.05, 0.08, "triangle", 0.3); },
    count: function (t) { tone(1500, t, 0.025, "triangle", 0.18); },
    perfect: function (t) { [784, 988, 1175, 1568, 1976].forEach(function (n, k) { tone(n, t + k * 0.06, 0.32, "triangle", 0.55); }); },
    great: function (t) { [659, 880, 1175].forEach(function (n, k) { tone(n, t + k * 0.07, 0.26, "triangle", 0.5); }); },
    good: function (t) { [587, 784].forEach(function (n, k) { tone(n, t + k * 0.08, 0.24, "triangle", 0.45); }); },
    close: function (t) { tone(523, t, 0.22, "triangle", 0.4); },
    far: function (t) { tone(330, t, 0.25, "triangle", 0.4, 247); },
    over: function (t) { [392, 330, 262, 196].forEach(function (n, k) { tone(n, t + k * 0.16, 0.36, "triangle", 0.5); }); },
    best: function (t) { [523, 659, 784, 1047, 784, 1047, 1319].forEach(function (n, k) { tone(n, t + k * 0.09, 0.3, "triangle", 0.55); }); }
  };
  function paintSound() { el.sound.setAttribute("aria-pressed", String(store.sound)); }
  el.sound.addEventListener("click", function () {
    store.sound = !store.sound; paintSound(); save();
    if (store.sound) { unlock(); play(SFX.pick); }
  });
  paintSound();

  /* The backdrop: a level that plays itself behind everything -------------------- */

  var backdrop = (function () {
    var canvas = el.bg, g = canvas.getContext("2d");
    if (!g) return { speed: function () {} };
    var W = 0, H = 0, dpr = 1, unit = 40, ground = 0;
    var layers = [], stars = [];
    var travelled = 0, speedNow = 1, speedTarget = 1;
    var hue = 282, hueTarget = 282, last = 0, t0 = performance.now();
    var BEAT = 60 / 128;
    var cube = { y: 0, vy: 0, rot: 0, air: false };
    // The game's cube spins at one steady rate while it is in the air: half a turn
    // over a normal jump. A jump here lasts 2 * 17.5 / 62 seconds of scroll time
    // (launch speed and gravity below), so that is 180 degrees over that long.
    // On landing it settles onto the nearest flat side.
    var JUMP_V = 17.5, PAD_V = 23, GRAVITY = 62;
    var SPIN = 180 / (2 * JUMP_V / GRAVITY);   // degrees per second of scroll time
    var trail = [];
    var running = false;

    function rnd(a, b) { return a + Math.random() * (b - a); }

    function makeLayer(scale, speed, near) {
      return { scale: scale, speed: speed, near: near, objs: [], next: 0 };
    }

    function spawn(L) {
      var u = unit * L.scale, x = L.next, kind = Math.random(), o;
      if (L.near) {
        if (kind < 0.45) o = { t: "spike", x: x, n: Math.random() < 0.6 ? 1 : 2 };
        else if (kind < 0.75) o = { t: "block", x: x, w: 1 + Math.floor(Math.random() * 2), h: 1 };
        else o = { t: "pad", x: x };
      } else {
        if (kind < 0.3) o = { t: "spike", x: x, n: 1 + Math.floor(Math.random() * 3) };
        else if (kind < 0.7) o = { t: "block", x: x, w: 1 + Math.floor(Math.random() * 3), h: 1 + Math.floor(Math.random() * 4) };
        else if (kind < 0.88) o = { t: "saw", x: x, r: rnd(0.8, 1.6), y: rnd(2.5, 5) };
        else o = { t: "plat", x: x, w: 3 + Math.floor(Math.random() * 3), y: rnd(2.5, 4.5) };
      }
      var width = o.t === "spike" ? o.n : o.t === "block" ? o.w : o.t === "plat" ? o.w : o.t === "saw" ? o.r * 2 : 1;
      o.wpx = width * u;
      L.objs.push(o);
      L.next = x + o.wpx + u * (L.near ? rnd(3.2, 6.5) : rnd(1.5, 4.5));
    }

    function resize() {
      var r = canvas.getBoundingClientRect();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      W = Math.max(1, r.width); H = Math.max(1, r.height);
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      var view = Math.min(H, window.innerHeight || H);
      unit = Math.max(24, Math.min(54, view / 14));
      ground = Math.min(H, view) * 0.8;
      stars = [];
      for (var i = 0; i < Math.round(W * view / 9000); i++) stars.push({ x: Math.random() * W, y: Math.random() * ground * 0.9, r: Math.random() * 1.4 + 0.3, p: Math.random() * 6.28 });
      layers = [makeLayer(0.55, 0.42, false), makeLayer(1, 1, true)];
      layers.forEach(function (L) { L.next = travelled * L.speed + W * 0.35; });
      cube.y = 0; cube.vy = 0; cube.air = false;
    }

    function path(L, o, sx) {
      var u = unit * L.scale, base = L.near ? ground : ground - unit * 0.2;
      g.beginPath();
      if (o.t === "spike") {
        for (var i = 0; i < o.n; i++) {
          g.moveTo(sx + i * u, base); g.lineTo(sx + i * u + u / 2, base - u * 0.95); g.lineTo(sx + (i + 1) * u, base); g.closePath();
        }
      } else if (o.t === "block") {
        g.rect(sx, base - o.h * u, o.w * u, o.h * u);
      } else if (o.t === "plat") {
        g.rect(sx, base - o.y * u, o.w * u, u * 0.5);
      } else if (o.t === "pad") {
        g.ellipse(sx + u / 2, base - u * 0.08, u * 0.42, u * 0.14, 0, Math.PI, 0);
      } else if (o.t === "saw") {
        var cx = sx + o.r * u, cy = base - o.y * u, rr = o.r * u, teeth = 12, a0 = (performance.now() / 600) % 6.283;
        for (var k = 0; k <= teeth * 2; k++) {
          var a = a0 + (k / (teeth * 2)) * 6.283, rad = k % 2 ? rr * 0.78 : rr;
          if (k === 0) g.moveTo(cx + Math.cos(a) * rad, cy + Math.sin(a) * rad); else g.lineTo(cx + Math.cos(a) * rad, cy + Math.sin(a) * rad);
        }
        g.closePath();
      }
    }

    function frame(now) {
      if (!running) return;
      var dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
      speedNow += (speedTarget - speedNow) * Math.min(1, dt * 2.5);
      var px = unit * 6.4 * speedNow * dt;
      travelled += px;

      var t = (now - t0) / 1000, phase = (t % BEAT) / BEAT, pulse = Math.exp(-phase * 5);
      var bar = Math.floor(t / (BEAT * 8));
      hueTarget = 282 + ((bar * 47) % 360);
      var dh = ((hueTarget - hue + 540) % 360) - 180;
      hue = (hue + dh * Math.min(1, dt * 1.2) + 360) % 360;
      docEl.style.setProperty("--gg-pulse", pulse.toFixed(3));
      docEl.style.setProperty("--gg-hue", String(Math.round(hue)));

      draw(t, pulse, dt, px);
      requestAnimationFrame(frame);
    }

    function draw(t, pulse, dt, px) {
      var h = hue;
      var sky = g.createLinearGradient(0, 0, 0, H);
      sky.addColorStop(0, "hsl(" + h + ",70%,5%)");
      sky.addColorStop(0.75, "hsl(" + ((h + 20) % 360) + ",75%,13%)");
      sky.addColorStop(1, "hsl(" + ((h + 30) % 360) + ",80%,8%)");
      g.fillStyle = sky; g.fillRect(0, 0, W, H);

      for (var i = 0; i < stars.length; i++) {
        var s = stars[i]; s.x -= px * 0.08; if (s.x < 0) s.x += W;
        g.globalAlpha = 0.35 + 0.35 * Math.sin(t * 2 + s.p);
        g.fillStyle = "#fff"; g.fillRect(s.x, s.y, s.r, s.r);
      }
      g.globalAlpha = 1;

      // a sun that breathes on the beat
      var sx = W * 0.74, sy = ground - unit * 2.6, sr = unit * 4.2 * (1 + pulse * 0.06);
      var sun = g.createRadialGradient(sx, sy, 0, sx, sy, sr * 1.6);
      sun.addColorStop(0, "hsla(" + ((h + 60) % 360) + ",100%,65%,0.32)");
      sun.addColorStop(0.45, "hsla(" + ((h + 40) % 360) + ",100%,55%,0.12)");
      sun.addColorStop(1, "hsla(" + h + ",100%,50%,0)");
      g.fillStyle = sun; g.beginPath(); g.arc(sx, sy, sr * 1.6, 0, 6.283); g.fill();
      for (var b = 0; b < 7; b++) {   // the sun's bands
        var by = sy - sr * 0.1 + b * sr * 0.14;
        g.fillStyle = "hsla(" + ((h + 50) % 360) + ",100%,62%," + (0.18 - b * 0.02) + ")";
        g.fillRect(sx - sr * 0.9, by, sr * 1.8, sr * 0.06);
      }

      layers.forEach(function (L) {
        var off = travelled * L.speed;
        while (L.next < off + W + unit * 6) spawn(L);
        L.objs = L.objs.filter(function (o) { return o.x + o.wpx > off - unit * 4; });
        var glow = "hsl(" + ((h + (L.near ? 180 : 40)) % 360) + ",100%," + (L.near ? 62 : 55) + "%)";
        g.fillStyle = L.near ? "#05020b" : "hsl(" + h + ",55%,9%)";
        g.lineJoin = "round";
        L.objs.forEach(function (o) {
          var x = o.x - off;
          if (x > W + unit * 4 || x + o.wpx < -unit * 4) return;
          path(L, o, x);
          g.fill();
          if (L.near) {
            g.strokeStyle = glow; g.globalAlpha = 0.22 + pulse * 0.2; g.lineWidth = 7; g.stroke();
            g.globalAlpha = 1; g.lineWidth = 2; g.stroke();
          } else {
            g.strokeStyle = glow; g.globalAlpha = 0.35; g.lineWidth = 1.5; g.stroke(); g.globalAlpha = 1;
          }
        });
      });

      // ground, with its moving tiles and a glowing edge
      g.fillStyle = "#04020a"; g.fillRect(0, ground, W, H - ground);
      var tile = unit * 2, shift = -(travelled % tile);
      g.strokeStyle = "hsla(" + ((h + 180) % 360) + ",100%,60%,0.12)"; g.lineWidth = 1;
      for (var x = shift; x < W; x += tile) { g.beginPath(); g.moveTo(x, ground); g.lineTo(x - unit * 1.2, H); g.stroke(); }
      var edge = g.createLinearGradient(0, ground - unit, 0, ground + 2);
      edge.addColorStop(0, "hsla(" + ((h + 180) % 360) + ",100%,60%,0)");
      edge.addColorStop(1, "hsla(" + ((h + 180) % 360) + ",100%,60%," + (0.22 + pulse * 0.25) + ")");
      g.fillStyle = edge; g.fillRect(0, ground - unit, W, unit);
      var line = g.createLinearGradient(0, 0, W, 0);
      line.addColorStop(0, "hsla(" + ((h + 180) % 360) + ",100%,70%,0)");
      line.addColorStop(0.5, "hsla(" + ((h + 180) % 360) + ",100%,72%,1)");
      line.addColorStop(1, "hsla(" + ((h + 180) % 360) + ",100%,70%,0)");
      g.fillStyle = line; g.fillRect(0, ground - 1, W, 2.5);

      drawCube(dt);
    }

    function drawCube(dt) {
      var near = layers[1], off = travelled * near.speed, u = unit;
      var cx = W * 0.2, size = u * 0.92;
      // jump for whatever is coming: physics run on the scroll's own clock, so a
      // slower level is the same jump in slow motion, and every jump clears 3.6 units
      var ds = dt * speedNow, reach = u * 1.8;
      if (!cube.air) {
        for (var i = 0; i < near.objs.length; i++) {
          var o = near.objs[i], ox = o.x - off, mid = ox + o.wpx / 2;
          if (ox + o.wpx < cx - size / 2) continue;
          if (o.t === "pad") {
            if (Math.abs(mid - cx) < u * 0.25) { cube.vy = -u * PAD_V; cube.air = true; }
          } else if (mid - cx < reach) { cube.vy = -u * JUMP_V; cube.air = true; }
          break;
        }
      }
      if (cube.air) {
        cube.vy += u * GRAVITY * ds;
        cube.y += cube.vy * ds;
        cube.rot += SPIN * ds;
        if (cube.y >= 0) { cube.y = 0; cube.vy = 0; cube.air = false; }
      } else {
        var flat = Math.round(cube.rot / 90) * 90;          // settle onto the nearest side
        cube.rot += (flat - cube.rot) * Math.min(1, ds * 18);
        if (Math.abs(flat - cube.rot) < 0.5) cube.rot = flat % 360;
      }

      var top = ground - size + cube.y;
      trail.push({ x: cx, y: top + size / 2, a: 1 });
      if (trail.length > 18) trail.shift();
      for (var k = 0; k < trail.length; k++) {
        var p = trail[k]; p.x -= unit * 6.4 * speedNow * dt; p.a *= 0.9;
        g.fillStyle = "hsla(" + ((hue + 180) % 360) + ",100%,65%," + (p.a * 0.35) + ")";
        var ts = size * 0.5 * (k / trail.length);
        g.fillRect(p.x - ts / 2, p.y - ts / 2, ts, ts);
      }

      g.save();
      g.translate(cx, top + size / 2);
      g.rotate(cube.rot * Math.PI / 180);
      g.fillStyle = "#a8ff2e"; g.strokeStyle = "#000"; g.lineWidth = 3;
      g.fillRect(-size / 2, -size / 2, size, size); g.strokeRect(-size / 2, -size / 2, size, size);
      g.fillStyle = "#21e6ff"; g.lineWidth = 2;
      g.fillRect(-size * 0.24, -size * 0.24, size * 0.48, size * 0.48); g.strokeRect(-size * 0.24, -size * 0.24, size * 0.48, size * 0.48);
      g.restore();
    }

    function go() { if (running || calm) return; running = true; last = 0; requestAnimationFrame(frame); }
    function stop() { running = false; }

    resize();
    if (calm) { draw(0, 0, 0, 0); }
    else go();
    var rt = null;
    window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { resize(); if (calm) draw(0, 0, 0, 0); }, 120); });
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else go(); });
    return {
      speed: function (s) { speedTarget = s; },
      refit: function () { resize(); if (calm) draw(0, 0, 0, 0); }
    };
  }());

  /* Bursts of squares, for a right name, a perfect spot, a wrong one --------------- */

  var burst = (function () {
    var c = el.burst, g = c.getContext && c.getContext("2d"), parts = [], on = false, last = 0;
    function fit() {
      var r = c.getBoundingClientRect(), d = Math.min(2, window.devicePixelRatio || 1);
      c.width = Math.round(r.width * d); c.height = Math.round(r.height * d);
      g.setTransform(d, 0, 0, d, 0, 0);
      return r;
    }
    function fire(kind) {
      if (!g || calm) return;
      var r = fit(), cx = r.width / 2, cy = r.height * 0.48;
      var palette = kind === "wrong" ? ["#ff3b5c", "#ff8a2b", "#ffd0d8"] : ["#a8ff2e", "#21e6ff", "#ffd23f", "#ff2bd6", "#ffffff"];
      var n = kind === "perfect" ? 140 : kind === "wrong" ? 46 : 80;
      for (var i = 0; i < n; i++) {
        var a = Math.random() * 6.283, v = (kind === "wrong" ? 160 : 260) + Math.random() * (kind === "perfect" ? 620 : 380);
        parts.push({
          x: cx + Math.cos(a) * 20, y: cy + Math.sin(a) * 20,
          vx: Math.cos(a) * v, vy: Math.sin(a) * v - (kind === "wrong" ? 0 : 160),
          s: 4 + Math.random() * (kind === "perfect" ? 11 : 8), r: Math.random() * 6.28, vr: (Math.random() - 0.5) * 14,
          c: palette[Math.floor(Math.random() * palette.length)], life: 1
        });
      }
      if (!on) { on = true; last = 0; requestAnimationFrame(step); }
    }
    function step(now) {
      var dt = Math.min(0.04, (now - (last || now)) / 1000); last = now;
      var w = c.width, h = c.height;
      g.clearRect(0, 0, w, h);
      parts = parts.filter(function (p) { return p.life > 0; });
      parts.forEach(function (p) {
        p.vy += 900 * dt; p.vx *= 0.985; p.x += p.vx * dt; p.y += p.vy * dt; p.r += p.vr * dt; p.life -= dt * 0.85;
        g.save(); g.globalAlpha = Math.max(0, Math.min(1, p.life * 1.6)); g.translate(p.x, p.y); g.rotate(p.r);
        g.fillStyle = p.c; g.fillRect(-p.s / 2, -p.s / 2, p.s, p.s);
        g.strokeStyle = "rgba(0,0,0,.6)"; g.lineWidth = 1.2; g.strokeRect(-p.s / 2, -p.s / 2, p.s, p.s);
        g.restore();
      });
      if (parts.length) requestAnimationFrame(step); else { on = false; g.clearRect(0, 0, w, h); }
    }
    return { fire: fire };
  }());

  /* The logo, one letter at a time --------------------------------------------- */

  (function split() {
    var n = 0;
    root.querySelectorAll("[data-split]").forEach(function (line) {
      var text = line.textContent; line.textContent = "";
      Array.prototype.forEach.call(text, function (ch) {
        var s = document.createElement("span");
        s.className = "gg-ch"; s.textContent = ch; s.style.setProperty("--i", n++);
        line.appendChild(s);
      });
    });
  }());

  /* Views ------------------------------------------------------------------------ */

  function show(view) {
    root.setAttribute("data-view", view);
    root.querySelectorAll("[data-screen]").forEach(function (s) {
      var on = s.getAttribute("data-screen") === view;
      s.hidden = !on;
      if (on && !calm) restart(s, "gg-enter");
    });
    backdrop.speed(view === "title" ? 1 : 0.35);
    requestAnimationFrame(function () { backdrop.refit && backdrop.refit(); });
  }

  function paintBest() {
    if (store.best) {
      el.best.hidden = false;
      el.bestNamed.textContent = fmt(store.best.named);
      el.bestScore.textContent = fmt(store.best.score);
    } else el.best.hidden = true;
  }
  paintBest();

  /* Counting numbers up ----------------------------------------------------------- */

  function countUp(node, from, to, ms, tick) {
    if (calm || from === to) { node.textContent = fmt(to); return; }
    var t0 = performance.now(), lastStep = from;
    function f(now) {
      var k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3), v = Math.round(from + (to - from) * e);
      node.textContent = fmt(v);
      if (tick && Math.floor(v / 100) !== Math.floor(lastStep / 100)) play(SFX.count);
      lastStep = v;
      if (k < 1) requestAnimationFrame(f);
    }
    requestAnimationFrame(f);
  }

  /* The run ------------------------------------------------------------------------ */

  var run = null, shot = null, picks = [], lastLevels = [], chosen = null, phase = "idle";

  function hud() {
    el.round.textContent = (run.round + (phase === "ask" ? 1 : 0)) + "/" + G.ROUNDS;
    el.named.textContent = fmt(run.named);
  }

  function start() {
    unlock();
    play(SFX.start);
    run = G.newRun();
    picks = G.pick(shots, Math.random, G.ROUNDS, lastLevels);
    lastLevels = picks.map(function (i) { return shots[i].l; });
    el.score.textContent = "0";
    show("play");
    deal();
  }

  function deal() {
    shot = shots[picks[run.round]];
    phase = "ask";
    hud();
    el.frame.classList.remove("is-right", "is-wrong");
    el.stamp.classList.remove("is-on");
    el.shot.classList.remove("is-live");
    el.shot.classList.add("is-loading");
    var src = BASE + shot.f;
    var shown = false;
    function reveal() {
      if (shown) return; shown = true;
      el.shot.classList.remove("is-loading");
      if (!calm) restart(el.shot, "is-live");
    }
    el.shot.onload = reveal;
    el.shot.onerror = reveal;
    el.shot.src = src;
    if (el.shot.complete && el.shot.naturalWidth) setTimeout(reveal, 30);
    var ahead = picks[run.round + 1];
    if (ahead !== undefined) { var pre = new Image(); pre.decoding = "async"; pre.src = BASE + shots[ahead].f; }

    el.ask.hidden = false; el.spot.hidden = true; el.reveal.hidden = true;
    el.input.value = ""; chosen = null; closeList(); el.guess.disabled = true;
    el.hint.textContent = "Pick a name from the list. Any of the " + levels.length + " could be the answer.";
    el.hint.classList.remove("is-warn");
    el.input.focus({ preventScroll: true });
    say("Round " + (run.round + 1) + " of " + G.ROUNDS + ". Which demon is this?");
  }

  function guess() {
    if (phase !== "ask") return;
    if (!chosen) {
      el.hint.textContent = "Choose a level from the list first.";
      el.hint.classList.add("is-warn");
      return;
    }
    run = G.nameLevel(run, shot, chosen.id);
    closeList();
    el.ask.hidden = true;
    if (run.history[run.history.length - 1].right) right(); else wrong();
  }

  function right() {
    phase = "spot";
    play(SFX.right);
    el.frame.classList.add("is-right");
    restart(el.flash, "is-right");
    burst.fire("right");
    restart(el.named, "gg-bump");
    hud();
    var lv = byId[shot.l];
    el.spotLevel.textContent = lv.n;
    el.spotQ.textContent = "— yes! Now, where in the level is this?";
    el.spot.hidden = false;
    el.spot.classList.remove("is-done");
    el.lock.hidden = false;
    el.truth.hidden = true; el.gap.hidden = true;
    el.track.classList.remove("is-locked");
    setV(50, true);
    el.cube.focus({ preventScroll: true });
    say("Right, it is " + lv.n + ". Now place the cube where in the level the shot was taken.");
  }

  function wrong() {
    phase = "reveal";
    play(SFX.wrong);
    el.frame.classList.add("is-wrong");
    restart(el.flash, "is-wrong");
    if (!calm) restart(el.frame, "gg-shake");
    burst.fire("wrong");
    hud();
    stampIt("WRONG", "#ff3b5c");
    var lv = byId[shot.l], said = byId[run.history[run.history.length - 1].picked];
    el.reveal.classList.add("is-wrong");
    el.revealK.textContent = "It was";
    el.revealName.textContent = lv.n;
    el.revealBy.textContent = "by " + lv.c + " · at " + shot.p + "%";
    el.revealSaid.textContent = said ? "You said " + said.n : "";
    el.next.textContent = run.over ? "See results" : "Next round";
    el.reveal.hidden = false;
    el.next.focus({ preventScroll: true });
    say("Wrong. It was " + lv.n + " by " + lv.c + ". No points this round.");
  }

  function lock() {
    if (phase !== "spot") return;
    phase = "reveal";
    var before = run.score;
    run = G.placeSpot(run, value);
    var last = run.history[run.history.length - 1], off = Math.abs(value - shot.p), word = G.verdict(off);
    play(SFX.lock);
    el.track.classList.add("is-locked");
    el.spot.classList.add("is-done");
    el.track.style.setProperty("--t", shot.p);
    el.truthLabel.textContent = shot.p + "%";
    el.truth.hidden = false;
    el.gap.hidden = off <= 0;
    el.lock.hidden = true;
    var colours = { perfect: "#a8ff2e", great: "#21e6ff", good: "#ffd23f", close: "#ff8a2b", far: "#ff3b5c" };
    setTimeout(function () {
      play(SFX[word]);
      stampIt(word === "perfect" ? "PERFECT!" : word === "great" ? "GREAT!" : word.toUpperCase(), colours[word]);
      if (word === "perfect") burst.fire("perfect");
    }, 260);

    var lv = byId[shot.l];
    el.reveal.classList.remove("is-wrong");
    el.revealK.textContent = off === 0 ? "Dead on" : off + (off === 1 ? " point off" : " points off");
    el.revealName.textContent = lv.n;
    el.revealBy.textContent = "by " + lv.c + " · at " + shot.p + "%, you said " + value + "%";
    el.revealSaid.textContent = "";
    el.revealPts.textContent = "0";
    el.next.textContent = run.over ? "See results" : "Next round";
    el.reveal.hidden = false;
    countUp(el.revealPts, 0, last.points, 900, true);
    countUp(el.score, before, run.score, 900, false);
    restart(el.score, "gg-bump");
    el.next.focus({ preventScroll: true });
    say(lv.n + " is at " + shot.p + " percent. You said " + value + ". " + last.points + " points.");
  }

  function stampIt(text, colour) {
    el.stamp.textContent = text;
    el.stamp.style.setProperty("--stamp", colour);
    restart(el.stamp, "is-on");
    clearTimeout(stampIt.t);
    stampIt.t = setTimeout(function () { el.stamp.classList.remove("is-on"); }, 1700);
  }

  function next() {
    if (phase !== "reveal") return;
    if (run.over) finish(); else deal();
  }

  function finish() {
    phase = "over";
    var isBest = run.named > 0 && G.better(run, store.best);
    store.runs += 1;
    if (isBest) store.best = { named: run.named, score: run.score };
    save();
    paintBest();
    show("over");
    el.over.classList.toggle("is-best", isBest);
    var all = G.complete(run);
    el.overTitle.textContent = run.score === G.ROUNDS * G.FULL ? "Perfect game!" :
      isBest ? "New best!" : "Final score";
    countUp(el.overNamed, 0, run.named, 700, false);
    countUp(el.overScore, 0, run.score, 1200, false);
    el.overBest.textContent = (all ? "All five demons named. " : run.named + " of " + G.ROUNDS + " named. ") +
      (isBest ? "Your best game yet." :
       store.best ? "Best: " + fmt(store.best.score) + " pts · " + fmt(store.best.named) + "/" + G.ROUNDS + " named" : "");
    el.copied.textContent = "";
    el.strip.textContent = "";
    run.history.forEach(function (h, i) {
      var lv = byId[h.shot.l], li = document.createElement("li");
      li.className = h.right ? "is-right" : "is-wrong";
      li.style.setProperty("--i", i);
      var img = document.createElement("img");
      img.src = BASE + h.shot.f; img.alt = ""; img.loading = "lazy"; img.decoding = "async";
      var pts = document.createElement("span"); pts.className = "gg-strip__pts";
      pts.textContent = h.right ? fmt(h.points) : "✗";
      var txt = document.createElement("span"); txt.className = "gg-strip__txt";
      var name = document.createElement("span"); name.className = "gg-strip__name"; name.textContent = lv.n;
      var meta = document.createElement("span"); meta.className = "gg-strip__meta";
      meta.textContent = h.right ? "at " + h.shot.p + "%, you said " + h.spot + "%" : "you said " + (byId[h.picked] ? byId[h.picked].n : "?");
      txt.appendChild(name); txt.appendChild(meta);
      li.appendChild(img); li.appendChild(pts); li.appendChild(txt);
      el.strip.appendChild(li);
    });
    play(isBest || all ? SFX.best : SFX.over);
    el.again.focus({ preventScroll: true });
    // The score board, when there is one, listens for this (gg-records.js).
    root.dispatchEvent(new CustomEvent("gg:finished", {
      detail: { named: run.named, score: run.score, name: store.name }
    }));
    say((isBest ? "New best. " : "Final score. ") + run.named + " of " + G.ROUNDS + " named, " + run.score + " points.");
  }

  function shareText() {
    var squares = [];
    for (var k = 0; k < G.ROUNDS; k++) {
      var h = run.history[k];
      squares.push(!h ? "\u2b1c" : !h.right ? "\u274c" :
        h.points >= 800 ? "\ud83d\udfe9" : h.points >= 400 ? "\ud83d\udfe8" : h.points > 0 ? "\ud83d\udfe7" : "\u2b1b");
    }
    return "GeometryGuessr " + fmt(run.score) + " / " + fmt(G.ROUNDS * G.FULL) + "\n" + squares.join("") + "\n" +
      run.named + "/" + G.ROUNDS + " demons named" + (SHARE_URL ? "\n" + SHARE_URL : "");
  }

  el.share.addEventListener("click", function () {
    var text = shareText();
    function done(ok) { el.copied.textContent = ok ? "Copied!" : "Couldn't copy"; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallback(text)); });
    } else done(fallback(text));
  });
  function fallback(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  /* The name box ------------------------------------------------------------------ */

  var results = [], active = -1;

  function closeList() {
    el.options.hidden = true; el.options.textContent = "";
    el.input.setAttribute("aria-expanded", "false");
    el.input.removeAttribute("aria-activedescendant");
    results = []; active = -1;
  }

  function choose(lv) {
    chosen = lv;
    el.input.value = lv.n;
    el.guess.disabled = false;
    el.hint.textContent = "Press Enter or Guess to lock in " + lv.n + ".";
    el.hint.classList.remove("is-warn");
    closeList();
    play(SFX.pick);
  }

  function paintList() {
    el.options.textContent = "";
    if (!results.length) { closeList(); return; }
    var q = G.norm(el.input.value);
    results.forEach(function (lv, i) {
      var li = document.createElement("li");
      li.className = "gg-option"; li.id = "gg-opt-" + i;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", String(i === active));
      var name = document.createElement("span");
      name.textContent = lv.n;
      var by = document.createElement("small"); by.textContent = lv.c;
      li.appendChild(name); li.appendChild(by);
      li.addEventListener("mousedown", function (e) { e.preventDefault(); choose(lv); el.input.focus(); });
      el.options.appendChild(li);
    });
    el.options.hidden = false;
    el.input.setAttribute("aria-expanded", "true");
    if (active >= 0) {
      el.input.setAttribute("aria-activedescendant", "gg-opt-" + active);
      var a = el.options.children[active]; if (a && a.scrollIntoView) a.scrollIntoView({ block: "nearest" });
    } else el.input.removeAttribute("aria-activedescendant");
    void q;
  }

  el.input.addEventListener("input", function () {
    chosen = null;
    el.guess.disabled = true;
    results = G.search(levels, el.input.value, 8);
    active = results.length ? 0 : -1;
    var exact = results.filter(function (lv) { return G.norm(lv.n) === G.norm(el.input.value); })[0];
    if (exact) { chosen = exact; el.guess.disabled = false; }
    paintList();
  });

  el.input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" && results.length) { e.preventDefault(); active = (active + 1) % results.length; paintList(); }
    else if (e.key === "ArrowUp" && results.length) { e.preventDefault(); active = (active - 1 + results.length) % results.length; paintList(); }
    else if (e.key === "Escape") { closeList(); }
    else if (e.key === "Enter") {
      if (!el.options.hidden && active >= 0 && results[active]) {
        e.preventDefault();
        var lv = results[active];
        if (chosen && chosen.id === lv.id && G.norm(el.input.value) === G.norm(lv.n)) { closeList(); guess(); }
        else choose(lv);
      }
    }
  });
  el.input.addEventListener("blur", function () { setTimeout(closeList, 120); });
  el.ask.addEventListener("submit", function (e) { e.preventDefault(); guess(); });

  /* The cube on the bar ----------------------------------------------------------- */

  var value = 50, lastTick = 50;
  function setV(v, quiet) {
    v = Math.max(0, Math.min(100, Math.round(v)));
    if (v === value && !quiet) return;
    value = v;
    el.track.style.setProperty("--v", v);
    el.cube.setAttribute("aria-valuenow", String(v));
    el.cube.setAttribute("aria-valuetext", v + " percent");
    el.cubeLabel.textContent = v + "%";
    if (!quiet && Math.abs(v - lastTick) >= 2) { play(SFX.tick); lastTick = v; }
  }
  function fromPointer(e) {
    var rail = el.track.querySelector(".gg-track__rail").getBoundingClientRect();
    return ((e.clientX - rail.left) / rail.width) * 100;
  }
  var dragging = false;
  el.track.addEventListener("pointerdown", function (e) {
    if (phase !== "spot") return;
    dragging = true;
    el.track.classList.add("is-dragging");
    try { el.track.setPointerCapture(e.pointerId); } catch (err) { /* fine */ }
    setV(fromPointer(e));
    el.cube.focus({ preventScroll: true });
    e.preventDefault();
  });
  el.track.addEventListener("pointermove", function (e) { if (dragging && phase === "spot") setV(fromPointer(e)); });
  function endDrag() { dragging = false; el.track.classList.remove("is-dragging"); }
  el.track.addEventListener("pointerup", endDrag);
  el.track.addEventListener("pointercancel", endDrag);
  el.cube.addEventListener("keydown", function (e) {
    if (phase !== "spot") { if (e.key === "Enter") { e.preventDefault(); next(); } return; }
    var step = e.shiftKey ? 5 : 1, k = e.key;
    if (k === "ArrowRight" || k === "ArrowUp") setV(value + step);
    else if (k === "ArrowLeft" || k === "ArrowDown") setV(value - step);
    else if (k === "PageUp") setV(value + 10);
    else if (k === "PageDown") setV(value - 10);
    else if (k === "Home") setV(0);
    else if (k === "End") setV(100);
    else if (k === "Enter" || k === " ") lock();
    else return;
    e.preventDefault();
  });

  /* Buttons ------------------------------------------------------------------------ */

  el.start.addEventListener("click", start);
  el.lock.addEventListener("click", lock);
  el.next.addEventListener("click", next);
  el.again.addEventListener("click", start);

  /* The board script hands back the username it submitted under; this file is the
     one place that writes storage, so it keeps it for next time. */
  root.addEventListener("gg:submitted", function (e) {
    var name = e.detail && typeof e.detail.name === "string" ? e.detail.name.slice(0, 20) : "";
    if (name) { store.name = name; save(); }
  });
})();
