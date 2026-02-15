CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE,
  full_name TEXT,
  ref_code TEXT,
  points INTEGER DEFAULT 0
);
