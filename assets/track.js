// Cookie-free visit counter for the admin dashboard: one page view per load, plus
// clicks on WhatsApp, phone and Instagram links. Nothing is stored in the browser.
(function () {
  if (navigator.webdriver) return;
  function send(type) {
    var data = JSON.stringify({ t: type, p: location.pathname, r: document.referrer, q: location.search.slice(0, 200) });
    try {
      if (navigator.sendBeacon && navigator.sendBeacon("/api/track", data)) return;
      fetch("/api/track", { method: "POST", body: data, keepalive: true }).catch(function () {});
    } catch (e) {}
  }
  send("view");
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || a.id === "sendOrder") return; // the order button is counted as an order instead
    var href = a.getAttribute("href");
    if (/wa\.me/.test(href)) send("wa");
    else if (/^tel:/.test(href)) send("call");
    else if (/instagram\.com/.test(href)) send("ig");
  }, true);
})();
