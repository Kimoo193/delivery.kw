// Simulates many visitors opening the site at the same time.
// Each "visitor" loads the page and every image on it, like a real browser.
//
// Usage: node scripts/loadtest.mjs <url> [visitors] [seconds]
// Example: node scripts/loadtest.mjs https://delivery-kw.pages.dev 200 30
//
// Only run this against your own site.

const [url, visitorsArg = '100', secondsArg = '30'] = process.argv.slice(2);
if (!url) {
  console.error('Usage: node scripts/loadtest.mjs <url> [visitors] [seconds]');
  process.exit(1);
}
const visitors = Number(visitorsArg);
const seconds = Number(secondsArg);
const base = url.endsWith('/') ? url : url + '/';

const html = await (await fetch(base)).text();
const assets = [...new Set([...html.matchAll(/(?:src|href)="(assets\/[^"]+)"/g)].map(m => m[1]))];
const files = ['', ...assets].map(p => new URL(p, base).href);
console.log(`Page + ${assets.length} files per visit, ${visitors} visitors at once, ${seconds}s\n`);

const times = [];
let visits = 0, failedVisits = 0, requests = 0, failedRequests = 0, bytes = 0;
const errors = new Map();
const end = Date.now() + seconds * 1000;

async function visit() {
  const start = performance.now();
  let ok = true;
  await Promise.all(files.map(async f => {
    requests++;
    try {
      const res = await fetch(f, { headers: { 'cache-control': 'no-cache' } });
      const buf = await res.arrayBuffer();
      bytes += buf.byteLength;
      if (!res.ok) { ok = false; failedRequests++; errors.set(res.status, (errors.get(res.status) || 0) + 1); }
    } catch (e) {
      ok = false; failedRequests++;
      const k = e.cause?.code || e.message;
      errors.set(k, (errors.get(k) || 0) + 1);
    }
  }));
  visits++;
  if (ok) times.push(performance.now() - start); else failedVisits++;
}

async function visitor() { while (Date.now() < end) await visit(); }

const t0 = Date.now();
await Promise.all(Array.from({ length: visitors }, visitor));
const elapsed = (Date.now() - t0) / 1000;

times.sort((a, b) => a - b);
const pct = p => times.length ? Math.round(times[Math.min(times.length - 1, Math.floor(times.length * p))]) : 0;
console.log(`Visits completed : ${visits} (${(visits / elapsed).toFixed(1)} per second)`);
console.log(`Failed visits    : ${failedVisits} (${visits ? (100 * failedVisits / visits).toFixed(2) : 0}%)`);
console.log(`Requests         : ${requests}, failed ${failedRequests}`);
console.log(`Data transferred : ${(bytes / 1e6).toFixed(1)} MB`);
console.log(`Full page load   : median ${pct(0.5)} ms, 95% ${pct(0.95)} ms, slowest ${pct(1)} ms`);
if (errors.size) console.log('Errors           :', Object.fromEntries(errors));
