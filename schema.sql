-- D1 schema for deliverykw-reviews (binding DB). Safe to re-run.
-- Apply: npx wrangler d1 execute deliverykw-reviews --remote --file schema.sql

CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, area TEXT, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), comment TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')), approved INTEGER NOT NULL DEFAULT 0, ip_hash TEXT);
CREATE INDEX IF NOT EXISTS idx_reviews_approved ON reviews(approved, created_at);
CREATE INDEX IF NOT EXISTS idx_reviews_ip ON reviews(ip_hash, created_at);

-- Orders prepared in the site form (saved just before WhatsApp opens).
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  name TEXT,
  phone TEXT,
  from_area TEXT NOT NULL,
  to_area TEXT NOT NULL,
  kind TEXT,
  pay TEXT,
  notes TEXT,
  page TEXT,
  source TEXT,
  status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','done','cancelled')),
  ip_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_phone ON orders(phone);
CREATE INDEX IF NOT EXISTS idx_orders_ip ON orders(ip_hash, created_at);

-- Cookie-free visit and click events. visitor is a daily-rotating hash, not a person id.
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  type TEXT NOT NULL,
  path TEXT,
  source TEXT,
  device TEXT,
  country TEXT,
  visitor TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at, type);
