const FIREBASE_DB_URL = 'https://earnbotdb-default-rtdb.asia-southeast1.firebasedatabase.app/';
const ADMIN_IDS = ['8145444675'];

let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const userId = tg.initDataUnsafe?.user?.id?.toString() || '';

if (!ADMIN_IDS.includes(userId)) {
    document.body.innerHTML = '<h2>Access Denied</h2>';
} else {
    fetch(`${FIREBASE_DB_URL}/users.json`)
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('userList');
        if (!data) {
            container.innerHTML = 'No users yet';
            return;
        }
        container.innerHTML = '';
        Object.keys(data).forEach(uid => {
            const user = data[uid];
            const div = document.createElement('div');
            div.innerHTML = `<strong>${user.name || uid}</strong> - Points: ${user.points || 0} - Total Views: ${user.totalViews || 0} - Referrals: ${user.referrals || 0}`;
            container.appendChild(div);
        });
    })
    .catch(err => {
        console.error(err);
        document.getElementById('userList').innerHTML = 'Error loading users';
    });
}
