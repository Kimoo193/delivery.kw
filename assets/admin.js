// Admin dashboard: orders, customers, visitors and review moderation.
// The admin key comes from the login form or a #key=... link. It is kept in sessionStorage
// (this tab only), removed from the address bar, and sent only in the X-Admin-Key header.
(function () {
  var STORE = "dkw-admin-key";
  var $ = function (id) { return document.getElementById(id); };
  var login = $("admLogin"), app = $("admApp"), msg = $("adminMsg");
  var key = "";

  var fromHash = new URLSearchParams(location.hash.slice(1)).get("key");
  if (fromHash) {
    try { sessionStorage.setItem(STORE, fromHash); } catch (e) {}
    history.replaceState(null, "", location.pathname);
  }
  try { key = fromHash || sessionStorage.getItem(STORE) || ""; } catch (e) { key = fromHash || ""; }

  var SOURCES = { google: "Google", bing: "Bing", yahoo: "Yahoo", duckduckgo: "DuckDuckGo", instagram: "انستجرام",
    facebook: "فيسبوك", whatsapp: "واتساب", x: "X / تويتر", tiktok: "تيك توك", snapchat: "سناب شات",
    chatgpt: "ChatGPT", perplexity: "Perplexity", ai: "ذكاء اصطناعي", direct: "مباشر / بدون مصدر", internal: "من داخل الموقع" };
  var DEVICES = { mobile: "جوال", desktop: "كمبيوتر", tablet: "تابلت" };
  var STATUS = { "new": "جديد", done: "تم التوصيل", cancelled: "ملغي" };
  var region = null;
  try { region = new Intl.DisplayNames(["ar"], { type: "region" }); } catch (e) {}
  var num = new Intl.NumberFormat("en-US");

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function when(utc) {
    var d = new Date(String(utc).replace(" ", "T") + "Z");
    return isNaN(d) ? utc : d.toLocaleString("ar-KW", { timeZone: "Asia/Kuwait", day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
  }
  function phoneText(p) {
    return p && p.indexOf("965") === 0 && p.length === 11 ? "+965 " + p.slice(3, 7) + " " + p.slice(7) : "+" + p;
  }
  function pct(a, b) { return b ? Math.round((a / b) * 100) + "%" : "—"; }

  function api(path, method, body) {
    return fetch(path, {
      method: method || "GET",
      headers: { "content-type": "application/json", "X-Admin-Key": key },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
    }).then(function (r) {
      if (r.status === 401) throw new Error("unauthorized");
      if (!r.ok) throw new Error("failed");
      return r.json();
    });
  }
  function fail(err) {
    if (err && err.message === "unauthorized") {
      try { sessionStorage.removeItem(STORE); } catch (e) {}
      key = "";
      showLogin("المفتاح غير صحيح، جرّب مرة ثانية.");
      return;
    }
    msg.textContent = "صار خطأ في تحميل البيانات، حدّث الصفحة وجرّب مرة ثانية.";
  }

  // ---------- charts ----------
  function bars(title, rows, label) {
    var box = el("div", "card adm-box");
    box.appendChild(el("h3", null, title));
    if (!rows || !rows.length) { box.appendChild(el("p", "muted", "ما في بيانات للحين.")); return box; }
    var max = Math.max.apply(null, rows.map(function (r) { return r.n; }));
    var total = rows.reduce(function (s, r) { return s + r.n; }, 0);
    var list = el("ul", "adm-bars");
    rows.forEach(function (r) {
      var li = el("li");
      var name = el("span", "adm-bar-k", label ? label(r.k) : r.k);
      var track = el("span", "adm-bar-t");
      var fill = el("span", "adm-bar-f");
      fill.style.setProperty("--w", (max ? (r.n / max) * 100 : 0) + "%");
      track.appendChild(fill);
      li.appendChild(name);
      li.appendChild(track);
      li.appendChild(el("span", "adm-bar-n", num.format(r.n) + " · " + pct(r.n, total)));
      list.appendChild(li);
    });
    box.appendChild(list);
    return box;
  }

  function columns(title, rows, days, valueKey, note) {
    var box = el("div", "card adm-box adm-wide");
    box.appendChild(el("h3", null, title));
    if (note) box.appendChild(el("p", "muted adm-note", note));
    var map = {};
    (rows || []).forEach(function (r) { map[r.k] = r[valueKey || "n"]; });
    var series = [];
    var today = new Date(Date.now() + 3 * 3600 * 1000);
    var span = Math.min(days, 90);
    for (var i = span - 1; i >= 0; i--) {
      var d = new Date(today.getTime() - i * 86400000).toISOString().slice(0, 10);
      series.push({ d: d, n: map[d] || 0 });
    }
    var max = Math.max(1, Math.max.apply(null, series.map(function (s) { return s.n; })));
    var chart = el("div", "adm-cols");
    chart.setAttribute("role", "img");
    chart.setAttribute("aria-label", title);
    series.forEach(function (s) {
      var c = el("span", "adm-col");
      c.style.setProperty("--h", (s.n / max) * 100 + "%");
      c.title = s.d + ": " + s.n;
      if (s.n) c.appendChild(el("i", null, String(s.n)));
      chart.appendChild(c);
    });
    box.appendChild(chart);
    var axis = el("div", "adm-axis");
    axis.appendChild(el("span", null, series[0].d));
    axis.appendChild(el("span", null, series[series.length - 1].d));
    box.appendChild(axis);
    return box;
  }

  function kpi(parent, label, value, hint) {
    var k = el("div", "adm-kpi");
    k.appendChild(el("b", null, value));
    k.appendChild(el("span", null, label));
    if (hint) k.appendChild(el("small", null, hint));
    parent.appendChild(k);
  }

  // ---------- overview + visitors ----------
  var days = 30;
  function loadDashboard() {
    msg.textContent = "جاري التحميل…";
    return api("/api/admin/dashboard?days=" + days).then(function (d) {
      msg.textContent = "";
      var o = d.orderTotals || {}, e = d.eventTotals || {};
      var visitors = e.visitors || 0, orders = o.orders || 0;

      var k = $("kpis"); k.textContent = "";
      kpi(k, "طلبات من الموقع", num.format(orders), (o.open || 0) + " جديد · " + (o.done || 0) + " تم");
      kpi(k, "عملاء (برقم تواصل)", num.format(o.customers || 0));
      kpi(k, "زوار", num.format(visitors), num.format(e.views || 0) + " مشاهدة صفحة");
      kpi(k, "نسبة التحويل", pct(orders, visitors), "طلبات ÷ زوار");
      kpi(k, "ضغطات واتساب", num.format((e.wa || 0) + orders), "زر واتساب + إرسال طلب");
      kpi(k, "اتصال / انستجرام", num.format(e.calls || 0) + " / " + num.format(e.ig || 0));

      var ov = $("ovCharts"); ov.textContent = "";
      ov.appendChild(columns("الطلبات باليوم", d.ordersByDay, days));
      ov.appendChild(bars("أنواع الطلبات", d.kinds));
      ov.appendChild(bars("أكثر مناطق الاستلام", d.fromAreas));
      ov.appendChild(bars("أكثر مناطق التسليم", d.toAreas));
      ov.appendChild(bars("أكثر المسارات", d.routes));
      ov.appendChild(bars("طريقة الدفع", d.pays));
      ov.appendChild(bars("ساعات الطلب (بتوقيت الكويت)", (d.orderHours || []).map(function (r) {
        return { k: (r.k < 10 ? "0" : "") + r.k + ":00", n: r.n };
      })));
      ov.appendChild(bars("مصدر الطلبات", d.orderSources, function (s) { return SOURCES[s] || s; }));

      var vk = $("vKpis"); vk.textContent = "";
      kpi(vk, "زوار", num.format(visitors));
      kpi(vk, "مشاهدات", num.format(e.views || 0), visitors ? (Math.round(((e.views || 0) / visitors) * 10) / 10) + " صفحة لكل زائر" : "");
      kpi(vk, "ضغطات واتساب", num.format(e.wa || 0));
      kpi(vk, "ضغطات اتصال", num.format(e.calls || 0));
      kpi(vk, "ضغطات انستجرام", num.format(e.ig || 0));

      var vc = $("vCharts"); vc.textContent = "";
      vc.appendChild(columns("الزوار باليوم", d.visitsByDay, days, "v", "الزائر يُحسب مرة وحدة في اليوم، بدون كوكيز."));
      vc.appendChild(bars("من وين جوا الزوار", d.sources, function (s) { return SOURCES[s] || s; }));
      vc.appendChild(bars("أكثر الصفحات زيارة", d.pages, function (p) { return p === "/" ? "الرئيسية" : decodeURIComponent(p); }));
      vc.appendChild(bars("الأجهزة", d.devices, function (x) { return DEVICES[x] || x; }));
      vc.appendChild(bars("الدول", d.countries, function (c) { return c === "—" ? c : (region ? region.of(c) : c) || c; }));
    }).catch(fail);
  }

  // ---------- orders ----------
  var lastOrders = [];
  function loadOrders() {
    var q = $("ordQ").value.trim(), st = $("ordStatus").value;
    return api("/api/admin/orders?status=" + encodeURIComponent(st) + "&q=" + encodeURIComponent(q)).then(function (d) {
      lastOrders = d.orders || [];
      var box = $("ordersList"); box.textContent = "";
      $("ordCount").textContent = lastOrders.length + " طلب";
      if (!lastOrders.length) { box.appendChild(el("p", "muted", "ما في طلبات بهذا الفلتر.")); return; }
      lastOrders.forEach(function (o) { box.appendChild(orderCard(o)); });
    }).catch(fail);
  }

  function orderCard(o) {
    var card = el("article", "card adm-order is-" + o.status);
    var head = el("div", "adm-order-h");
    head.appendChild(el("span", "adm-pill is-" + o.status, STATUS[o.status] || o.status));
    head.appendChild(el("span", "muted", when(o.created_at) + " · #" + o.id));
    card.appendChild(head);
    card.appendChild(el("p", "adm-route", o.from_area + " ← " + o.to_area));
    var meta = [o.kind, o.pay].filter(Boolean).join(" · ");
    if (meta) card.appendChild(el("p", "adm-meta", meta));
    var who = el("p", "adm-who");
    who.appendChild(el("span", null, o.name || "بدون اسم"));
    if (o.phone) {
      var tel = el("a", null, phoneText(o.phone));
      tel.href = "tel:+" + o.phone; tel.dir = "ltr";
      who.appendChild(tel);
    }
    card.appendChild(who);
    if (o.notes) card.appendChild(el("p", "adm-notes", o.notes));
    var src = [SOURCES[o.source] || o.source, o.page].filter(Boolean).join(" · ");
    if (src) card.appendChild(el("p", "muted adm-src", "المصدر: " + src));

    var actions = el("div", "adm-actions");
    if (o.phone) {
      var wa = el("a", "btn btn-wa btn-sm", "واتساب");
      wa.href = "https://wa.me/" + o.phone; wa.target = "_blank"; wa.rel = "noopener noreferrer";
      actions.appendChild(wa);
    }
    ["new", "done", "cancelled"].forEach(function (s) {
      if (s !== o.status) actions.appendChild(orderButton(STATUS[s], s, o.id));
    });
    actions.appendChild(orderButton("حذف", "delete", o.id, "adm-danger"));
    card.appendChild(actions);
    return card;
  }

  function orderButton(label, action, id, extra) {
    var b = el("button", "btn btn-sm adm-btn" + (extra ? " " + extra : ""), label);
    b.type = "button";
    b.addEventListener("click", function () {
      if (action === "delete" && !b.dataset.sure) { b.dataset.sure = "1"; b.textContent = "متأكد؟ اضغط مرة ثانية"; return; }
      b.disabled = true;
      api("/api/admin/orders", "POST", { id: id, action: action }).then(function () { loadOrders(); loadDashboard(); }).catch(fail);
    });
    return b;
  }

  function csv() {
    var head = ["id", "التاريخ", "الاسم", "الرقم", "الاستلام", "التسليم", "النوع", "الدفع", "ملاحظات", "الحالة", "المصدر"];
    var rows = lastOrders.map(function (o) {
      return [o.id, o.created_at, o.name, o.phone, o.from_area, o.to_area, o.kind, o.pay, o.notes, STATUS[o.status], o.source];
    });
    var text = [head].concat(rows).map(function (r) {
      return r.map(function (c) {
        var s = c == null ? "" : String(c);
        if (/^[=+\-@]/.test(s)) s = "'" + s; // keep spreadsheet apps from running formulas
        return '"' + s.replace(/"/g, '""') + '"';
      }).join(",");
    }).join("\r\n");
    var a = el("a");
    a.href = URL.createObjectURL(new Blob(["﻿" + text], { type: "text/csv;charset=utf-8" }));
    a.download = "deliverykw-orders-" + new Date().toISOString().slice(0, 10) + ".csv";
    document.body.appendChild(a); a.click(); a.remove();
  }

  // ---------- customers ----------
  function loadCustomers() {
    return api("/api/admin/orders?view=customers").then(function (d) {
      var box = $("custList"); box.textContent = "";
      var list = d.customers || [];
      $("custCount").textContent = list.length + " عميل" + (d.withoutPhone ? " · " + d.withoutPhone + " طلب بدون رقم" : "");
      if (!list.length) { box.appendChild(el("p", "muted", "العملاء يظهرون هنا لما يكتبون رقم التواصل في نموذج الطلب.")); return; }
      var table = el("table", "adm-table");
      var thead = el("thead"), tr = el("tr");
      ["العميل", "الرقم", "الطلبات", "تم", "آخر طلب", "أول طلب", "الأصناف", "المناطق"].forEach(function (h) { tr.appendChild(el("th", null, h)); });
      thead.appendChild(tr); table.appendChild(thead);
      var tbody = el("tbody");
      list.forEach(function (c) {
        var row = el("tr");
        row.appendChild(el("td", null, (c.name || "بدون اسم") + (c.orders > 1 ? " ⭐" : "")));
        var td = el("td"), a = el("a", null, phoneText(c.phone));
        a.href = "https://wa.me/" + c.phone; a.target = "_blank"; a.rel = "noopener noreferrer"; a.dir = "ltr";
        td.appendChild(a); row.appendChild(td);
        row.appendChild(el("td", null, String(c.orders)));
        row.appendChild(el("td", null, String(c.done || 0)));
        row.appendChild(el("td", null, when(c.last)));
        row.appendChild(el("td", null, when(c.first)));
        row.appendChild(el("td", null, (c.kinds || "—").split(",").join("، ")));
        row.appendChild(el("td", null, (c.areas || "—").split(",").join("، ")));
        tbody.appendChild(row);
      });
      table.appendChild(tbody);
      var wrap = el("div", "adm-scroll");
      wrap.appendChild(table);
      box.appendChild(wrap);
    }).catch(fail);
  }

  // ---------- reviews ----------
  function loadReviews() {
    return api("/api/admin/reviews").then(function (data) {
      var box = $("adminList"); box.textContent = "";
      var reviews = data.reviews || [];
      var pending = reviews.filter(function (r) { return !r.approved; }).length;
      $("revCount").textContent = pending + " رأي بانتظار الموافقة · " + reviews.length + " إجمالي";
      $("revBadge").textContent = pending ? String(pending) : "";
      reviews.forEach(function (r) {
        var card = el("div", "card adm-order" + (r.approved ? " is-done" : ""));
        card.appendChild(el("p", "adm-meta", (r.approved ? "✅ منشور" : "⏳ بانتظار الموافقة") + " · " + "★".repeat(r.rating) +
          " · " + r.name + (r.area ? " · " + r.area : "") + " · " + when(r.created_at)));
        card.appendChild(el("p", null, r.comment));
        var actions = el("div", "adm-actions");
        if (!r.approved) actions.appendChild(reviewButton("موافقة ونشر", "approve", r.id, "btn btn-wa btn-sm"));
        actions.appendChild(reviewButton("حذف", "delete", r.id, "btn btn-sm adm-btn adm-danger"));
        card.appendChild(actions);
        box.appendChild(card);
      });
    }).catch(fail);
  }
  function reviewButton(label, action, id, cls) {
    var b = el("button", cls, label);
    b.type = "button";
    b.addEventListener("click", function () {
      b.disabled = true;
      api("/api/admin/reviews", "POST", { id: id, action: action }).then(loadReviews).catch(fail);
    });
    return b;
  }

  // ---------- shell ----------
  function showTab(name) {
    document.querySelectorAll("[data-panel]").forEach(function (p) { p.hidden = p.getAttribute("data-panel") !== name; });
    document.querySelectorAll(".adm-tabs button").forEach(function (b) {
      b.setAttribute("aria-selected", b.getAttribute("data-tab") === name ? "true" : "false");
    });
    if (name === "orders") loadOrders();
    if (name === "customers") loadCustomers();
    if (name === "reviews") loadReviews();
  }

  function showLogin(text) {
    app.hidden = true;
    login.hidden = false;
    $("admLoginMsg").textContent = text || "";
    $("admKey").focus();
  }

  function start() {
    login.hidden = true;
    app.hidden = false;
    loadDashboard();
    loadReviews();
  }

  login.addEventListener("submit", function (e) {
    e.preventDefault();
    key = $("admKey").value.trim();
    if (!key) return;
    try { sessionStorage.setItem(STORE, key); } catch (err) {}
    $("admKey").value = "";
    start();
  });
  $("admLogout").addEventListener("click", function () {
    try { sessionStorage.removeItem(STORE); } catch (e) {}
    key = "";
    showLogin("تم تسجيل الخروج.");
  });
  document.querySelectorAll(".adm-tabs button").forEach(function (b) {
    b.addEventListener("click", function () { showTab(b.getAttribute("data-tab")); });
  });
  $("admDays").addEventListener("change", function () { days = parseInt(this.value, 10) || 30; loadDashboard(); });
  $("admRefresh").addEventListener("click", function () {
    loadDashboard();
    var open = document.querySelector('.adm-tabs [aria-selected="true"]');
    if (open) showTab(open.getAttribute("data-tab"));
  });
  var t;
  $("ordQ").addEventListener("input", function () { clearTimeout(t); t = setTimeout(loadOrders, 300); });
  $("ordStatus").addEventListener("change", loadOrders);
  $("ordCsv").addEventListener("click", csv);

  if (key) start(); else showLogin();
})();
