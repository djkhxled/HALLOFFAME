/* The record boards' service -- a Cloudflare Worker with one KV namespace.
 *
 * This is the whole backend. It is deliberately small enough to read in one
 * sitting, because it is the only part of the site that stores anything about
 * a visitor and the privacy page has to be true of it.
 *
 *   GET  /boards   every board, best first
 *   POST /submit   { mode, name, score, t }        -> { ok, rank, improved, boards }
 *   POST /submit   { mode: "gg", name, score, named }   (GeometryGuessr)
 *
 * What it keeps: per board, one line per username -- the name, the score
 * (levels named, or GeometryGuessr points), how far into the run the last one
 * was named or how many of the five demons were named, and the date. Each
 * board keeps its best 100. Nothing else. In particular it does not read,
 * store or log the visitor's IP address, headers, or anything but the four
 * fields above, and it sets no cookies.
 *
 * What it does NOT do is stop anyone lying. The quiz runs in the visitor's
 * own browser and the answers are in the page, so any score can be faked and
 * the checks below only refuse the plainly impossible. That is a decision,
 * not an oversight: this is a board for friends.
 *
 * Binding: a KV namespace named RECORDS.
 * Optional variable: ALLOWED_ORIGINS, comma-separated, to replace the list
 * below.
 */

const MODES = { "5": 300, "10": 600, "30": 1800, "60": 3600 };   // seconds
const GG = { rounds: 5, perRound: 1000 };   // GeometryGuessr: five rounds, up to 1,000 each
const MAX_LEVELS = 2000;        // the list is ~1,621 and grows; this is a ceiling
const MAX_PER_SECOND = 2;       // a person types nothing like faster than this
const KEEP = 100;               // entries kept per board
const SHOW = 25;                // entries sent per board

const NAME_OK = /^[\p{L}\p{N}][\p{L}\p{N} _.\-]{1,19}$/u;

const DEFAULT_ORIGINS = [
  "https://www.b4ylor.com",
  "https://b4ylor.com",
  "https://djkhxled.github.io",
  "http://localhost:3003",
];

const clean = (s) => String(s).normalize("NFKC").replace(/\s+/g, " ").trim();
const idOf = (name) => name.toLowerCase();

/* More named wins; on a tie, the one who got there sooner. */
const better = (a, b) => a.s > b.s || (a.s === b.s && a.t < b.t);
const order = (a, b) =>
  b.s - a.s || a.t - b.t || (a.d < b.d ? -1 : a.d > b.d ? 1 : 0);

/* GeometryGuessr: more points wins; on a tie, more demons named, then whoever was first. */
const ggBetter = (a, b) => a.s > b.s || (a.s === b.s && a.r > b.r);
const ggOrder = (a, b) =>
  b.s - a.s || b.r - a.r || (a.d < b.d ? -1 : a.d > b.d ? 1 : 0);

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...headers,
    },
  });
}

function corsFor(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = env.ALLOWED_ORIGINS
    ? env.ALLOWED_ORIGINS.split(",").map((s) => s.trim())
    : DEFAULT_ORIGINS;
  const ok = allowed.includes(origin);
  return {
    ok,
    headers: ok
      ? { "Access-Control-Allow-Origin": origin, Vary: "Origin" }
      : { Vary: "Origin" },
  };
}

async function readBoard(env, mode) {
  const raw = await env.RECORDS.get("board:" + mode, "json");
  return Array.isArray(raw) ? raw : [];
}

async function allBoards(env, replace) {
  const out = {};
  for (const mode of Object.keys(MODES)) {
    const board = replace && replace.mode === mode ? replace.board : await readBoard(env, mode);
    out[mode] = board.slice(0, SHOW);
  }
  const gg = replace && replace.mode === "gg" ? replace.board : await readBoard(env, "gg");
  out.gg = gg.slice(0, SHOW);
  return out;
}

