// Shared helpers for the Pages Functions (bundled into each function at deploy time).

export const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export const clean = (v, max) => (typeof v === "string" ? v.replace(/\s+/g, " ").trim().slice(0, max) : "");

export async function sha256Hex(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export const ipHash = (request, secret) =>
  sha256Hex((request.headers.get("CF-Connecting-IP") || "unknown") + secret);

export const isBot = (ua) =>
  !ua || /bot|crawl|spider|slurp|preview|headless|lighthouse|pagespeed|facebookexternalhit|whatsapp|curl|wget|python|node-fetch/i.test(ua);

// Where a visit came from: utm_source wins, then the referrer host.
export function sourceOf(referrer, search) {
  const utm = /(?:^|[?&])utm_source=([^&]+)/.exec(search || "");
  if (utm) return decodeURIComponent(utm[1]).toLowerCase().slice(0, 30);
  let host = "";
  try { host = new URL(referrer).hostname.replace(/^www\./, ""); } catch { return "direct"; }
  const rules = [
    [/deliverykw\.com$|delivery-kw\.pages\.dev$/, "internal"],
    [/gemini\.google|claude\.ai$/, "ai"],
    [/google\./, "google"], [/bing\.com$/, "bing"], [/yahoo\./, "yahoo"], [/duckduckgo/, "duckduckgo"],
    [/instagram\.com$/, "instagram"], [/facebook\.com$|fb\.com$|fb\.me$/, "facebook"],
    [/whatsapp|wa\.me$/, "whatsapp"], [/t\.co$|twitter\.com$|x\.com$/, "x"], [/tiktok/, "tiktok"],
    [/snapchat/, "snapchat"], [/chatgpt\.com$|openai\.com$/, "chatgpt"], [/perplexity/, "perplexity"],
  ];
  for (const [re, name] of rules) if (re.test(host)) return name;
  return host.slice(0, 40) || "direct";
}

export async function authorized(request, env) {
  const given = request.headers.get("X-Admin-Key") || "";
  const expected = env.ADMIN_KEY || "";
  if (!expected || given.length !== expected.length) return false;
  const [a, b] = await Promise.all([sha256Hex(given), sha256Hex(expected)]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
