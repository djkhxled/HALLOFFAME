/* game.js — name every extreme demon.
 *
 * No dependencies, and deliberately not part of scroll.js: that file returns
 * early on reduced motion and when GSAP fails to load, and a game should not
 * depend on either.
 *
 * What counts as a right answer is decided at build time (hall/game.py) and
 * arrives as a lookup table. The one rule this file has to get right on its
 * own is norm(), which must match game.py's exactly.
 *
 * Kept cheap on purpose. Naming a level touches one row, one block counter,
 * the score and the bar; nothing is re-rendered, nothing is measured, and the
 * list itself is 1,621 static <li>s whose off-screen blocks the browser skips
 * (content-visibility in game.css). The sound is synthesised, so there is no
 * audio to download.
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-game]");
  var dataEl = document.getElementById("game-data");
  if (!root || !dataEl) return;

  var data = JSON.parse(dataEl.textContent);
  var levels = data.levels;            // [position, id, name, legacy]
  var keys = data.keys;                // answer -> index | [index, ...]
  var total = levels.length;

  function $(sel) { return root.querySelector(sel); }
  var input = $("[data-input]");
  var elScore = $("[data-score]");
  var elPct = $("[data-pct]");
  var elTime = $("[data-time]");
  var elStatus = $("[data-status]");
  var elLive = root.querySelector("[data-live]") || document.querySelector("[data-live]");
  var btnLast = $("[data-last]");
  var btnNamedOnly = $("[data-named-only]");
  var btnSound = $("[data-sound]");
  var btnGiveUp = $("[data-giveup]");
  var btnReset = $("[data-reset]");
  var list = $("[data-list]");
  var result = $("[data-result]");
  var fill = document.querySelector("[data-attempt-fill]");
  var readout = document.querySelector("[data-attempt-pct]");

  var calm = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Rows ------------------------------------------------------------------ */

  var rows = new Array(total);
  var blockOf = new Array(total);
  var blocks = [];
  Array.prototype.forEach.call(list.querySelectorAll("[data-block]"), function (b, n) {
    blocks.push({
      el: b,
      count: b.querySelector("[data-count]"),
      size: b.querySelectorAll(".slot").length,
      found: 0,
    });
    Array.prototype.forEach.call(b.querySelectorAll(".slot"), function (li) {
      var i = +li.getAttribute("data-i");
      rows[i] = li;
      blockOf[i] = n;
    });
  });

  /* A block the browser has skipped (content-visibility:auto in game.css) is
     laid out at a guessed height. The guess in the stylesheet was about half a
     real block at desktop width, so the scrollbar lurched as blocks were drawn
     and grew, and a jump to a far row could land a screen or two off. Measure
     one real block instead and use it for all of them: the page's estimated
     height is then within about 1% of its real height. Rows inside a skipped
     block do report real positions when asked, so nothing else is needed. */
  function sizeBlocks() {
    var first = blocks[0].el;
    var prior = first.style.contentVisibility;
    first.style.contentVisibility = "visible";
    var rowsEl = first.querySelector(".gblock__rows");
    var cols = Math.max(1, getComputedStyle(rowsEl).gridTemplateColumns.split(" ").length);
    var head = rowsEl.offsetTop;
    var rowH = (first.offsetHeight - head) / Math.ceil(blocks[0].size / cols);
    first.style.contentVisibility = prior;
    blocks.forEach(function (b) {
      var h = head + Math.ceil(b.size / cols) * rowH;
      b.el.style.containIntrinsicBlockSize = "auto " + Math.round(h) + "px";
    });
  }

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(sizeBlocks, 200);
  });
  sizeBlocks();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(sizeBlocks);

  var idToIndex = {};
  levels.forEach(function (lv, i) { idToIndex[lv[1]] = i; });

  /* State ----------------------------------------------------------------- */

  var found = new Uint8Array(total);
  var foundCount = 0;
  var over = null;                     // null | "gaveup" | "done"
  var elapsed = 0;                     // ms of time on the page, not wall time
  var runningSince = null;
  var started = false;
  var clock = null;

  /* Storage --------------------------------------------------------------- */
  /* Everything is wrapped: private windows and blocked storage throw, and
     the game must still play. Progress is keyed by AREDL's id, not by rank,
     because ranks move every time the list does. */

  var KEY = "hall-of-extremes.game.v1";
  var memory = null;

  function read() {
    try {
      var raw = window.localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return memory; }
  }

  function write(state) {
    memory = state;
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }

  var saved = read() || {};
  var soundOn = saved.sound !== false;
  var saveTimer = null;

  function snapshot() {
    var ids = [];
    for (var i = 0; i < total; i++) if (found[i]) ids.push(levels[i][1]);
    return { v: 1, found: ids, ms: Math.round(nowMs()), over: over, sound: soundOn };
  }

  function save() { clearTimeout(saveTimer); write(snapshot()); }
  function saveSoon() { clearTimeout(saveTimer); saveTimer = setTimeout(save, 400); }

  /* Matching -------------------------------------------------------------- */

  /* Must match hall/game.py norm(). */
  function norm(s) {
    return s.normalize("NFKD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]/g, "");
  }

  function bucket(key) {
    var b = keys[key];
    if (b === undefined) return null;
    return typeof b === "number" ? [b] : b;
  }

  function firstUnnamed(list_) {
    for (var k = 0; k < list_.length; k++) if (!found[list_[k]]) return list_[k];
    return -1;
  }

  /* Answers are taken the instant they match, as on Sporcle. So typing
     "aurora" on the way to "aurorae" names Aurora at once and clears the box;
     Aurorae is typed afterwards. */
  function onInput(e) {
    if (e && e.isComposing) return;
    if (over) return;
    if (!started) begin();

    var key = norm(input.value);
    if (!key) { say(""); return; }

    var list_ = bucket(key);
    if (!list_) { say(""); return; }

    if (firstUnnamed(list_) === -1) {
      /* Already named: leave the box alone. Clearing it here would make
         "aurorae" untypeable once Aurora was in, since the box would empty
         at "aurora" every time. Enter clears it. */
      say("Already named");
      pulse(rows[list_[0]]);
      return;
    }
    settle(key);
  }

  function settle(key) {
    var list_ = bucket(key);
    if (!list_) return false;
    var target = firstUnnamed(list_);
    input.value = "";
    if (target === -1) {
      say("Already named");
      pulse(rows[list_[0]]);
      return true;
    }
    name(target, true);
    return true;
  }

  function onKey(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      if (over) return;
      var key = norm(input.value);
      if (!key) return;
      if (!settle(key)) {
        say("Not on the list");
        shake();
      }
    } else if (e.key === "Escape") {
      input.value = "";
      say("");
    }
  }

  /* Naming ---------------------------------------------------------------- */

  var SUFFIX = /^(.*?)\s*\(([^()]*)\)\s*$/;

  function paint(i, live) {
    var li = rows[i];
    var full = levels[i][2];
    var m = SUFFIX.exec(full);
    var nameEl = li.lastChild;
    if (m && m[1]) {
      nameEl.textContent = m[1];
      var by = document.createElement("span");
      by.className = "slot__by";
      by.textContent = "(" + m[2] + ")";
      nameEl.appendChild(document.createTextNode(" "));
      nameEl.appendChild(by);
    } else {
      nameEl.textContent = full;
    }
    li.classList.add("is-found");
    li.removeAttribute("aria-hidden");
    if (live) {
      motion(li,
        [{ backgroundColor: "color-mix(in srgb, var(--accent) 42%, transparent)" },
         { backgroundColor: "transparent" }],
        { duration: 900, easing: "ease-out" });
      motion(nameEl,
        [{ opacity: 0, transform: "translateY(0.4em) scale(0.94)" },
         { opacity: 1, transform: "none" }],
        { duration: 420, easing: "cubic-bezier(0.22, 1, 0.36, 1)" });
    }
  }

  function name(i, live) {
    found[i] = 1;
    foundCount++;
    paint(i, live);

    var b = blocks[blockOf[i]];
    b.found++;
    b.count.textContent = b.found + " / " + b.size;
    var blockDone = b.found === b.size;
    if (blockDone) b.el.classList.add("is-done");

    renderScore();
    showLast(i);

    if (live) {
      announce(levels[i][2] + ", number " + levels[i][0] + ". " +
               foundCount + " of " + total + " named.");
      bump(elScore);
      say("");
      chime(blockDone, foundCount === total);
      saveSoon();
      if (foundCount === total) finish("done");
    }
  }

  var lastIndex = -1;
  function showLast(i) {
    lastIndex = i;
    var m = SUFFIX.exec(levels[i][2]);
    $("[data-last-name]").textContent = m && m[1] ? m[1] : levels[i][2];
    $("[data-last-rank]").textContent = "#" + levels[i][0];
    btnLast.hidden = false;
  }

  btnLast.addEventListener("click", function () {
    if (lastIndex < 0) return;
    rows[lastIndex].scrollIntoView({ block: "center", behavior: calm ? "auto" : "smooth" });
    pulse(rows[lastIndex]);
  });

  /* Feedback -------------------------------------------------------------- */

  /* Every animation in the game goes through here, so reduced motion is
     honoured in exactly one place and cannot be forgotten by the next one. */
  function motion(el, frames, opts) {
    if (calm || !el || !el.animate) return;
    el.animate(frames, opts);
  }

  function say(text) { elStatus.textContent = text; }
  function announce(text) { if (elLive) elLive.textContent = text; }

  function pulse(el) {
    motion(el,
      [{ backgroundColor: "color-mix(in srgb, var(--accent) 30%, transparent)" },
       { backgroundColor: "transparent" }],
      { duration: 700, easing: "ease-out" });
  }

  function bump(el) {
    motion(el, [{ transform: "scale(1.22)" }, { transform: "scale(1)" }],
      { duration: 240, easing: "cubic-bezier(0.22, 1, 0.36, 1)" });
  }

  function shake() {
    motion(input,
      [{ transform: "translateX(0)" }, { transform: "translateX(-6px)" },
       { transform: "translateX(6px)" }, { transform: "translateX(-3px)" },
       { transform: "translateX(0)" }],
      { duration: 260 });
  }

  /* One decimal under 10%: 3 of 1,621 is 0.2%, and "0%" reads as nothing. */
  function pctText() {
    var pct = total ? (foundCount / total) * 100 : 0;
    return (pct < 10 && foundCount ? pct.toFixed(1) : Math.round(pct)) + "%";
  }

  function renderScore() {
    var pct = total ? (foundCount / total) * 100 : 0;
    elScore.textContent = foundCount.toLocaleString("en-US");
    elPct.textContent = pctText();
    if (fill) fill.style.transform = "scaleX(" + (pct / 100).toFixed(4) + ")";
    if (readout) readout.textContent = Math.round(pct) + "%";
  }

  /* Clock ----------------------------------------------------------------- */
  /* Counts time spent on the page. Closing the tab and coming back next week
     must not add a week, so it accumulates only while visible and only after
     the first keystroke. */

  function nowMs() {
    return elapsed + (runningSince === null ? 0 : performance.now() - runningSince);
  }

  function fmt(ms) {
    var s = Math.floor(ms / 1000);
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    var two = function (n) { return (n < 10 ? "0" : "") + n; };
    return h ? h + ":" + two(m) + ":" + two(sec) : m + ":" + two(sec);
  }

  function renderTime() { elTime.textContent = fmt(nowMs()); }

  function resume() {
    if (over || !started || runningSince !== null || document.hidden) return;
    runningSince = performance.now();
    clock = setInterval(renderTime, 1000);
  }

  function pause() {
    if (runningSince === null) return;
    elapsed += performance.now() - runningSince;
    runningSince = null;
    clearInterval(clock);
    renderTime();
  }

  function begin() { started = true; resume(); }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) { pause(); save(); } else { resume(); }
  });
  window.addEventListener("pagehide", function () { pause(); save(); });

  /* Sound ----------------------------------------------------------------- */
  /* Synthesised, so nothing to download and nothing to decode. The context
     is created on the first gesture: browsers refuse to make noise before
     one, and iOS refuses unless it happens inside the gesture's own handler. */

  var ctx = null;
  var master = null;
  var combo = 0;
  var lastHit = -1e9;   // not 0: that made an answer in the first 3.5s a "streak"
  var SCALE = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.66, 1318.51];

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

  function tone(freq, at, dur, type, gain) {
    var o = ctx.createOscillator();
    var g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, at);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(gain, at + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g);
    g.connect(master);
    o.start(at);
    o.stop(at + dur + 0.03);
  }

  /* The pitch climbs a pentatonic scale while answers keep coming and falls
     back after a few quiet seconds, so a streak sounds like one. */
  function chime(blockDone, everything) {
    if (!soundOn) return;
    try {
      unlock();
      if (!ctx || ctx.state !== "running") return;
      var t = ctx.currentTime + 0.005;
      var now = performance.now();
      combo = now - lastHit < 3500 ? combo + 1 : 0;
      lastHit = now;
      var f = SCALE[Math.min(combo, SCALE.length - 1)];
      tone(f, t, 0.17, "triangle", 0.9);
      tone(f * 2, t, 0.11, "sine", 0.22);
      if (everything) {
        [523.25, 659.25, 783.99, 1046.5, 1318.51, 1567.98].forEach(function (n, k) {
          tone(n, t + 0.12 + k * 0.09, 0.42, "triangle", 0.8);
        });
      } else if (blockDone) {
        [523.25, 659.25, 783.99, 1046.5].forEach(function (n, k) {
          tone(n, t + 0.16 + k * 0.075, 0.26, "triangle", 0.7);
        });
      }
    } catch (e) { /* the game must never break over a beep */ }
  }

  ["pointerdown", "keydown"].forEach(function (ev) {
    root.addEventListener(ev, unlock, { passive: true });
  });

  function renderSoundButton() {
    btnSound.setAttribute("aria-pressed", soundOn ? "true" : "false");
    btnSound.querySelector("[data-sound-state]").textContent = soundOn ? "on" : "off";
  }

  btnSound.addEventListener("click", function () {
    soundOn = !soundOn;
    renderSoundButton();
    if (soundOn) { unlock(); chime(false, false); }
    save();
  });

  /* Controls -------------------------------------------------------------- */

  btnNamedOnly.addEventListener("click", function () {
    var on = btnNamedOnly.getAttribute("aria-pressed") !== "true";
    btnNamedOnly.setAttribute("aria-pressed", on ? "true" : "false");
    list.classList.toggle("is-named-only", on);
  });

  /* Destructive buttons ask twice instead of using confirm(): a modal
     dialog is jarring in the middle of a streak. */
  function twoStep(btn, ask, run) {
    var label = btn.textContent;
    var timer = null;
    btn.addEventListener("click", function () {
      if (btn.dataset.armed) {
        clearTimeout(timer);
        delete btn.dataset.armed;
        btn.textContent = label;
        run();
        return;
      }
      btn.dataset.armed = "1";
      btn.textContent = ask;
      timer = setTimeout(function () {
        delete btn.dataset.armed;
        btn.textContent = label;
      }, 4000);
    });
  }

  twoStep(btnGiveUp, "Really give up?", function () { finish("gaveup"); });
  twoStep(btnReset, "Wipe it all?", reset);

  /* Ending ---------------------------------------------------------------- */

  function finish(how, quiet) {
    if (over) return;
    over = how;
    pause();
    input.disabled = true;
    input.value = "";
    input.placeholder = how === "done" ? "You named every one." : "Finished";

    if (how === "gaveup") {
      for (var i = 0; i < total; i++) {
        if (found[i]) continue;
        paint(i, false);
        rows[i].classList.remove("is-found");
        rows[i].classList.add("is-missed");
      }
    }

    $("[data-result-title]").textContent =
      how === "done" ? "All " + total.toLocaleString("en-US") + "." :
      foundCount.toLocaleString("en-US") + " of " + total.toLocaleString("en-US");
    $("[data-result-line]").textContent =
      how === "done" ? "Every extreme demon on the list, in " + fmt(nowMs()) + "."
                     : pctText() + " of the list, in " + fmt(nowMs()) + ".";
    result.hidden = false;
    /* Restoring a finished game on load must not yank the page down to it. */
    if (!quiet) {
      result.scrollIntoView({ block: "nearest" });
      announce("Finished. " + foundCount + " of " + total + " named in " + fmt(nowMs()) + ".");
    }
    save();
  }

  function reset() {
    pause();
    for (var i = 0; i < total; i++) {
      var li = rows[i];
      li.className = "slot";
      li.setAttribute("aria-hidden", "true");
      li.lastChild.textContent = "";
      found[i] = 0;
    }
    blocks.forEach(function (b) {
      b.found = 0;
      b.el.classList.remove("is-done");
      b.count.textContent = "0 / " + b.size;
    });
    foundCount = 0;
    over = null;
    elapsed = 0;
    started = false;
    combo = 0;
    lastIndex = -1;
    btnLast.hidden = true;
    result.hidden = true;
    input.disabled = false;
    input.placeholder = "Type a level name…";
    input.value = "";
    renderScore();
    renderTime();
    say("");
    write({ v: 1, found: [], ms: 0, over: null, sound: soundOn });
    input.focus();
  }

  $("[data-again]").addEventListener("click", reset);

  $("[data-copy]").addEventListener("click", function () {
    var note = $("[data-copied]");
    var text = "I named " + foundCount.toLocaleString("en-US") + "/" +
      total.toLocaleString("en-US") + " extreme demons in " + fmt(nowMs()) +
      " — " + location.href.split("#")[0];
    var done = function (msg) { note.textContent = msg; };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { done("Copied"); },
        function () { done("Couldn’t copy — select it by hand"); });
    } else {
      done("Couldn’t copy — select it by hand");
    }
  });

  /* Start ----------------------------------------------------------------- */

  (function restore() {
    (saved.found || []).forEach(function (id) {
      var i = idToIndex[id];
      if (i !== undefined && !found[i]) name(i, false);
    });
    elapsed = saved.ms || 0;
    started = foundCount > 0 || elapsed > 0;
    /* Saved in rank order, not in the order they were named, so there is no
       honest "last one" to show; name() just set it to the highest rank. */
    lastIndex = -1;
    btnLast.hidden = true;
    renderScore();
    renderTime();
    renderSoundButton();
    if (saved.over === "gaveup" || saved.over === "done" || foundCount === total) {
      finish(foundCount === total ? "done" : saved.over, true);
    }
  })();

  input.addEventListener("input", onInput);
  input.addEventListener("keydown", onKey);
  btnReset.disabled = false;

  if (!over) {
    input.disabled = false;
    /* Focusing on a phone throws the keyboard up over the list before the
       person has decided to play. */
    if (window.matchMedia && window.matchMedia("(pointer: fine)").matches) {
      input.focus();
    }
  }
})();