async function submit(request, env, cors) {
  // A browser on another site has no business posting here. This is a
  // courtesy to the page, not security: anyone can send any Origin header.
  if (!cors.ok) return json({ error: "Not allowed from here." }, 403, cors.headers);

  const text = await request.text();
  if (text.length > 1000) return json({ error: "That is too large." }, 413, cors.headers);
  let body;
  try { body = JSON.parse(text); } catch { return json({ error: "Unreadable request." }, 400, cors.headers); }
  if (!body || typeof body !== "object") return json({ error: "Unreadable request." }, 400, cors.headers);

  const mode = String(body.mode);
  if (mode !== "gg" && !Object.hasOwn(MODES, mode)) return json({ error: "Unknown mode." }, 400, cors.headers);

  const name = clean(body.name ?? "");
  if (!NAME_OK.test(name)) {
    return json({ error: "Usernames are 2–20 letters, numbers, spaces, dots, dashes or underscores." }, 400, cors.headers);
  }
  if (mode === "gg") return submitGG(env, cors, name, body);

  const { score, t } = body;
  if (!Number.isInteger(score) || score < 1 || score > MAX_LEVELS) {
    return json({ error: "That score isn’t possible." }, 400, cors.headers);
  }
  const limit = MODES[mode];
  if (!Number.isInteger(t) || t < 0 || t > limit * 1000 + 5000) {
    return json({ error: "That time isn’t possible." }, 400, cors.headers);
  }
  if (score > limit * MAX_PER_SECOND) {
    return json({ error: "That score isn’t possible in that time." }, 400, cors.headers);
  }

  const board = await readBoard(env, mode);
  const id = idOf(name);
  const entry = { n: name, s: score, t, d: new Date().toISOString().slice(0, 10) };
  const at = board.findIndex((e) => idOf(e.n) === id);

  let improved = true;
  if (at >= 0) {
    if (better(entry, board[at])) board[at] = entry;
    else improved = false;
  } else {
    board.push(entry);
  }
  board.sort(order);
  const kept = board.slice(0, KEEP);

  // Only write when something changed: KV's free tier counts writes.
  if (improved) await env.RECORDS.put("board:" + mode, JSON.stringify(kept));

  return json({
    ok: true,
    improved,
    rank: kept.findIndex((e) => idOf(e.n) === id) + 1,   // 0 if it fell off the bottom
    boards: await allBoards(env, { mode, board: kept }),
  }, 200, cors.headers);
}

/* GeometryGuessr's board. The same rules as the others: one line per username,
   the best 100 kept, nothing written unless something improved. */
async function submitGG(env, cors, name, body) {
  const { score, named } = body;
  if (!Number.isInteger(named) || named < 1 || named > GG.rounds) {
    return json({ error: "That isn’t possible." }, 400, cors.headers);
  }
  if (!Number.isInteger(score) || score < 0 || score > named * GG.perRound) {
    return json({ error: "That score isn’t possible." }, 400, cors.headers);
  }

  const board = await readBoard(env, "gg");
  const id = idOf(name);
  const entry = { n: name, s: score, r: named, d: new Date().toISOString().slice(0, 10) };
  const at = board.findIndex((e) => idOf(e.n) === id);

  let improved = true;
  if (at >= 0) {
    if (ggBetter(entry, board[at])) board[at] = entry;
    else improved = false;
  } else {
    board.push(entry);
  }
  board.sort(ggOrder);
  const kept = board.slice(0, KEEP);

  if (improved) await env.RECORDS.put("board:gg", JSON.stringify(kept));

  return json({
    ok: true,
    improved,
    rank: kept.findIndex((e) => idOf(e.n) === id) + 1,
    boards: await allBoards(env, { mode: "gg", board: kept }),
  }, 200, cors.headers);
}

async function route(request, env) {
  const cors = corsFor(request, env);
  const path = new URL(request.url).pathname.replace(/\/+$/, "") || "/";

  if (request.method === "OPTIONS") {
    if (!cors.ok) return new Response(null, { status: 204, headers: cors.headers });
    return new Response(null, {
      status: 204,
      headers: {
        ...cors.headers,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Max-Age": "86400",
      },
    });
  }

  if (!env.RECORDS) return json({ error: "Records storage is not connected." }, 500, cors.headers);

  if (request.method === "GET" && path === "/boards") {
    return json(await allBoards(env), 200, cors.headers);
  }
  if (request.method === "POST" && path === "/submit") return submit(request, env, cors);
  if (request.method === "GET" && path === "/") {
    return json({ service: "hall-of-extremes records" }, 200, cors.headers);
  }
  return json({ error: "Not found." }, 404, cors.headers);
}

export default {
  async fetch(request, env) {
    try {
      return await route(request, env);
    } catch (err) {
      // Deliberately not logged: nothing about the request is kept.
      return json({ error: "Something went wrong." }, 500, {});
    }
  },
};
