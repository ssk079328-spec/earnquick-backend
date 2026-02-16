const tg = window.Telegram.WebApp;
tg.expand();
const API_URL = "https://your-backend-url.onrender.com";

async function autoLogin() {
    const user = tg.initDataUnsafe.user;
    if (!user) return alert("টেলিগ্রাম থেকে ওপেন করুন!");

    const res = await fetch(`${API_URL}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            telegram_id: user.id,
            name: user.first_name + " " + (user.last_name || "")
        })
    });
    const data = await res.json();
    updateUI(data);
}

function watchAd() {
    if (typeof show_10615270 === 'function') {
        show_10615270().then(async () => {
            const res = await fetch(`${API_URL}/watch`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ telegram_id: tg.initDataUnsafe.user.id })
            });
            const data = await res.json();
            document.getElementById("balance-val").innerText = data.points;
        });
    }
}

function showWithdraw() { document.getElementById("withdraw-modal").style.display = "flex"; }
function closeModal() { document.getElementById("withdraw-modal").style.display = "none"; }

function updateUI(data) {
    document.getElementById("user-name").innerText = data.name;
    document.getElementById("balance-val").innerText = data.points;
    document.getElementById("refer-count").innerText = data.refer_count || 0;
    document.getElementById("tg-display-id").innerText = "ID: " + data.telegram_id;
}

autoLogin();
