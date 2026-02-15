const API = "https://earnquick-backend.onrender.com"; // Render URL দেবে

function join() {
  const telegram_id = document.getElementById("tgId").value;
  const name = document.getElementById("name").value;

  fetch(API + "/join", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id, name })
  })
  .then(r => r.json())
  .then(d => show("Joined"));
}

function watchAd() {
  const telegram_id = document.getElementById("tgId").value;

  fetch(API + "/ad", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id })
  })
  .then(r => r.json())
  .then(d => show(d.msg));
}

function withdraw() {
  const telegram_id = document.getElementById("tgId").value;

  fetch(API + "/withdraw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id })
  })
  .then(r => r.text())
  .then(d => show(d));
}

function show(text) {
  document.getElementById("msg").innerText = text;
}
