// Admin orders API (X-Admin-Key header).
// GET  /api/admin/orders?status=new|done|cancelled|all&q=...  -> latest orders
// GET  /api/admin/orders?view=customers                        -> customers grouped by phone
// POST /api/admin/orders {id, action}                           -> action: new | done | cancelled | delete
import { json, authorized, clean } from "../../../lib/common.js";

const STATUSES = new Set(["new", "done", "cancelled"]);

export async function onRequest({ request, env }) {
  if (!(await authorized(request, env))) return json({ error: "unauthorized" }, 401);

  if (request.method === "GET") {
    const params = new URL(request.url).searchParams;
    if (params.get("view") === "customers") {
      const { results } = await env.DB.prepare(
        `SELECT phone, COUNT(*) AS orders, MIN(created_at) AS first, MAX(created_at) AS last,
                SUM(status = 'done') AS done,
                GROUP_CONCAT(DISTINCT kind) AS kinds, GROUP_CONCAT(DISTINCT from_area) AS areas,
                (SELECT name FROM orders o2 WHERE o2.phone = o.phone AND o2.name IS NOT NULL
                  ORDER BY o2.created_at DESC LIMIT 1) AS name
           FROM orders o WHERE phone IS NOT NULL
          GROUP BY phone ORDER BY orders DESC, last DESC LIMIT 500`
      ).all();
      const { n } = await env.DB.prepare("SELECT COUNT(*) AS n FROM orders WHERE phone IS NULL").first();
      return json({ customers: results, withoutPhone: n });
    }

    const status = params.get("status");
    const q = clean(params.get("q") || "", 40);
    const where = [];
    const binds = [];
    if (STATUSES.has(status)) { where.push("status = ?"); binds.push(status); }
    if (q) {
      where.push("(name LIKE ? OR phone LIKE ? OR from_area LIKE ? OR to_area LIKE ? OR notes LIKE ?)");
      binds.push(...Array(5).fill(`%${q}%`));
    }
    const { results } = await env.DB.prepare(
      `SELECT id, created_at, name, phone, from_area, to_area, kind, pay, notes, page, source, status
         FROM orders ${where.length ? "WHERE " + where.join(" AND ") : ""}
        ORDER BY created_at DESC LIMIT 300`
    ).bind(...binds).all();
    return json({ orders: results });
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
    if (STATUSES.has(body.action)) {
      await env.DB.prepare("UPDATE orders SET status = ? WHERE id = ?").bind(body.action, id).run();
    } else if (body.action === "delete") {
      await env.DB.prepare("DELETE FROM orders WHERE id = ?").bind(id).run();
    } else {
      return json({ error: "invalid" }, 400);
    }
    return json({ ok: true });
  }

  return json({ error: "method" }, 405);
}
