// POST /api/track -> record a page view or a contact click, without cookies.
// Body (sent with navigator.sendBeacon as text): {t, p, r, q}
import { clean, sha256Hex, isBot, sourceOf } from "../../lib/common.js";

const TYPES = new Set(["view", "wa", "call", "ig"]);
const noContent = () => new Response(null, { status: 204, headers: { "cache-control": "no-store" } });

export async function onRequestPost({ request, env, waitUntil }) {
  const ua = request.headers.get("User-Agent") || "";
  if (isBot(ua)) return noContent();
  let body;
  try {
    body = JSON.parse(await request.text());
  } catch {
    return noContent();
  }
  const type = TYPES.has(body.t) ? body.t : null;
  if (!type) return noContent();

  const day = new Date().toISOString().slice(0, 10);
  const ip = request.headers.get("CF-Connecting-IP") || "";
  // Rotates daily, so a visitor can be counted per day but not followed over time.
  const visitor = (await sha256Hex(ip + ua + day + (env.ADMIN_KEY || ""))).slice(0, 16);
  const device = /iPad|Tablet/i.test(ua) ? "tablet" : /Mobi|Android|iPhone/i.test(ua) ? "mobile" : "desktop";

  waitUntil(
    env.DB.prepare("INSERT INTO events (type, path, source, device, country, visitor) VALUES (?, ?, ?, ?, ?, ?)")
      .bind(type, clean(body.p, 100) || "/", sourceOf(clean(body.r, 300), clean(body.q, 200)), device,
        (request.cf && request.cf.country) || null, visitor)
      .run()
      .then(() => Math.random() < 0.01
        ? env.DB.prepare("DELETE FROM events WHERE created_at < datetime('now', '-400 days')").run()
        : null)
  );
  return noContent();
}
