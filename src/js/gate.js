/* gate.js — the notice before the Game opens.
 *
 * Only on the page when the record boards are switched on. It asks the visitor
 * to read the privacy policy and accept that the only way to have a record
 * removed is to message the site's owner, and it keeps the Game closed until
 * they do.
 *
 * It is a native <dialog> opened with showModal(), which makes the rest of the
 * page inert (keyboard, pointer and screen reader alike), traps focus inside,
 * and gives it a ::backdrop to fade and blur. What the browser does not
 * guarantee is that it stays: Escape cancels a modal dialog, and Chrome will
 * close one on a second Escape even when the first was prevented. So it is put
 * straight back if it closes without an Accept.
 *
 * "Don't ask me again" keeps a version marker in localStorage, under its own
 * key and apart from the game's progress. The marker is the hash of the notice
 * and the privacy page, so changing either asks everyone again: nobody is
 * bound by wording they never saw. Nothing else is stored, and Deny stores
 * nothing at all.
 *
 * Deliberately not part of game.js, which makes no requests and writes one
 * storage key and is held to both by tests.
 */
(function () {
  "use strict";

  var dialog = document.querySelector("[data-gate]");
  /* A browser with no <dialog> cannot show this. The submit box and the board
     both carry the same removal wording beside them, so nothing is hidden from
     anyone; the notice just is not a gate there. */
  if (!dialog || typeof dialog.showModal !== "function") return;

  var KEY = "hall-of-extremes.game.consent.v1";
  var version = dialog.getAttribute("data-version") || "";
  var again = dialog.querySelector("[data-gate-again]");
  var btnAccept = dialog.querySelector("[data-gate-accept]");
  var btnDeny = dialog.querySelector("[data-gate-deny]");
  var denied = dialog.querySelector("[data-gate-denied]");
  var accepted = false;

  function remembered() {
    try {
      var v = JSON.parse(window.localStorage.getItem(KEY));
      return !!v && v.v === version;
    } catch (e) { return false; }
  }

  function remember() {
    try { window.localStorage.setItem(KEY, JSON.stringify({ v: version })); } catch (e) { /* ignore */ }
  }

  /* Accepting without the box ticked also clears an older marker, so "ask me
     every time" really is every time. */
  function forget() {
    try { window.localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
  }

  if (remembered()) return;

  /* Escape cancels a modal dialog. It is not allowed to. */
  dialog.addEventListener("cancel", function (e) { e.preventDefault(); });
  dialog.addEventListener("close", function () {
    if (!accepted) dialog.showModal();
  });

  btnAccept.addEventListener("click", function () {
    if (again.checked) remember(); else forget();
    accepted = true;
    dialog.close();
    var input = document.querySelector("[data-input]");
    if (input && !input.disabled && window.matchMedia &&
        window.matchMedia("(pointer: fine)").matches) {
      input.focus();
    }
  });

  /* Deny does not close anything and does not store anything. It says why the
     Game is still shut and offers the way out. */
  btnDeny.addEventListener("click", function () {
    denied.hidden = false;
    denied.setAttribute("tabindex", "-1");
    denied.focus();
  });

  dialog.showModal();
  /* Focus the notice itself, not a control: the first focusable thing is a
     link, and the last thing a consent screen wants is an accidental Enter. */
  dialog.setAttribute("tabindex", "-1");
  dialog.focus();
})();
