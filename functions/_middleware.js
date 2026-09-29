// Permanently redirect the old Cloudflare Pages address to the real domain, so Google
// moves the old delivery-kw.pages.dev search result over to deliverykw.com.
// The Search Console verification file stays reachable for the Change of Address tool.
const OLD_HOST = "delivery-kw.pages.dev";
const NEW_ORIGIN = "https://deliverykw.com";
const KEEP_PATHS = new Set(["/google73f6d10659cad8c2.html", "/google73f6d10659cad8c2"]);

export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === OLD_HOST && !KEEP_PATHS.has(url.pathname)) {
    return Response.redirect(NEW_ORIGIN + url.pathname + url.search, 301);
  }
  return next();
}
