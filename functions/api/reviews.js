// Public reviews API.
// GET  /api/reviews  -> latest approved reviews
// POST /api/reviews  -> submit a review (stored as pending until approved in /admin)

const MAX_PER_DAY = 3;

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const clean = (v, max) => (typeof v === "string" ? v.replace(/\s+/g, " ").trim().slice(0, max) : "");

async function ipHash(request, secret) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip + secret));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    "SELECT name, area, rating, comment, created_at FROM reviews WHERE approved = 1 ORDER BY created_at DESC LIMIT 30"
  ).all();
  return json({ reviews: results });
}

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid" }, 400);
  }
  // Honeypot: real visitors never fill this hidden field.
  if (clean(body.website, 100)) return json({ ok: true });

  const name = clean(body.name, 40);
  const area = clean(body.area, 40);
  const comment = clean(body.comment, 500);
  const rating = Number(body.rating);
  if (name.length < 2 || comment.length < 10 || !Number.isInteger(rating) || rating < 1 || rating > 5) {
    return json({ error: "invalid" }, 400);
  }

  const hash = await ipHash(request, env.ADMIN_KEY || "");
  const { n } = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM reviews WHERE ip_hash = ? AND created_at > datetime('now', '-1 day')"
  ).bind(hash).first();
  if (n >= MAX_PER_DAY) return json({ error: "limit" }, 429);

  await env.DB.prepare("INSERT INTO reviews (name, area, rating, comment, ip_hash) VALUES (?, ?, ?, ?, ?)")
    .bind(name, area || null, rating, comment, hash)
    .run();
  return json({ ok: true }, 201);
}
