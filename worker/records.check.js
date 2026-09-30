/* Behaviour checks for records.js, run in a browser against a stand-in for KV.
 *
 * There is no Node on this project, so these cannot run under `unittest`; the
 * browser is the JavaScript engine that is always to hand. Serve this folder
 * and open check.html:
 *
 *     python3 -m http.server 3010 --directory worker
 *     open http://127.0.0.1:3010/check.html
 *
 * The page title becomes PASS or FAIL and the list below it says which.
 *
 * The stand-in for the Request is only what the service reads -- method, url,
 * headers.get and text() -- because a browser will not let a script set an
 * Origin header on a real one.
 */

export async function run(worker) {
  const ORIGIN = "https://www.b4ylor.com";
  const results = {};
  const ok = (name, cond, detail) =>
    (results[name] = cond ? "pass" : "FAIL " + JSON.stringify(detail));

  function makeEnv(extra) {
    const store = new Map();
    const env = { writes: 0, store, ...extra };
    env.RECORDS = {
      async get(k, type) {
        const v = store.get(k);
        return v === undefined ? null : type === "json" ? JSON.parse(v) : v;
      },
      async put(k, v) { env.writes++; store.set(k, v); },
    };
    return env;
  }

  const fake = (method, path, body, origin) => ({
    method,
    url: "https://x.workers.dev" + path,
    headers: { get: (h) => (h.toLowerCase() === "origin" ? origin || null : null) },
    text: async () => (body === undefined ? "" : typeof body === "string" ? body : JSON.stringify(body)),
  });

  const call = async (env, method, path, body, origin = ORIGIN) => {
    const res = await worker.fetch(fake(method, path, body, origin), env);
    return { status: res.status, body: await res.json().catch(() => null), cors: res.headers.get("Access-Control-Allow-Origin"), res };
  };

  const env = makeEnv();
  let r = await call(env, "POST", "/submit", { mode: "10", name: "bperk", score: 143, t: 590000 });
  ok("accepts a good score", r.status === 200 && r.body.ok && r.body.rank === 1 && r.body.improved, r.body);
  ok("returns all four boards", Object.keys(r.body.boards || {}).join() === "5,10,30,60", r.body);
  ok("sets CORS for the site", r.cors === ORIGIN, r.cors);

  await call(env, "POST", "/submit", { mode: "10", name: "alex", score: 200, t: 600000 });
  await call(env, "POST", "/submit", { mode: "10", name: "sam", score: 143, t: 400000 });
  r = await call(env, "GET", "/boards");
  const b10 = r.body["10"].map((e) => e.n + ":" + e.s);
  ok("higher score first, ties by who got there sooner", b10.join() === "alex:200,sam:143,bperk:143", b10);

  r = await call(env, "POST", "/submit", { mode: "10", name: "BPERK", score: 99, t: 1000 });
  ok("a worse score does not replace a better one", r.body.improved === false && r.body.rank === 3, r.body);
  const w0 = env.writes;
  await call(env, "POST", "/submit", { mode: "10", name: "bperk", score: 99, t: 1000 });
  ok("a non-improvement costs no KV write", env.writes === w0, env.writes - w0);
  r = await call(env, "POST", "/submit", { mode: "10", name: "BPerk", score: 150, t: 500000 });
  const mine = (await call(env, "GET", "/boards")).body["10"].filter((e) => e.n.toLowerCase() === "bperk");
  ok("a better score replaces it, still one line", r.body.improved && mine.length === 1 && mine[0].s === 150 && mine[0].n === "BPerk", mine);

  r = await call(env, "POST", "/submit", { mode: "5", name: "bperk", score: 50, t: 290000 });
  ok("modes are separate boards", r.body.boards["5"].length === 1 && r.body.boards["10"].length === 3, r.body.boards);

  const bad = async (label, body, status, origin) => {
    const x = await call(env, "POST", "/submit", body, origin);
    ok(label, x.status === status && !x.body.ok, [x.status, x.body]);
  };
  await bad("rejects an unknown mode", { mode: "7", name: "abc", score: 5, t: 1 }, 400);
  await bad("rejects a prototype-key mode", { mode: "constructor", name: "abc", score: 5, t: 1 }, 400);
  await bad("rejects __proto__ as a mode", { mode: "__proto__", name: "abc", score: 5, t: 1 }, 400);
  await bad("rejects a 1-character name", { mode: "5", name: "a", score: 5, t: 1 }, 400);
  await bad("rejects a 21-character name", { mode: "5", name: "a".repeat(21), score: 5, t: 1 }, 400);
  await bad("rejects markup in a name", { mode: "5", name: "<script>alert(1)", score: 5, t: 1 }, 400);
  await bad("rejects a zero score", { mode: "5", name: "abc", score: 0, t: 1 }, 400);
  await bad("rejects a fractional score", { mode: "5", name: "abc", score: 5.5, t: 1 }, 400);
  await bad("rejects a string score", { mode: "5", name: "abc", score: "5", t: 1 }, 400);
  await bad("rejects more than the list holds", { mode: "60", name: "abc", score: 2001, t: 1 }, 400);
  await bad("rejects faster than a person can type", { mode: "5", name: "abc", score: 601, t: 1 }, 400);
  await bad("rejects a time past the limit", { mode: "5", name: "abc", score: 5, t: 400000 }, 400);
  await bad("rejects a negative time", { mode: "5", name: "abc", score: 5, t: -1 }, 400);
  await bad("rejects garbage JSON", "{not json", 400);
  await bad("rejects a body that is not an object", "null", 400);
  await bad("rejects an oversized body", "x".repeat(1200), 413);
  await bad("rejects another site", { mode: "5", name: "abc", score: 5, t: 1 }, 403, "https://evil.example");
  await bad("rejects no origin at all", { mode: "5", name: "abc", score: 5, t: 1 }, 403, "");

  // Whitespace is normalised rather than refused, so no control character is ever stored.
  r = await call(env, "POST", "/submit", { mode: "30", name: "ab\ncd", score: 10, t: 5000 });
  ok("turns a newline into a space and never stores one", r.body.boards["30"][0].n === "ab cd", r.body.boards["30"]);
  r = await call(env, "POST", "/submit", { mode: "30", name: "  Mr   Nobody  ", score: 9, t: 5000 });
  ok("collapses whitespace in a name", r.body.boards["30"].some((e) => e.n === "Mr Nobody"), r.body.boards["30"]);
  r = await call(env, "POST", "/submit", { mode: "30", name: "Zoë_山", score: 11, t: 5000 });
  ok("accepts letters from other alphabets", r.status === 200, r.body);

  const big = makeEnv();
  for (let i = 0; i < 105; i++) await call(big, "POST", "/submit", { mode: "60", name: "player" + i, score: 1 + i, t: 1000 });
  const kept = JSON.parse(big.store.get("board:60"));
  ok("keeps only the best 100", kept.length === 100 && kept[0].s === 105 && kept[99].s === 6, [kept.length, kept[0].s, kept[99].s]);
  r = await call(big, "POST", "/submit", { mode: "60", name: "lowest", score: 1, t: 1000 });
  ok("a score that misses the cut reports rank 0", r.body.ok && r.body.rank === 0, r.body.rank);
  ok("...and is not stored", !big.store.get("board:60").includes("lowest"), 1);
  r = await call(big, "GET", "/boards");
  ok("GET sends only the top 25", r.body["60"].length === 25, r.body["60"].length);

  r = await call(env, "OPTIONS", "/submit", undefined, ORIGIN);
  ok("answers the CORS preflight", r.status === 204 && r.res.headers.get("Access-Control-Allow-Methods").includes("POST") && r.res.headers.get("Access-Control-Allow-Headers") === "content-type", r.status);
  r = await call(env, "OPTIONS", "/submit", undefined, "https://evil.example");
  ok("gives a stranger no CORS headers", !r.cors, r.cors);
  r = await call(env, "GET", "/nope");
  ok("404s unknown paths", r.status === 404, r.status);
  r = await call(makeEnv({ ALLOWED_ORIGINS: "https://other.example" }), "POST", "/submit", { mode: "5", name: "abc", score: 5, t: 1 });
  ok("ALLOWED_ORIGINS replaces the default list", r.status === 403, r.status);
  r = await worker.fetch(fake("GET", "/boards", undefined, ORIGIN), {});
  ok("says so when storage is not connected", (await r.json()).error.includes("not connected"), 1);

  const failures = Object.entries(results).filter(([, v]) => v !== "pass");
  return { results, total: Object.keys(results).length, failed: failures.length };
}
