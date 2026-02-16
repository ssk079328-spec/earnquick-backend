// Telegram WebApp init
let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Admin ID
const ADMIN_IDS = ['8145444675'];

// Firebase DB
const FIREBASE_DB_URL = 'https://earnbotdb-default-rtdb.asia-southeast1.firebasedatabase.app/';

let userData = {
    id: '',
    name: '',
    points: 0,
    totalViews: 0,
    referrals: 0
};

// Init
function initApp() {
    if (tg.initDataUnsafe?.user) {
        const user = tg.initDataUnsafe.user;
        userData.id = user.id.toString();
        userData.name = user.first_name + (user.last_name ? ' ' + user.last_name : '');
    } else {
        userData.id = 'local_' + Date.now();
        userData.name = 'Local User';
    }

    updateUI();
    checkAdminAccess();
    setupReferral();
    saveUserToDB();
}

// UI Update
function updateUI() {
    document.getElementById('userName').textContent = userData.name;
    document.getElementById('userId').textContent = userData.id;
    document.getElementById('tokenDisplay').textContent = userData.points;
}

// Admin Button
function checkAdminAccess() {
    const adminBtn = document.getElementById('adminBtn');
    if (ADMIN_IDS.includes(userData.id)) {
        adminBtn.style.display = 'block';
        adminBtn.addEventListener('click', () => {
            window.location.href = 'admin/index.html';
        });
    } else {
        adminBtn.style.display = 'none';
    }
}

// Referral
function setupReferral() {
    const url = new URL(window.location.href);
    const ref = url.searchParams.get('ref');
    if (ref && ref !== userData.id) {
        // Increment referral for the referred user
        fetch(`${FIREBASE_DB_URL}/users/${ref}.json`)
        .then(res => res.json())
        .then(data => {
            const points = (data?.points || 0) + 10;
            fetch(`${FIREBASE_DB_URL}/users/${ref}.json`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({points})
            });
        });
    }
    document.getElementById('refLink').textContent = `${window.location.href}?ref=${userData.id}`;
}

// Save/Update user to Firebase
function saveUserToDB() {
    fetch(`${FIREBASE_DB_URL}/users/${userData.id}.json`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(userData)
    });
}

// Watch Ad Simulation
document.getElementById('watchAdBtn').addEventListener('click', () => {
    userData.points += 5;
    userData.totalViews += 1;
    updateUI();
    saveUserToDB();
    alert('+5 পয়েন্ট!');
});

// Withdraw
document.getElementById('withdrawBtn').addEventListener('click', () => {
    const amount = parseInt(document.getElementById('withdrawAmount').value);
    if (amount <= 0 || amount > userData.points) {
        alert('সঠিক পরিমাণ লিখুন!');
        return;
    }
    userData.points -= amount;
    saveUserToDB();
    updateUI();
    alert(`আপনার ${amount} টাকা উইথড্রাল রিকোয়েস্ট করা হয়েছে।`);
});

// Start App
initApp();
