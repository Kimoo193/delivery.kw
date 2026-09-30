// POST /api/order -> save an order prepared in the site form, just before WhatsApp opens.
// The order itself still happens on WhatsApp; this copy feeds the admin dashboard.
import { json, clean, ipHash, sourceOf } from "../../lib/common.js";

const MAX_PER_DAY = 20;
const STATUS_NEW = "new";

// Keep digits only (Arabic-Indic digits included), e.g. "+965 9945-4818" -> "96599454818".
function normalizePhone(v) {
  const s = clean(v, 30).replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660))
    .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 0x06F0)).replace(/\D/g, "");
  if (s.length === 8) return "965" + s;
  return s.length >= 8 && s.length <= 15 ? s : "";
}

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = JSON.parse(await request.text());
  } catch {
    return json({ error: "invalid" }, 400);
  }
  if (clean(body.website, 100)) return json({ ok: true });

  const from = clean(body.from, 40);
  const to = clean(body.to, 40);
  if (from.length < 2 || to.length < 2) return json({ error: "invalid" }, 400);

  const order = {
    name: clean(body.name, 40) || null,
    phone: normalizePhone(body.phone) || null,
    kind: clean(body.kind, 30) || null,
    pay: clean(body.pay, 12) || null,
    notes: clean(body.notes, 300) || null,
    page: clean(body.page, 80) || null,
    source: sourceOf(clean(body.ref, 300), clean(body.q, 200)),
  };

  const hash = await ipHash(request, env.ADMIN_KEY || "");
  const recent = await env.DB.prepare(
    `SELECT COUNT(*) AS n,
            SUM(from_area = ? AND to_area = ? AND created_at > datetime('now', '-10 minutes')) AS dup
       FROM orders WHERE ip_hash = ? AND created_at > datetime('now', '-1 day')`
  ).bind(from, to, hash).first();
  if (recent.dup) return json({ ok: true, duplicate: true });
  if (recent.n >= MAX_PER_DAY) return json({ error: "limit" }, 429);

  await env.DB.prepare(
    `INSERT INTO orders (name, phone, from_area, to_area, kind, pay, notes, page, source, status, ip_hash)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(order.name, order.phone, from, to, order.kind, order.pay, order.notes, order.page, order.source, STATUS_NEW, hash).run();
  return json({ ok: true }, 201);
}
