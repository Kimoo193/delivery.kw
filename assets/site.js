// Shared behaviour for the generated area/article pages: light/dark toggle.
(function () {
  var root = document.documentElement,
    modeBtn = document.getElementById("modeBtn"),
    themeMeta = document.querySelector('meta[name="theme-color"]');
  if (!modeBtn) return;
  function applyMode(light) {
    if (light) root.setAttribute("data-mode", "light");
    else root.removeAttribute("data-mode");
    modeBtn.setAttribute("aria-pressed", light ? "true" : "false");
    modeBtn.setAttribute("aria-label", light ? "الوضع الداكن" : "الوضع الفاتح");
    if (themeMeta) themeMeta.setAttribute("content", light ? "#F6F7FB" : "#0A1733");
  }
  applyMode(root.getAttribute("data-mode") === "light");
  modeBtn.addEventListener("click", function () {
    var light = root.getAttribute("data-mode") !== "light";
    applyMode(light);
    try { localStorage.setItem("dkw-mode", light ? "light" : "dark"); } catch (e) {}
  });
})();
