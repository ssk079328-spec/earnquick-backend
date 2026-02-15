const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// DATABASE CONNECTION (Neon / PostgreSQL)
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false
  }
});

// ROOT ROUTE
app.get('/', (req, res) => {
  res.send('EarnQuick Backend Running');
});

// JOIN USER
app.post('/join', async (req, res) => {
  try {
    const { telegram_id, name, ref_code } = req.body;

    const checkUser = await pool.query(
      'SELECT * FROM users WHERE telegram_id=$1',
      [telegram_id]
    );

    if (checkUser.rows.length > 0) {
      return res.json({ message: 'User Already Exists' });
    }

    const myRef = 'EQ' + Math.floor(Math.random() * 100000);

    await pool.query(
      'INSERT INTO users (telegram_id, name, ref_code, points) VALUES ($1,$2,$3,$4)',
      [telegram_id, name, myRef, 0]
    );

    // Referral Bonus
    if (ref_code) {
      const refUser = await pool.query(
        'SELECT * FROM users WHERE ref_code=$1',
        [ref_code]
      );

      if (refUser.rows.length > 0) {
        await pool.query(
          'UPDATE users SET points = points + 100 WHERE ref_code=$1',
          [ref_code]
        );
      }
    }

    res.json({ message: 'Joined Successfully', ref: myRef });

  } catch (err) {
    console.log(err);
    res.status(500).send('Error');
  }
});

// WATCH AD (+5 POINT)
app.post('/watch', async (req, res) => {
  try {
    const { telegram_id } = req.body;

    await pool.query(
      'UPDATE users SET points = points + 5 WHERE telegram_id=$1',
      [telegram_id]
    );

    res.json({ message: 'Points Added +5' });
  } catch (err) {
    res.status(500).send('Error');
  }
});

// WITHDRAW
app.post('/withdraw', async (req, res) => {
  try {
    const { telegram_id } = req.body;

    const user = await pool.query(
      'SELECT points FROM users WHERE telegram_id=$1',
      [telegram_id]
    );

    if (user.rows.length === 0) {
      return res.json({ message: 'User Not Found' });
    }

    const points = user.rows[0].points;

    if (points < 4000) {
      return res.json({ message: 'Minimum 4000 Points Needed' });
    }

    await pool.query(
      'UPDATE users SET points = points - 4000 WHERE telegram_id=$1',
      [telegram_id]
    );

    res.json({ message: 'Withdraw Request Sent' });

  } catch (err) {
    res.status(500).send('Error');
  }
});

// PORT
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log('Server Running on ' + PORT);
});
