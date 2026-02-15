/* ADMIN STATS */
app.get('/admin/stats', async (req, res) => {
  const totalUsers = await pool.query('SELECT COUNT(*) FROM users');
  const pendingPayments = await pool.query('SELECT COUNT(*) FROM users WHERE points >= 4000'); // উদাহরণ
  
  res.json({
    totalUsers: totalUsers.rows[0].count,
    pending: pendingPayments.rows[0].count,
    todayEarning: "₹500.00" // এটি আপনার অ্যাড নেটওয়ার্ক থেকে ম্যানুয়ালি বা API দিয়ে আনতে হবে
  });
});

/* GET USER FOR PROFILE */
app.get('/user/:id', async (req, res) => {
  const user = await pool.query('SELECT * FROM users WHERE telegram_id=$1', [req.params.id]);
  if(user.rows.length > 0) {
    res.json(user.rows[0]);
  } else {
    res.status(404).json({msg: "Not found"});
  }
});
