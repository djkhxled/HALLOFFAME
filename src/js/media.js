/* media.js — click-to-load video. Nothing reaches YouTube until asked. */
(function () {
  "use strict";

  document.querySelectorAll(".videoframe__load").forEach(function (button) {
    button.addEventListener("click", function () {
      var id = button.dataset.youtube;
      if (!id) return;

      var frame = document.createElement("iframe");
      frame.src =
        "https://www.youtube-nocookie.com/embed/" +
        encodeURIComponent(id) +
        "?autoplay=1&rel=0";
      frame.title = button.dataset.title || "Level footage";
      frame.allow =
        "accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      frame.allowFullscreen = true;
      frame.referrerPolicy = "strict-origin-when-cross-origin";

      button.replaceWith(frame);
      frame.focus();
    });
  });
})();
