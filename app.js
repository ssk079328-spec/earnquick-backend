// ===== BACKEND URL =====
const API = "https://earnquick-backend.onrender.com";

// ===== TELEGRAM WEB APP =====
let telegram_id = "";
let name = "";

if (window.Telegram && window.Telegram.WebApp) {
  const tg = window.Telegram.WebApp;
  tg.expand();

  const user = tg.initDataUnsafe.user;

  if (user) {
    telegram_id = user.id;
    name = user.first_name || "User";

    document.getElementById("tgId").value = telegram_id;
    document.getElementById("name").value = name;
  }
}

// ===== JOIN USER =====
function join() {
  if (!telegram_id) {
    telegram_id = document.getElementById("tgId").value;
    name = document.getElementById("name").value;
  }

  fetch(API + "/join", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id, name })
  })
  .then(res => res.json())
  .then(data => show(data.msg || "Joined"))
  .catch(() => show("Server Error"));
}

// ===== WATCH AD =====
function watchAd() {
  if (!telegram_id) {
    show("Join First");
    return;
  }

  fetch(API + "/ad", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id })
  })
  .then(res => res.json())
  .then(data => show(data.msg || "+5 Points"))
  .catch(() => show("Server Error"));
}

// ===== WITHDRAW =====
function withdraw() {
  if (!telegram_id) {
    show("Join First");
    return;
  }

  fetch(API + "/withdraw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id })
  })
  .then(res => res.text())
  .then(data => show(data))
  .catch(() => show("Server Error"));
}

// ===== MESSAGE SHOW =====
function show(text) {
  alert(text);
}
