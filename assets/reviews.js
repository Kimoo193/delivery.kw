// Customer reviews: list approved reviews and submit new ones (pending approval).
(function () {
  var list = document.getElementById("reviewsList");
  var form = document.getElementById("reviewForm");
  if (!list || !form) return;
  var status = document.getElementById("reviewStatus");

  function stars(n) {
    return "★★★★★".slice(0, n) + "☆☆☆☆☆".slice(0, 5 - n);
  }

  function monthYear(iso) {
    var d = new Date(String(iso).replace(" ", "T") + "Z");
    return isNaN(d) ? "" : d.toLocaleDateString("ar-KW", { month: "long", year: "numeric" });
  }

  function render(reviews) {
    list.textContent = "";
    if (!reviews.length) {
      var empty = document.createElement("p");
      empty.className = "reviews-empty";
      empty.textContent = "كن أول من يكتب رأيه في خدمتنا.";
      list.appendChild(empty);
      return;
    }
    reviews.forEach(function (r) {
      var card = document.createElement("figure");
      card.className = "review";
      var s = document.createElement("div");
      s.className = "review-stars";
      s.setAttribute("aria-label", r.rating + " من 5");
      s.textContent = stars(r.rating);
      var q = document.createElement("blockquote");
      q.textContent = r.comment;
      var who = document.createElement("figcaption");
      who.textContent = r.name + (r.area ? " · " + r.area : "") + " · " + monthYear(r.created_at);
      card.appendChild(s);
      card.appendChild(q);
      card.appendChild(who);
      list.appendChild(card);
    });
  }

  fetch("/api/reviews")
    .then(function (res) { return res.ok ? res.json() : { reviews: [] }; })
    .then(function (data) { render(data.reviews || []); })
    .catch(function () { render([]); });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var fd = new FormData(form);
    var payload = {
      name: fd.get("name"),
      area: fd.get("area"),
      rating: Number(fd.get("rating")),
      comment: fd.get("comment"),
      website: fd.get("website"),
    };
    var btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    status.hidden = false;
    status.textContent = "جاري الإرسال…";
    fetch("/api/reviews", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        if (res.ok) {
          form.reset();
          status.textContent = "شكرًا لك! وصلنا رأيك وبيظهر بعد المراجعة.";
        } else if (res.status === 429) {
          status.textContent = "أرسلت أكثر من رأي اليوم، جرّب بكرة.";
        } else {
          status.textContent = "تأكد من كتابة الاسم والتقييم وتعليق من 10 أحرف على الأقل.";
        }
      })
      .catch(function () {
        status.textContent = "صار خطأ في الاتصال، جرّب مرة ثانية.";
      })
      .finally(function () {
        btn.disabled = false;
      });
  });
})();
