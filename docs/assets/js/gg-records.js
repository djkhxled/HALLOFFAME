/* gg-records.js — GeometryGuessr's score board.
 *
 * The only GeometryGuessr script that can send anything anywhere, kept apart from
 * gg.js (which makes no requests, and a test holds it to that). It is on the page
 * only when a records service is configured, and it only acts when a button is
 * pressed:
 *
 *   Show the board   GET  /boards
 *   Submit score     POST /submit   { mode: "gg", name, score, named }
 *
 * Nothing is requested on load. Requests carry no cookies and no referrer, and this
 * file never touches storage: the username goes back to gg.js in an event, so the one
 * place that writes storage stays the one place.
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-gg]");
  var endpoint = root && root.getAttribute("data-records-endpoint");
  if (!endpoint) return;

  function $(sel) { return root.querySelector(sel); }
  var panel = $("[data-rec]");
  var form = $("[data-rec-form]");
  var nameInput = $("[data-rec-name]");
  var btnSubmit = $("[data-rec-submit]");
  var elStatus = $("[data-rec-status]");
  var boards = root.querySelectorAll("[data-rec-board]");
  var showButtons = root.querySelectorAll("[data-rec-show]");
  if (!panel || !form) return;

  /* Mirrors the check in the service, which is the one that counts. */
  var NAME_OK = /^[\p{L}\p{N}][\p{L}\p{N} _.\-]{1,19}$/u;

  var current = null;      // the game that just ended
  var sent = false;        // this game is already on the board
  var you = "";
  var busy = false;

  function clean(s) { return s.normalize("NFKC").replace(/\s+/g, " ").trim(); }

  function request(path, options) {
    var init = { credentials: "omit", referrerPolicy: "no-referrer", cache: "no-store" };
    for (var k in options) init[k] = options[k];
    return fetch(endpoint + path, init).then(function (res) {
      return res.json().then(
        function (data) { return { ok: res.ok, data: data }; },
        function () { return { ok: false, data: { error: "Unexpected reply" } }; });
    });
  }

  /* Names come from strangers: everything is set with textContent, never as markup. */
  function render(entries) {
    boards.forEach(function (box) {
      box.textContent = "";
      if (!entries.length) {
        var p = document.createElement("p");
        p.className = "gg-board__empty";
        p.textContent = "Nobody on the board yet. Be first.";
        box.appendChild(p);
        return;
      }
      var ol = document.createElement("ol");
      ol.className = "gg-board";
      entries.slice(0, 10).forEach(function (e, i) {
        var li = document.createElement("li");
        if (you && e.n.toLowerCase() === you.toLowerCase()) li.className = "is-you";
        var rank = document.createElement("span"); rank.className = "gg-board__rank"; rank.textContent = String(i + 1);
        var name = document.createElement("span"); name.className = "gg-board__name"; name.textContent = e.n;
        var named = document.createElement("span"); named.className = "gg-board__named"; named.textContent = e.r + "/5";
        var pts = document.createElement("span"); pts.className = "gg-board__pts"; pts.textContent = e.s.toLocaleString("en-US");
        li.appendChild(rank); li.appendChild(name); li.appendChild(named); li.appendChild(pts);
        ol.appendChild(li);
      });
      box.appendChild(ol);
    });
  }

  function showBoard() {
    if (busy) return;
    busy = true;
    showButtons.forEach(function (b) { b.disabled = true; });
    request("/boards", { method: "GET" }).then(function (r) {
      if (!r.ok) throw new Error(r.data && r.data.error || "Could not load the board");
      render((r.data && r.data.gg) || []);
    }).catch(function (err) {
      boards.forEach(function (box) { box.textContent = err.message || "Could not load the board."; });
    }).then(function () {
      busy = false;
      showButtons.forEach(function (b) { b.disabled = false; });
    });
  }

  function submit() {
    if (busy || sent || !current) return;
    var name = clean(nameInput.value);
    if (!NAME_OK.test(name)) {
      elStatus.textContent = "Usernames are 2–20 letters, numbers, spaces, dots, dashes or underscores.";
      nameInput.focus();
      return;
    }
    busy = true;
    btnSubmit.disabled = true;
    elStatus.textContent = "Sending…";
    request("/submit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ mode: "gg", name: name, score: current.score, named: current.named })
    }).then(function (r) {
      if (!r.ok || !r.data || !r.data.ok) throw new Error(r.data && r.data.error || "Could not submit");
      sent = true;
      you = name;
      elStatus.textContent = r.data.improved
        ? (r.data.rank ? "You're #" + r.data.rank + " on the board." : "Submitted, but it's not in the top 100.")
        : "Your best on the board is still higher, so it stays.";
      render((r.data.boards && r.data.boards.gg) || []);
      root.dispatchEvent(new CustomEvent("gg:submitted", { detail: { name: name } }));
      form.classList.add("is-sent");
    }).catch(function (err) {
      elStatus.textContent = (err && err.message) || "Could not submit.";
      btnSubmit.disabled = false;
    }).then(function () { busy = false; });
  }

  root.addEventListener("gg:finished", function (e) {
    current = e.detail || null;
    sent = false;
    form.classList.remove("is-sent");
    btnSubmit.disabled = false;
    boards.forEach(function (box) { if (box.closest("[data-rec]")) box.textContent = ""; });
    if (!current || current.named < 1) {
      panel.hidden = true;
      return;
    }
    panel.hidden = false;
    if (current.name && !nameInput.value) nameInput.value = current.name;
    you = clean(nameInput.value);
    elStatus.textContent = "";
  });

  form.addEventListener("submit", function (e) { e.preventDefault(); });
  nameInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); submit(); }
  });
  btnSubmit.addEventListener("click", submit);
  showButtons.forEach(function (b) { b.addEventListener("click", showBoard); });
})();
