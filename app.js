const API_URL = "https://your-backend-url.onrender.com"; // আপনার Render URL দিন

async function join() {
  const tgId = document.getElementById("tgId").value;
  const name = document.getElementById("name").value;
  if(!tgId || !name) return alert("All fields are required!");

  const res = await fetch(`${API_URL}/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id: tgId, name: name })
  });
  const data = await res.json();
  localStorage.setItem("user_id", tgId);
  document.getElementById("auth-box").style.display = "none";
  updateUI(data);
}

function watchAd() {
  const tgId = localStorage.getItem("user_id");
  if(!tgId) return alert("Please login first!");

  if (typeof show_10603687 === 'function') {
    show_10603687().then(async () => {
      const res = await fetch(`${API_URL}/watch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegram_id: tgId })
      });
      const data = await res.json();
      document.getElementById("balance-val").innerText = data.points;
      document.getElementById("inr-val").innerText = (data.points / 100).toFixed(2);
    });
  }
}

function showWithdraw() { document.getElementById("withdraw-modal").style.display = "block"; }
function closeModal() { document.getElementById("withdraw-modal").style.display = "none"; }

function updateUI(user) {
  document.getElementById("display-name").innerText = user.name;
  document.getElementById("balance-val").innerText = user.points;
  document.getElementById("inr-val").innerText = (user.points / 100).toFixed(2);
}
