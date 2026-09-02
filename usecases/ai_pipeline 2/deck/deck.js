// Shared deck behaviour: nav highlight, prev/next + arrow keys, show/hide toggle.
(function () {
  var PAGES = [
    ["index.html", "Overview"],
    ["platform.html", "Platform"],
    ["implementation.html", "Implementation"],
    ["decisions.html", "Decisions"],
    ["future.html", "Future Use Cases"],
    ["usecases.html", "AFNI Ideas"],
  ];
  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  var idx = Math.max(0, PAGES.findIndex(function (p) { return p[0] === here; }));

  // highlight current nav link
  document.querySelectorAll(".nav a[data-page]").forEach(function (a) {
    if (a.getAttribute("data-page") === PAGES[idx][0]) a.classList.add("active");
  });

  // build pager
  var pager = document.querySelector(".pager");
  if (pager) {
    var prev = PAGES[idx - 1], next = PAGES[idx + 1];
    var dots = PAGES.map(function (p, i) { return '<span class="dot' + (i === idx ? " on" : "") + '"></span>'; }).join("");
    pager.innerHTML =
      (prev ? '<a href="' + prev[0] + '">&larr; ' + prev[1] + "</a>" : '<span class="muted">Start</span>') +
      '<div style="display:flex;align-items:center;gap:14px"><span class="muted">' + (idx + 1) + " / " + PAGES.length +
      '</span><div class="dots">' + dots + "</div></div>" +
      (next ? '<a class="primary" href="' + next[0] + '">' + next[1] + " &rarr;</a>" : '<span class="muted">End</span>');
    document.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight" && next) location.href = next[0];
      if (e.key === "ArrowLeft" && prev) location.href = prev[0];
    });
  }
})();

// Generic show/hide toggle used by the AFNI ideas page.
function toggleBlock(id, btn) {
  var el = document.getElementById(id);
  if (!el) return;
  var hidden = el.classList.toggle("hidden");
  if (btn) btn.textContent = hidden ? btn.getAttribute("data-show") : btn.getAttribute("data-hide");
}
