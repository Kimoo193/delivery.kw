// Customer reviews: list approved reviews and submit new ones (pending approval).
// Reviews are only shown once there are at least MIN_SHOWN approved ones; until then
// the section stays an invitation, so an empty or failed list never reads as "no customers".
(function () {
  var MIN_SHOWN = 3;
  var list = document.getElementById("reviewsList");
  var form = document.getElementById("reviewForm");
  if (!list || !form) return;
  var status = document.getElementById("reviewStatus");
  var title = document.getElementById("reviewsTitle");
  var lead = document.getElementById("reviewsLead");

  function stars(n) {
    return "★★★★★".slice(0, n) + "☆☆☆☆☆".slice(0, 5 - n);
  }

  function monthYear(iso) {
    var d = new Date(String(iso).replace(" ", "T") + "Z");
    return isNaN(d) ? "" : d.toLocaleDateString("ar-KW", { month: "long", year: "numeric" });
  }

  function render(reviews) {
    if (reviews.length < MIN_SHOWN) return;
    list.textContent = "";
    reviews.forEach(function (r) {
      var card = document.createElement("figure");
      card.className = "review";
      var s = document.createElement("div");
      s.className = "review-stars";
      s.setAttribute("role", "img");
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
    if (title) title.textContent = "شنو يقولون عملاؤنا عن Delivery.KW";
    if (lead) lead.textContent = "آراء حقيقية من عملائنا، وتقدر تضيف رأيك تحت.";
    list.hidden = false;
  }

  fetch("/api/reviews")
    .then(function (res) { return res.ok ? res.json() : { reviews: [] }; })
    .then(function (data) { render(data.reviews || []); })
    .catch(function () { /* keep the invitation state */ });

  function say(text, bad, focusEl) {
    status.hidden = false;
    status.textContent = text;
    status.classList.toggle("bad", !!bad);
    if (focusEl) focusEl.focus();
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var fd = new FormData(form);
    var name = String(fd.get("name") || "").trim();
    var comment = String(fd.get("comment") || "").trim();
    var rating = Number(fd.get("rating"));
    if (name.length < 2) return say("اكتب اسمك (حرفين على الأقل).", true, form.elements.name);
    if (!rating) return say("اختار عدد النجوم للتقييم.", true, form.querySelector("input[name=rating]"));
    if (comment.length < 10) return say("اكتب رأيك في 10 أحرف على الأقل.", true, form.elements.comment);

    var btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    say("جاري الإرسال…", false);
    fetch("/api/reviews", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: name,
        area: fd.get("area"),
        rating: rating,
        comment: comment,
        website: fd.get("website"),
      }),
    })
      .then(function (res) {
        if (res.ok) {
          form.reset();
          say("شكرًا لك! وصلنا رأيك وبيظهر بعد المراجعة.", false);
        } else if (res.status === 429) {
          say("أرسلت أكثر من رأي اليوم، جرّب بكرة.", true);
        } else {
          say("ما قدرنا نحفظ الرأي، تأكد من الاسم والتقييم والتعليق وجرّب مرة ثانية.", true);
        }
      })
      .catch(function () {
        say("صار خطأ في الاتصال، جرّب مرة ثانية.", true);
      })
      .finally(function () {
        btn.disabled = false;
      });
  });
})();
