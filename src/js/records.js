/* records.js — the record boards.
 *
 * This is the only script on the site that can send anything anywhere, which
 * is why it is a file of its own and not part of game.js. The game makes no
 * network requests at all and a test holds it to that; everything that talks
 * to the records service is here, it is only loaded when a service is
 * configured, and it only acts when a button is pressed:
 *
 *   Show records       GET  /boards
 *   Submit to records  POST /submit   { mode, name, score, t }
 *
 * Nothing is requested on load. Requests carry no cookies and no referrer,
 * and this file never touches storage: the username and the "already
 * submitted" flag are handed to game.js in an event, so the one place that
 * writes storage stays the one place.
 */
(function () {
  "use strict";

  var root = document.querySelector("[data-game]");
  var endpoint = root && root.getAttribute("data-records-endpoint");
  if (!endpoint) return;

  var MODES = ["5", "10", "30", "60"];
  var HEADING = { "5": "5 minutes", "10": "10 minutes", "30": "30 minutes", "60": "1 hour" };
  var ADJECTIVE = { "5": "5-minute", "10": "10-minute", "30": "30-minute", "60": "1-hour" };

  function $(sel) { return root.querySelector(sel); }
  var btnLoad = $("[data-records-load]");
  var elStatus = $("[data-records-status]");
  var elBoards = $("[data-records-boards]");
  var form = $("[data-submit]");
  var nameInput = $("[data-submit-name]");
  var btnSubmit = $("[data-submit-btn]");
  var elSubStatus = $("[data-submit-status]");
  var elSubMode = $("[data-submit-mode]");

  /* Mirrors the check in the service, which is the one that counts. */
  var NAME_OK = /^[\p{L}\p{N}][\p{L}\p{N} _.\-]{1,19}$/u;

  var current = null;      // the run that just ended
  var you = "";            // highlighted on the boards
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

  /* Drawing ---------------------------------------------------------------- */

  function cell(tag, text, scope) {
    var el = document.createElement(tag);
    el.textContent = text;
    if (scope) el.setAttribute("scope", scope);
    return el;
  }

  /* Names come from strangers. Everything is set with textContent, never as
     markup. */
  function renderBoards(boards) {
    elBoards.textContent = "";
    MODES.forEach(function (m) {
      var entries = boards[m] || [];
      var wrap = document.createElement("section");
      wrap.className = "gboard";
      var h = document.createElement("h3");
      h.className = "gboard__title";
      h.textContent = HEADING[m];
      wrap.appendChild(h);

      if (!entries.length) {
        var p = document.createElement("p");
        p.className = "gboard__empty";
        p.textContent = "Nothing here yet. Be first.";
        wrap.appendChild(p);
      } else {
        var table = document.createElement("table");
        var cap = document.createElement("caption");
        cap.className = "visually-hidden";
        cap.textContent = "Most levels named in " + HEADING[m];
        table.appendChild(cap);
        var head = document.createElement("tr");
        head.appendChild(cell("th", "#", "col"));
        head.appendChild(cell("th", "Name", "col"));
        head.appendChild(cell("th", "Named", "col"));
        var thead = document.createElement("thead");
        thead.appendChild(head);
        table.appendChild(thead);
        var tbody = document.createElement("tbody");
        entries.slice(0, 10).forEach(function (e, i) {
          var tr = document.createElement("tr");
          if (you && e.n.toLowerCase() === you.toLowerCase()) tr.className = "is-you";
          tr.appendChild(cell("td", String(i + 1)));
          tr.appendChild(cell("td", e.n));
          tr.appendChild(cell("td", e.s.toLocaleString("en-US")));
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        wrap.appendChild(table);
      }
      elBoards.appendChild(wrap);
    });
  }

  /* Show records ----------------------------------------------------------- */

  function loadBoards() {
    if (busy) return;
    busy = true;
    btnLoad.disabled = true;
    elStatus.textContent = "Loading…";
    request("/boards", { method: "GET" }).then(function (r) {
      busy = false;
      btnLoad.disabled = false;
      if (!r.ok) { elStatus.textContent = "Couldn’t load the records right now."; return; }
      elStatus.textContent = "";
      btnLoad.textContent = "Refresh records";
      renderBoards(r.data);
    }, function () {
      busy = false;
      btnLoad.disabled = false;
      elStatus.textContent = "Couldn’t reach the records service.";
    });
  }

  btnLoad.addEventListener("click", loadBoards);

  /* Submit to records ------------------------------------------------------ */

  function submit() {
    if (!current || busy) return;
    var name = clean(nameInput.value);
    if (!NAME_OK.test(name)) {
      elSubStatus.textContent =
        "Use 2–20 letters, numbers, spaces, dots, dashes or underscores.";
      return;
    }
    busy = true;
    btnSubmit.disabled = true;
    elSubStatus.textContent = "Sending…";
    request("/submit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        mode: current.mode, name: name, score: current.score, t: current.lastAt }),
    }).then(function (r) {
      busy = false;
      if (!r.ok || !r.data.ok) {
        btnSubmit.disabled = false;
        elSubStatus.textContent = (r.data && r.data.error) || "That didn’t go through.";
        return;
      }
      you = name;
      current.submitted = true;
      nameInput.disabled = true;
      btnSubmit.hidden = true;
      var board = ADJECTIVE[current.mode] + " board";
      elSubStatus.textContent =
        !r.data.rank ? "Sent, but it didn’t make the top 100 this time."
        : r.data.improved === false
          ? "You already have a better score here — #" + r.data.rank + " on the " + board + "."
          : "You’re #" + r.data.rank + " on the " + board + ".";
      document.dispatchEvent(new CustomEvent("records:submitted", {
        detail: { mode: current.mode, name: name, rank: r.data.rank } }));
      if (r.data.boards) renderBoards(r.data.boards);
    }, function () {
      busy = false;
      btnSubmit.disabled = false;
      elSubStatus.textContent = "Couldn’t reach the records service.";
    });
  }

  btnSubmit.addEventListener("click", submit);
  nameInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); submit(); }
  });

  /* The game tells us when a run ends, and when it is wiped. */

  document.addEventListener("game:finished", function (e) {
    var d = e.detail;
    current = d;
    var rankable = d.mode !== "free" && d.score > 0;
    form.hidden = !rankable;
    if (!rankable) return;
    elSubMode.textContent = ADJECTIVE[d.mode];
    nameInput.value = d.name || "";
    if (d.submitted) {
      you = d.name || "";
      nameInput.disabled = true;
      btnSubmit.hidden = true;
      elSubStatus.textContent = "Submitted as " + (d.name || "your username") + ".";
    } else {
      nameInput.disabled = false;
      btnSubmit.hidden = false;
      btnSubmit.disabled = false;
      elSubStatus.textContent = "";
    }
  });

  document.addEventListener("game:reset", function () {
    current = null;
    form.hidden = true;
    nameInput.disabled = false;
    btnSubmit.hidden = false;
    btnSubmit.disabled = false;
    elSubStatus.textContent = "";
  });
})();
