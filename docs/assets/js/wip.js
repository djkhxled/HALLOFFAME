/* wip.js — the "still unfinished" notice on the list and the level pages.
 *
 * It shows on arriving at the list section: from another site, a bookmark, a shared
 * link or the games. It does not show again while moving between the list and its
 * level pages. That is read from the page the visitor came from (document.referrer),
 * so nothing is remembered and nothing is written to the browser: the privacy page
 * promises that only the games keep anything.
 *
 * A native <dialog> opened with showModal(): the page behind goes inert, focus stays
 * inside, and Escape or the button closes it. The markup is closed, so without this
 * script nobody sees it.
 */
(function () {
  "use strict";

  var dialog = document.querySelector("[data-wip]");
  if (!dialog || typeof dialog.showModal !== "function") return;

  function fromTheList(ref) {
    try {
      var u = new URL(ref);
      return u.origin === location.origin && /^\/(list|levels)\//.test(u.pathname);
    } catch (e) { return false; }
  }
  if (fromTheList(document.referrer)) return;

  dialog.showModal();
})();
