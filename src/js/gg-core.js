/* gg-core.js — the rules of GeometryGuessr, and nothing else.
 *
 * No DOM, no storage, no network, no clock. Randomness comes in as a function so the
 * checks in tests/gg.check.html can replay it. gg.js draws; this decides.
 *
 * A game: five rounds, five different demons, like GeoGuessr. Each round deals a
 * screenshot; name the level (a wrong name scores nothing that round) and, if right,
 * place the spot (0-100%) for up to 1,000 points. A perfect game is 5,000.
 */
(function (root) {
  "use strict";

  var ROUNDS = 5;
  var FULL = 1000;      // points for a spot within GRACE of the truth
  var GRACE = 2;        // percentage points
  var ZERO_AT = 30;     // this far off (or further) scores nothing

  /* Points for a spot guess: full within 2 points, falling in a straight line to
     nothing at 30 points away. */
  function score(guess, truth) {
    var off = Math.abs(guess - truth);
    var k = 1 - Math.max(0, off - GRACE) / (ZERO_AT - GRACE);
    return Math.round(FULL * Math.max(0, k));
  }

  /* A word for how close a spot was, for the reveal. */
  function verdict(off) {
    if (off <= GRACE) return "perfect";
    if (off <= 6) return "great";
    if (off <= 12) return "good";
    if (off <= 20) return "close";
    return "far";
  }

  /* A seeded generator (mulberry32), for the checks and anything that wants a replay. */
  function seeded(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function shuffle(list, rand) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(rand() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /* The shots for one game: n different levels, chosen at random, one shot of each.
     Levels in `avoid` (the last game's) are used only if there are not enough others. */
  function pick(shots, rand, n, avoid) {
    var byLevel = {}, levels = [];
    shots.forEach(function (s, i) {
      if (!byLevel[s.l]) { byLevel[s.l] = []; levels.push(s.l); }
      byLevel[s.l].push(i);
    });
    var skip = {};
    (avoid || []).forEach(function (l) { skip[l] = true; });
    var fresh = shuffle(levels.filter(function (l) { return !skip[l]; }), rand);
    var stale = shuffle(levels.filter(function (l) { return skip[l]; }), rand);
    return fresh.concat(stale).slice(0, n).map(function (l) {
      var mine = byLevel[l];
      return mine[Math.floor(rand() * mine.length)];
    });
  }

  /* Names compared without case, accents, spaces or punctuation. */
  function norm(s) {
    return String(s).normalize("NFKD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]/g, "");
  }

  /* Levels whose name contains the query; names that start with it first, then the
     most downloaded. */
  function search(levels, query, limit) {
    var q = norm(query);
    if (!q) return [];
    var hits = [];
    for (var i = 0; i < levels.length; i++) {
      var n = norm(levels[i].n);
      var at = n.indexOf(q);
      if (at >= 0) hits.push({ lv: levels[i], first: at === 0, exact: n === q });
    }
    hits.sort(function (a, b) {
      return (b.exact - a.exact) || (b.first - a.first) || (b.lv.d - a.lv.d);
    });
    return hits.slice(0, limit || 8).map(function (h) { return h.lv; });
  }

  /* The run, as plain data. Each step returns a new state. */
  function newRun() {
    return { named: 0, score: 0, round: 0, history: [], over: false };
  }

  /* All five named (whatever the spots scored). */
  function complete(run) { return run.over && run.named === ROUNDS; }

  function nameLevel(run, shot, pickedId) {
    var right = pickedId === shot.l;
    var next = copy(run);
    next.round += 1;
    next.history.push({ shot: shot, picked: pickedId, right: right, spot: null, points: 0 });
    if (right) next.named += 1;
    else if (next.round >= ROUNDS) next.over = true;   // a right name ends after its spot
    return next;
  }

  function placeSpot(run, spot) {
    var next = copy(run);
    var last = next.history[next.history.length - 1];
    if (!last || !last.right || last.spot !== null) return run;
    last.spot = spot;
    last.points = score(spot, last.shot.p);
    next.score += last.points;
    if (next.round >= ROUNDS) next.over = true;
    return next;
  }

  function copy(run) {
    return {
      named: run.named, score: run.score, round: run.round, over: run.over,
      history: run.history.map(function (h) {
        return { shot: h.shot, picked: h.picked, right: h.right, spot: h.spot, points: h.points };
      })
    };
  }

  /* A game is "better" by score, then by levels named. */
  function better(a, b) {
    if (!b) return true;
    return a.score > b.score || (a.score === b.score && a.named > b.named);
  }

  root.GGCore = {
    ROUNDS: ROUNDS, FULL: FULL, GRACE: GRACE, ZERO_AT: ZERO_AT,
    score: score, verdict: verdict, seeded: seeded, pick: pick, norm: norm, search: search,
    newRun: newRun, nameLevel: nameLevel, placeSpot: placeSpot, complete: complete, better: better
  };
}(this));
