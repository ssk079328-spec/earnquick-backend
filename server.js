const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const app = express();

app.use(cors());
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// Join/Register
app.post('/join', async (req, res) => {
  const { telegram_id, name } = req.body;
  try {
    const exist = await pool.query('SELECT * FROM users WHERE telegram_id=$1', [telegram_id]);
    if (exist.rows.length) return res.json(exist.rows[0]);
    const newUser = await pool.query('INSERT INTO users (telegram_id, name, points) VALUES ($1,$2,0) RETURNING *', [telegram_id, name]);
    res.json(newUser.rows[0]);
  } catch (err) { res.status(500).json(err); }
});

// Update Points (Watch Ad)
app.post('/watch', async (req, res) => {
  const { telegram_id } = req.body;
  const result = await pool.query('UPDATE users SET points=points+5 WHERE telegram_id=$1 RETURNING points', [telegram_id]);
  res.json({ points: result.rows[0].points });
});

// Withdraw Request
app.post('/withdraw', async (req, res) => {
  const { telegram_id, amount, number } = req.body;
  const user = await pool.query('SELECT points FROM users WHERE telegram_id=$1', [telegram_id]);
  if (user.rows[0].points < amount) return res.status(400).json({ msg: "Insufficient Points" });
  
  await pool.query('UPDATE users SET points=points-$1 WHERE telegram_id=$2', [amount, telegram_id]);
  await pool.query('INSERT INTO withdrawals (telegram_id, amount, number, status) VALUES ($1,$2,$3,$4)', [telegram_id, amount, number, 'pending']);
  res.json({ msg: "Withdrawal Request Sent!" });
});

// Admin Stats
app.get('/admin/stats', async (req, res) => {
  const total = await pool.query('SELECT COUNT(*) FROM users');
  const pending = await pool.query("SELECT COUNT(*) FROM withdrawals WHERE status='pending'");
  res.json({ totalUsers: total.rows[0].count, pending: pending.rows[0].count });
});

app.listen(process.env.PORT || 3000);
