// Review moderation page. The admin key is read from the URL fragment (#key=...),
// which browsers never send to the server, and is kept only in this tab.
(function () {
  var key = new URLSearchParams(location.hash.slice(1)).get("key") || "";
  var box = document.getElementById("adminList");
  var msg = document.getElementById("adminMsg");

  function api(method, body) {
    return fetch("/api/admin/reviews", {
      method: method,
      headers: { "content-type": "application/json", "X-Admin-Key": key },
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (r) {
      if (r.status === 401) throw new Error("unauthorized");
      return r.json();
    });
  }

  function row(r) {
    var card = document.createElement("div");
    card.className = "admin-review" + (r.approved ? " is-approved" : "");
    var head = document.createElement("p");
    head.className = "admin-meta";
    head.textContent = (r.approved ? "✅ منشور" : "⏳ بانتظار الموافقة") + " · " + "★".repeat(r.rating) +
      " · " + r.name + (r.area ? " · " + r.area : "") + " · " + r.created_at;
    var text = document.createElement("p");
    text.textContent = r.comment;
    var actions = document.createElement("div");
    actions.className = "admin-actions";
    if (!r.approved) actions.appendChild(button("موافقة ونشر", "approve", r.id, "btn btn-wa"));
    actions.appendChild(button("حذف", "delete", r.id, "btn"));
    card.appendChild(head);
    card.appendChild(text);
    card.appendChild(actions);
    return card;
  }

  function button(label, action, id, cls) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.textContent = label;
    b.addEventListener("click", function () {
      b.disabled = true;
      api("POST", { id: id, action: action }).then(load).catch(fail);
    });
    return b;
  }

  function fail(err) {
    msg.textContent = err && err.message === "unauthorized"
      ? "الرابط غير صحيح. افتح رابط الإدارة الكامل اللي فيه المفتاح."
      : "صار خطأ، حدّث الصفحة وجرّب مرة ثانية.";
  }

  function load() {
    api("GET").then(function (data) {
      box.textContent = "";
      var reviews = data.reviews || [];
      var pending = reviews.filter(function (r) { return !r.approved; }).length;
      msg.textContent = pending + " رأي بانتظار الموافقة · " + reviews.length + " إجمالي";
      reviews.forEach(function (r) { box.appendChild(row(r)); });
    }).catch(fail);
  }

  if (!key) {
    msg.textContent = "افتح هذي الصفحة من رابط الإدارة الكامل اللي فيه المفتاح.";
    return;
  }
  load();
})();
