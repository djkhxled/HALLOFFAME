/* guess-core.js — the rules of Guess the Demon, with no DOM and no network.
 *
 * Everything the game decides lives here so it can be checked on its own
 * (tests/guess.check.html). guess.js is only the interface on top.
 *
 * Level objects: { id, n, r, p, y, v, s, c, cn } = level id, name, rank, peak
 * rank, year, version, seconds, creator count, creator names (see hall/guess.py
 * data_json).
 */
(function (root) {
  "use strict";

  var VERSIONS = ["1.8", "1.9PS", "2.0", "2.1", "2.2"];   // must equal hall/guess.py
  var MAX_GUESSES = 6;
  var STATS = ["rank", "peak", "year", "version", "seconds", "creators"];

  // Arrows point toward the answer. For year, version, length and creators "up"
  // means a bigger number. Rank is read the other way, as a leaderboard is: "up"
  // means higher on the list, nearer #1, which is a SMALLER number.
  function arrow(g, a) { return g < a ? "up" : g > a ? "down" : "none"; }

  function grade(g, a, band, flip) {
    var d = Math.abs(a - g);
    return { state: d === 0 ? "exact" : d <= band ? "close" : "miss", arrow: flip ? arrow(a, g) : arrow(g, a) };
  }

  function judge(guess, answer) {
    return {
      rank: grade(guess.r, answer.r, 10, true),
      peak: grade(guess.p, answer.p, 5, true),   // best position ever held; read like Rank
      year: grade(guess.y, answer.y, 1),
      version: grade(VERSIONS.indexOf(guess.v), VERSIONS.indexOf(answer.v), 1),
      seconds: grade(guess.s, answer.s, 30),
      creators: grade(guess.c, answer.c, Math.max(2, Math.round(0.2 * answer.c))),
    };
  }

  function isWin(result) {
    return STATS.every(function (k) { return result[k].state === "exact"; });
  }

  function fmtTime(s) {
    return s < 60 ? s + "s" : Math.floor(s / 60) + "m " + (s % 60) + "s";
  }

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function isoDate(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }

  function dayNumber(launch, iso) {
    var a = launch.split("-"), b = iso.split("-");
    var da = Date.UTC(+a[0], +a[1] - 1, +a[2]), db = Date.UTC(+b[0], +b[1] - 1, +b[2]);
    return Math.round((db - da) / 86400000) + 1;
  }

  function hashString(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }

  function dailyAnswerId(data, iso) {
    var i = dayNumber(data.launch, iso) - 1;
    if (i >= 0 && i < data.sched.length) return data.sched[i];
    var pool = data.levels.map(function (l) { return l.id; });
    return pool[hashString(iso) % pool.length];   // schedule ran out: never break
  }

  function pickInfinite(pool, seen, rnd) {
    var left = pool.filter(function (id) { return seen.indexOf(id) < 0; });
    if (!left.length) { seen = []; left = pool.slice(); }
    var id = left[Math.min(left.length - 1, Math.floor(rnd() * left.length))];
    return { id: id, seen: seen.concat([id]) };
  }

  function newRound(answerId) { return { answer: answerId, guesses: [], done: false, won: false }; }

  function addGuess(round, guess, answer) {
    if (round.done) return { round: round, result: null, error: "finished" };
    if (round.guesses.indexOf(guess.id) >= 0) return { round: round, result: null, error: "duplicate" };
    var result = judge(guess, answer);
    var won = guess.id === answer.id;   // the level itself, not just matching stats
    var guesses = round.guesses.concat([guess.id]);
    return {
      round: { answer: round.answer, guesses: guesses, won: won, done: won || guesses.length >= MAX_GUESSES },
      result: result,
      error: null,
    };
  }

  function zeros() { return [0, 0, 0, 0, 0, 0]; }

  function emptyStats() {
    return {
      daily: { played: 0, won: 0, streak: 0, best: 0, lastDay: 0, dist: zeros() },
      infinite: { played: 0, won: 0, dist: zeros() },
    };
  }

  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  function recordResult(stats, mode, won, guessCount, dayNum) {
    var s = clone(stats), m = s[mode];
    m.played++;
    if (won) { m.won++; m.dist[guessCount - 1]++; }
    if (mode === "daily") {
      if (won) m.streak = (m.lastDay === dayNum - 1 && m.streak > 0) ? m.streak + 1 : 1;
      else m.streak = 0;
      m.best = Math.max(m.best, m.streak);
      m.lastDay = dayNum;
    }
    return s;
  }

  function currentStreak(stats, todayNum) {
    var d = stats.daily;
    return d.lastDay >= todayNum - 1 ? d.streak : 0;
  }

  var EMOJI = { exact: "🟩", close: "🟨", miss: "⬛" };

  function shareText(o) {
    var score = (o.won ? o.guesses.length : "X") + "/" + MAX_GUESSES;
    var head = "Hall of Extremes — Guess the Demon " +
      (o.mode === "daily" ? "#" + o.n : "(infinite)") + " · " + score;
    var rows = o.guesses.map(function (r) {
      return STATS.map(function (k) { return EMOJI[r[k].state]; }).join("");
    });
    return [head].concat(rows).join("\n");
  }

  function validRound(r) {
    return r && typeof r.answer === "number" && Array.isArray(r.guesses) &&
      r.guesses.length <= MAX_GUESSES &&
      { answer: r.answer, guesses: r.guesses.filter(Number.isFinite), done: !!r.done, won: !!r.won };
  }

  function validStats(s) {
    var out = emptyStats();
    ["daily", "infinite"].forEach(function (mode) {
      var from = s && s[mode];
      if (!from) return;
      Object.keys(out[mode]).forEach(function (k) {
        if (k === "dist") {
          if (Array.isArray(from.dist) && from.dist.length === 6 && from.dist.every(Number.isFinite)) out[mode].dist = from.dist;
        } else if (Number.isFinite(from[k])) out[mode][k] = from[k];
      });
    });
    return out;
  }

  function emptyState() {
    return { v: 1, sound: true, mode: "daily", daily: { day: null, round: null },
             infinite: { round: null, seen: [] }, stats: emptyStats() };
  }

  function normalizeState(raw) {
    var s = emptyState();
    if (!raw || typeof raw !== "object") return s;
    if (raw.mode === "daily" || raw.mode === "infinite") s.mode = raw.mode;
    if (typeof raw.sound === "boolean") s.sound = raw.sound;
    if (raw.daily && Number.isFinite(raw.daily.day)) { s.daily.day = raw.daily.day; s.daily.round = validRound(raw.daily.round) || null; }
    if (raw.infinite) {
      if (Array.isArray(raw.infinite.seen)) s.infinite.seen = raw.infinite.seen.filter(Number.isFinite);
      s.infinite.round = validRound(raw.infinite.round) || null;
    }
    s.stats = validStats(raw.stats);
    return s;
  }

  var api = {
    VERSIONS: VERSIONS, MAX_GUESSES: MAX_GUESSES, STATS: STATS, judge: judge, isWin: isWin,
    fmtTime: fmtTime, isoDate: isoDate, dayNumber: dayNumber, dailyAnswerId: dailyAnswerId,
    pickInfinite: pickInfinite, newRound: newRound, addGuess: addGuess, emptyStats: emptyStats,
    recordResult: recordResult, currentStreak: currentStreak, shareText: shareText,
    emptyState: emptyState, normalizeState: normalizeState,
  };
  root.GuessCore = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : this);
