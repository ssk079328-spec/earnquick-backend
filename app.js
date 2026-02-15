const tg = window.Telegram.WebApp;
tg.expand();

const API_URL = "https://your-backend-url.onrender.com";
let userData = tg.initDataUnsafe.user;

async function autoRegister() {
    if (!userData) {
        alert("টেলিগ্রাম থেকে অ্যাপটি ওপেন করুন!");
        return;
    }

    const res = await fetch(`${API_URL}/user/${userData.id}`);
    if (res.status === 404) {
        // নতুন ইউজার হলে রেফার কোড অপশন দেখাবে
        document.getElementById("refer-overlay").style.display = "flex";
    } else {
        const data = await res.json();
        updateUI(data);
    }
}

async function completeRegistration() {
    const refCode = document.getElementById("ref-input").value;
    const res = await fetch(`${API_URL}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            telegram_id: userData.id,
            name: userData.first_name + " " + (userData.last_name || ""),
            referred_by: refCode
        })
    });
    const data = await res.json();
    document.getElementById("refer-overlay").style.display = "none";
    updateUI(data);
}

function updateUI(data) {
    document.getElementById("user-name").innerText = data.name;
    document.getElementById("balance-val").innerText = data.points;
    document.getElementById("refer-count").innerText = data.refer_count || 0;
    document.getElementById("tg-display-id").innerText = "ID: " + data.telegram_id;
}

autoRegister();
