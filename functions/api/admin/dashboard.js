// GET /api/admin/dashboard?days=30 -> order and visitor statistics for the admin page.
// Dates are grouped in Kuwait time (UTC+3).
import { json, authorized } from "../../../lib/common.js";

const KW = "'+3 hours'";

export async function onRequestGet({ request, env }) {
  if (!(await authorized(request, env))) return json({ error: "unauthorized" }, 401);
  const days = Math.min(Math.max(parseInt(new URL(request.url).searchParams.get("days"), 10) || 30, 1), 365);
  const since = `datetime('now', '-${days} days')`;
  const top = (col, table, where = "1", limit = 10) =>
    `SELECT COALESCE(${col}, '—') AS k, COUNT(*) AS n FROM ${table} WHERE created_at > ${since} AND ${where} GROUP BY k ORDER BY n DESC LIMIT ${limit}`;

  const queries = {
    orderTotals: `SELECT COUNT(*) AS orders, COUNT(DISTINCT phone) AS customers,
        SUM(status = 'new') AS open, SUM(status = 'done') AS done, SUM(status = 'cancelled') AS cancelled
        FROM orders WHERE created_at > ${since}`,
    ordersByDay: `SELECT date(created_at, ${KW}) AS k, COUNT(*) AS n FROM orders WHERE created_at > ${since} GROUP BY k ORDER BY k`,
    orderHours: `SELECT CAST(strftime('%H', created_at, ${KW}) AS INTEGER) AS k, COUNT(*) AS n FROM orders WHERE created_at > ${since} GROUP BY k ORDER BY k`,
    kinds: top("kind", "orders"),
    pays: top("pay", "orders"),
    fromAreas: top("from_area", "orders"),
    toAreas: top("to_area", "orders"),
    routes: top("from_area || ' ← ' || to_area", "orders"),
    orderSources: top("source", "orders"),
    eventTotals: `SELECT SUM(type = 'view') AS views,
        COUNT(DISTINCT CASE WHEN type = 'view' THEN visitor || date(created_at) END) AS visitors,
        SUM(type = 'wa') AS wa, SUM(type = 'call') AS calls, SUM(type = 'ig') AS ig
        FROM events WHERE created_at > ${since}`,
    visitsByDay: `SELECT date(created_at, ${KW}) AS k, SUM(type = 'view') AS n,
        COUNT(DISTINCT CASE WHEN type = 'view' THEN visitor END) AS v
        FROM events WHERE created_at > ${since} GROUP BY k ORDER BY k`,
    sources: top("source", "events", "type = 'view' AND source != 'internal'", 12),
    pages: top("path", "events", "type = 'view'", 12),
    devices: top("device", "events", "type = 'view'"),
    countries: top("country", "events", "type = 'view'"),
  };

  const names = Object.keys(queries);
  const results = await env.DB.batch(names.map((n) => env.DB.prepare(queries[n])));
  const out = { days };
  names.forEach((n, i) => {
    const rows = results[i].results;
    out[n] = n.endsWith("Totals") ? rows[0] || {} : rows;
  });
  return json(out);
}
