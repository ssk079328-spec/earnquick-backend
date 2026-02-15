CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0
);

CREATE TABLE withdrawals (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT,
    amount INTEGER,
    number TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
