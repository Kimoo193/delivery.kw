// Admin reviews API, protected by the ADMIN_KEY secret sent in the X-Admin-Key header.
// GET  /api/admin/reviews                       -> pending + recent approved reviews
// POST /api/admin/reviews {id, action}          -> action: "approve" | "delete"
import { json, authorized } from "../../../lib/common.js";

export async function onRequest({ request, env }) {
  if (!(await authorized(request, env))) return json({ error: "unauthorized" }, 401);

  if (request.method === "GET") {
    const { results } = await env.DB.prepare(
      "SELECT id, name, area, rating, comment, created_at, approved FROM reviews ORDER BY approved ASC, created_at DESC LIMIT 100"
    ).all();
    return json({ reviews: results });
  }

  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid" }, 400);
    }
    const id = Number(body.id);
    if (!Number.isInteger(id)) return json({ error: "invalid" }, 400);
    if (body.action === "approve") {
      await env.DB.prepare("UPDATE reviews SET approved = 1 WHERE id = ?").bind(id).run();
    } else if (body.action === "delete") {
      await env.DB.prepare("DELETE FROM reviews WHERE id = ?").bind(id).run();
    } else {
      return json({ error: "invalid" }, 400);
    }
    return json({ ok: true });
  }

  return json({ error: "method" }, 405);
}
