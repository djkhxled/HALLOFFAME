/* guess.js — the interface for Guess the Demon.
 *
 * Rules live in guess-core.js and are checked in tests/guess.check.html.
 * This file does the DOM and nothing else decides anything. No network of any
 * kind: the data is in the page and progress is kept in localStorage.
 */
(function () {
  "use strict";

  var G = window.GuessCore;
  var root = document.querySelector("[data-guess]");
  var dataEl = document.getElementById("guess-data");
  if (!G || !root || !dataEl) return;

  var data = JSON.parse(dataEl.textContent);
  var levels = data.levels;
  var byId = {};
  levels.forEach(function (l) { byId[l.id] = l; });
  var poolIds = levels.map(function (l) { return l.id; });

  function $(sel) { return root.querySelector(sel); }
  var input = $("[data-input]"), optionsEl = $("[data-options]"), board = $("[data-board]");
  var statusEl = $("[data-status]"), liveEl = $("[data-live]");
  var result = $("[data-result]"), resTitle = $("[data-result-title]"), resLine = $("[data-result-line]");
  var resLink = $("[data-result-link]"), btnShare = $("[data-share]"), btnNext = $("[data-next]");
  var copied = $("[data-copied]"), countRow = $("[data-countdown-row]"), countEl = $("[data-countdown]");
  var btnSound = $("[data-sound]"), soundState = $("[data-sound-state]");
  var modeRadios = root.querySelectorAll('input[name="mode"]');
  var statsDaily = $("[data-stats-daily]"), statsInf = $("[data-stats-infinite]");

  var KEY = "hall-of-extremes.guess.v1";
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function motion(el, frames, opts) { if (calm || !el || !el.animate) return; el.animate(frames, opts); }
  function norm(s) {
    return s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  /* State ----------------------------------------------------------------- */

  var state;
  function load() {
    try { state = G.normalizeState(JSON.parse(localStorage.getItem(KEY))); }
    catch (e) { state = G.emptyState(); }
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* works without */ } }

  function today() { return G.isoDate(new Date()); }
  function todayNum() { return G.dayNumber(data.launch, today()); }

  function rollDaily() {
    var n = todayNum();
    if (state.daily.day !== n || !state.daily.round) {
      state.daily = { day: n, round: G.newRound(G.dailyAnswerId(data, today())) };
    }
  }
  function ensureInfinite() {
    var r = state.infinite.round;
    if (!r || !byId[r.answer]) {
      var p = G.pickInfinite(poolIds, state.infinite.seen, Math.random);
      state.infinite.seen = p.seen;
      state.infinite.round = G.newRound(p.id);
    }
  }
  function round() { return state.mode === "daily" ? state.daily.round : state.infinite.round; }
  function answer() { return byId[round().answer]; }

  /* Sound ------------------------------------------------------------------ */

  var ctx = null, master = null;
  function unlock() {
    try {
      if (!ctx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        ctx = new AC();
        master = ctx.createGain();
        master.gain.value = 0.14;
        master.connect(ctx.destination);
      }
      if (ctx.state === "suspended") ctx.resume();
    } catch (e) { ctx = null; }
  }
  function tone(freq, at, dur, type, gain) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, at);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(gain, at + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g); g.connect(master); o.start(at); o.stop(at + dur + 0.03);
  }
  function play(fn) {
    if (!state.sound) return;
    try { unlock(); if (ctx && ctx.state === "running") fn(ctx.currentTime + 0.005); } catch (e) { /* never break over a beep */ }
  }
  function tick(t) { tone(660, t, 0.08, "triangle", 0.5); }
  function winChime(t) { [523.25, 659.25, 783.99, 1046.5].forEach(function (n, k) { tone(n, t + k * 0.09, 0.3, "triangle", 0.7); }); }
  function lossBuzz(t) { tone(392, t, 0.22, "triangle", 0.5); tone(311, t + 0.2, 0.3, "triangle", 0.5); }

  /* Board ------------------------------------------------------------------ */

  var HEAD = { rank: "Rank", year: "Verified", version: "Version", seconds: "Length", creators: "Creators" };
  var GLYPH = { exact: "✓", close: "~", miss: "✗" };
  var WORD = { exact: "exact", close: "close", miss: "not close" };
  var ARROW = { up: "▲", down: "▼", none: "" };
  // What each arrow means, per stat. Rank is read like a leaderboard: up is toward #1.
  var ARROWWORD = {
    rank: { up: "the answer is higher on the list", down: "the answer is lower on the list" },
    year: { up: "the answer was verified later", down: "the answer was verified earlier" },
    version: { up: "the answer is from a newer version", down: "the answer is from an older version" },
    seconds: { up: "the answer is longer", down: "the answer is shorter" },
    creators: { up: "the answer has more creators", down: "the answer has fewer creators" },
  };
  var tipSeq = 0;

  function cellValue(key, lv) {
    if (key === "rank") return "#" + lv.r;
    if (key === "year") return String(lv.y);
    if (key === "version") return lv.v;
    if (key === "seconds") return G.fmtTime(lv.s);
    return String(lv.c);
  }

  function buildCell(key, lv, verdict) {
    var li = el("li", "gcell gcell--" + verdict.state);
    li.setAttribute("data-stat", key);
    li.appendChild(el("span", "gcell__head", HEAD[key]));
    var v = el("span", "gcell__v");
    if (key === "creators") {
      var id = "gtip" + (++tipSeq);
      var b = el("button", "credit");
      b.type = "button";
      b.setAttribute("aria-describedby", id);
      b.appendChild(el("span", "credit__lead", cellValue(key, lv)));
      var tip = el("span", "credit__all");
      tip.id = id; tip.setAttribute("role", "tooltip");
      tip.appendChild(el("span", "credit__head", "All " + lv.c + " credited"));
      tip.appendChild(document.createTextNode(lv.cn.join(", ")));
      b.appendChild(tip);
      v.appendChild(b);
    } else {
      v.textContent = cellValue(key, lv);
    }
    li.appendChild(v);
    li.appendChild(el("span", "gcell__g", GLYPH[verdict.state] + " " + ARROW[verdict.arrow]));
    li.appendChild(el("span", "visually-hidden",
      HEAD[key] + " " + cellValue(key, lv) + ": " + WORD[verdict.state] +
      (verdict.arrow !== "none" ? ", " + ARROWWORD[key][verdict.arrow] : "")));
    return li;
  }

  function buildRow(lv, res) {
    var row = el("li", "grow");
    var name = el("div", "grow__name");
    name.appendChild(document.createTextNode(lv.n));
    name.appendChild(el("span", "grow__rank", "#" + lv.r));
    row.appendChild(name);
    G.STATS.forEach(function (k) { row.appendChild(buildCell(k, lv, res[k])); });
    return row;
  }

  function emptyRow() {
    var row = el("li", "grow grow--empty");
    row.appendChild(el("div", "grow__name"));
    for (var i = 0; i < 5; i++) row.appendChild(el("span", "gcell"));
    return row;
  }

  function renderBoard(animateLast) {
    var r = round(), a = answer();
    board.textContent = "";
    r.guesses.forEach(function (id, i) {
      var lv = byId[id];
      if (!lv) return;
      var row = buildRow(lv, G.judge(lv, a));
      board.appendChild(row);
      if (animateLast && i === r.guesses.length - 1) {
        Array.prototype.forEach.call(row.querySelectorAll(".gcell"), function (c, k) {
          motion(c, [{ transform: "rotateX(90deg)", opacity: 0 }, { transform: "none", opacity: 1 }],
                 { duration: 380, delay: k * 120, fill: "backwards", easing: "ease-out" });
        });
      }
    });
    for (var i = r.guesses.length; i < G.MAX_GUESSES; i++) board.appendChild(emptyRow());
  }

  /* Result, stats ----------------------------------------------------------- */

  function shareResults() {
    var a = answer();
    return round().guesses.map(function (id) { return G.judge(byId[id], a); });
  }

  function renderResult() {
    var r = round(), a = answer();
    if (!r.done) { result.hidden = true; countRow.hidden = true; return; }
    result.hidden = false;
    resTitle.textContent = r.won ? "Got it in " + r.guesses.length + " of " + G.MAX_GUESSES : "It was " + a.n;
    resLine.textContent = a.n + " — #" + a.r + " on the Demonlist, verified " + a.y + ", " + a.v + ", " +
      G.fmtTime(a.s) + ", " + a.c + (a.c === 1 ? " creator." : " creators.");
    var slug = data.hall[String(a.id)];
    resLink.hidden = !slug;
    resLink.textContent = "";
    if (slug) {
      resLink.appendChild(document.createTextNode("It is one of the Hall’s own: "));
      var link = el("a", "", "read the page on " + a.n);
      link.href = "/levels/" + slug + "/";
      resLink.appendChild(link);
      resLink.appendChild(document.createTextNode("."));
    }
    btnNext.hidden = state.mode !== "infinite";
    countRow.hidden = state.mode !== "daily";
  }

  function statBlock(title, s, mode) {
    var wrap = el("div", "gstat");
    wrap.appendChild(el("h3", "", title));
    var dl = el("dl");
    function pair(label, value) { var d = el("div"); d.appendChild(el("dt", "", label)); d.appendChild(el("dd", "", String(value))); dl.appendChild(d); }
    pair("Played", s.played);
    pair("Win %", s.played ? Math.round(100 * s.won / s.played) : 0);
    if (mode === "daily") { pair("Streak", G.currentStreak(state.stats, todayNum())); pair("Best", s.best); }
    wrap.appendChild(dl);
    var max = Math.max.apply(null, s.dist.concat([1]));
    var ul = el("ul", "gdist");
    ul.setAttribute("aria-label", "Wins by number of guesses");
    s.dist.forEach(function (n, i) {
      var li = el("li");
      li.appendChild(el("span", "", String(i + 1)));
      var bar = el("span", "gdist__bar" + (n ? " gdist__bar--won" : ""), String(n));
      bar.style.width = Math.max(8, Math.round(100 * n / max)) + "%";
      li.appendChild(bar);
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
    return wrap;
  }

  function renderStats() {
    statsDaily.textContent = ""; statsInf.textContent = "";
    statsDaily.appendChild(statBlock("Daily", state.stats.daily, "daily"));
    statsInf.appendChild(statBlock("Infinite", state.stats.infinite, "infinite"));
  }

  /* Combobox ----------------------------------------------------------------- */

  var shown = [], active = -1;

  function matches(q) {
    var n = norm(q);
    if (!n) return [];
    var guessed = round().guesses;
    return levels.filter(function (l) { return guessed.indexOf(l.id) < 0 && norm(l.n).indexOf(n) >= 0; })
      .sort(function (a, b) {
        var sa = norm(a.n).indexOf(n) === 0 ? 0 : 1, sb = norm(b.n).indexOf(n) === 0 ? 0 : 1;
        return sa - sb || a.r - b.r;
      }).slice(0, 8);
  }

  function alreadyGuessed(q) {
    var n = norm(q);
    return !!n && round().guesses.some(function (id) { return byId[id] && norm(byId[id].n).indexOf(n) >= 0; });
  }

  function closeOptions() {
    optionsEl.hidden = true; optionsEl.textContent = "";
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    shown = []; active = -1;
  }

  function setActive(i) {
    active = i;
    Array.prototype.forEach.call(optionsEl.children, function (li, k) {
      li.setAttribute("aria-selected", k === i ? "true" : "false");
    });
    if (i >= 0) input.setAttribute("aria-activedescendant", optionsEl.children[i].id);
    else input.removeAttribute("aria-activedescendant");
  }

  function openOptions() {
    shown = matches(input.value);
    optionsEl.textContent = "";
    if (!shown.length) { closeOptions(); return; }
    shown.forEach(function (l, i) {
      var li = el("li", "goption");
      li.id = "gopt" + i; li.setAttribute("role", "option"); li.setAttribute("aria-selected", "false");
      li.appendChild(el("span", "", l.n));
      li.appendChild(el("span", "goption__rank", "#" + l.r));
      li.addEventListener("mousedown", function (e) { e.preventDefault(); submit(l); });
      optionsEl.appendChild(li);
    });
    optionsEl.hidden = false;
    input.setAttribute("aria-expanded", "true");
    setActive(0);
  }

  function announce(text) { liveEl.textContent = ""; setTimeout(function () { liveEl.textContent = text; }, 30); }

  function submit(lv) {
    if (round().done) return;
    unlock();
    var out = G.addGuess(round(), lv, answer());
    if (out.error) { statusEl.textContent = out.error === "duplicate" ? "You already guessed that one." : ""; return; }
    if (state.mode === "daily") state.daily.round = out.round; else state.infinite.round = out.round;
    input.value = ""; closeOptions(); statusEl.textContent = "";
    play(tick);
    var r = out.round;
    if (r.done) {
      state.stats = G.recordResult(state.stats, state.mode, r.won, r.guesses.length, todayNum());
      play(function (t) { if (r.won) winChime(t + 0.5); else lossBuzz(t + 0.5); });
    }
    save();
    renderBoard(true);
    announce("Guess " + r.guesses.length + " of " + G.MAX_GUESSES + ": " + lv.n + ". " +
      G.STATS.map(function (k) { return HEAD[k] + " " + WORD[out.result[k].state]; }).join(", ") + ".");
    // Show the verdict when the last cell has flipped, so it is not spoilt mid-reveal.
    var delay = calm ? 0 : 5 * 120 + 380;
    setTimeout(function () { renderResult(); renderStats(); setInputState(); }, delay);
    if (!r.done) input.focus();
  }

  function setInputState() {
    var done = round().done;
    input.disabled = done;
    input.placeholder = done ? "Round over" : "Start typing a level name…";
  }

  input.addEventListener("input", openOptions);
  input.addEventListener("focus", function () { if (input.value) openOptions(); });
  input.addEventListener("blur", function () { setTimeout(closeOptions, 120); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") { e.preventDefault(); if (!shown.length) openOptions(); else setActive((active + 1) % shown.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); if (shown.length) setActive((active - 1 + shown.length) % shown.length); }
    else if (e.key === "Escape") { closeOptions(); }
    else if (e.key === "Enter") {
      e.preventDefault();
      var pick = shown[active >= 0 ? active : 0] || matches(input.value)[0];
      if (pick) submit(pick);
      else statusEl.textContent = alreadyGuessed(input.value) ? "You already guessed that one." : "Pick a level from the list.";
    }
  });
  root.querySelector("[data-form]").addEventListener("submit", function (e) { e.preventDefault(); });

  /* Controls ----------------------------------------------------------------- */

  function show(animate) {
    if (state.mode === "daily") rollDaily(); else ensureInfinite();
    Array.prototype.forEach.call(modeRadios, function (r) { r.checked = r.value === state.mode; });
    renderBoard(false); renderResult(); renderStats(); setInputState();
    copied.textContent = ""; statusEl.textContent = ""; closeOptions();
    save();
  }

  Array.prototype.forEach.call(modeRadios, function (r) {
    r.addEventListener("change", function () { if (r.checked) { state.mode = r.value; show(); } });
  });

  btnNext.addEventListener("click", function () {
    var p = G.pickInfinite(poolIds, state.infinite.seen, Math.random);
    state.infinite.seen = p.seen;
    state.infinite.round = G.newRound(p.id);
    show(); input.focus();
  });

  btnShare.addEventListener("click", function () {
    var text = G.shareText({ mode: state.mode, n: todayNum(), won: round().won, guesses: shareResults() });
    function done(msg) { copied.textContent = msg; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done("Copied."); }, function () { done("Couldn’t copy — select and copy by hand."); });
    } else { done("Couldn’t copy — select and copy by hand."); }
  });

  function paintSound() { btnSound.setAttribute("aria-pressed", String(state.sound)); soundState.textContent = state.sound ? "on" : "off"; }
  btnSound.addEventListener("click", function () { state.sound = !state.sound; paintSound(); save(); if (state.sound) unlock(); });

  /* Countdown to the next daily (local midnight) ----------------------------- */
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  setInterval(function () {
    if (countRow.hidden) return;
    var now = new Date(), next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
    var s = Math.max(0, Math.floor((next - now) / 1000));
    countEl.textContent = pad(Math.floor(s / 3600)) + ":" + pad(Math.floor(s / 60) % 60) + ":" + pad(s % 60);
    if (s === 0 && state.mode === "daily") location.reload();
  }, 1000);

  load();
  paintSound();
  show();
})();
