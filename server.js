const express = require("express");
const cors = require("cors");
const db = require("./db");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json());

/* USER JOIN */
app.post("/join", async (req, res) => {
  const { telegram_id, name } = req.body;

  const user = await db.query(
    "INSERT INTO users (telegram_id, full_name, ref_code) VALUES ($1,$2,$3) RETURNING *",
    [telegram_id, name, "REF" + telegram_id]
  );

  res.json(user.rows[0]);
});

/* WATCH AD */
app.post("/ad", async (req, res) => {
  const { telegram_id } = req.body;

  await db.query(
    "UPDATE users SET points = points + 5 WHERE telegram_id=$1",
    [telegram_id]
  );

  res.json({ msg: "5 Points Added" });
});

/* WITHDRAW */
app.post("/withdraw", async (req, res) => {
  const { telegram_id } = req.body;

  const u = await db.query(
    "SELECT * FROM users WHERE telegram_id=$1",
    [telegram_id]
  );

  if (u.rows[0].points < 4000)
    return res.send("Minimum 4000 points needed");

  await db.query(
    "UPDATE users SET points=0 WHERE telegram_id=$1",
    [telegram_id]
  );

  res.send("Withdraw Requested");
});

app.listen(process.env.PORT, () =>
  console.log("Server Running")
);
