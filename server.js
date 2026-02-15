const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(cors());
app.use(express.json());

/* DATABASE */
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

/* ROOT */
app.get('/', (req, res) => {
  res.send('EarnQuick Backend Running');
});

/* JOIN */
app.post('/join', async (req, res) => {
  const { telegram_id, name } = req.body;

  const exist = await pool.query(
    'SELECT * FROM users WHERE telegram_id=$1',
    [telegram_id]
  );

  if (exist.rows.length)
    return res.json({ msg: 'Already Joined' });

  await pool.query(
    'INSERT INTO users (telegram_id, name, points) VALUES ($1,$2,0)',
    [telegram_id, name]
  );

  res.json({ msg: 'Joined' });
});

/* WATCH AD */
app.post('/watch', async (req, res) => {
  const { telegram_id } = req.body;

  await pool.query(
    'UPDATE users SET points=points+5 WHERE telegram_id=$1',
    [telegram_id]
  );

  res.json({ msg: '+5 Points' });
});

/* WITHDRAW */
app.post('/withdraw', async (req, res) => {
  const { telegram_id } = req.body;

  const u = await pool.query(
    'SELECT points FROM users WHERE telegram_id=$1',
    [telegram_id]
  );

  if (!u.rows.length)
    return res.json({ msg: 'User Not Found' });

  if (u.rows[0].points < 4000)
    return res.json({ msg: 'Need 4000 Points' });

  await pool.query(
    'UPDATE users SET points=points-4000 WHERE telegram_id=$1',
    [telegram_id]
  );

  res.json({ msg: 'Withdraw Requested' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('Server Running'));
