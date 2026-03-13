const tg = window.Telegram.WebApp;
tg.expand();

let userData = { id: '', name: '', points: 0, lastAdTime: 0 };

// লোড ইউজার ও রিয়েল-টাইম লিসেনার
async function initApp() {
    const user = tg.initDataUnsafe?.user;
    userData.id = user ? user.id.toString() : "test_123";
    userData.name = user ? user.first_name : "Nazmul Forhad";

    const userRef = db.ref('users/' + userData.id);

    // রিয়েল-টাইম লিসেনার: ডাটাবেসে পয়েন্ট বাড়লে অটোমেটিক স্ক্রিনে আপডেট হবে
    userRef.on('value', (snapshot) => {
        if (snapshot.exists()) {
            userData = snapshot.val();
            updateUI();
        } else {
            // নতুন ইউজার হলে ডাটাবেসে এন্ট্রি
            userRef.set({
                id: userData.id,
                name: userData.name,
                points: 50, // জয়েন বোনাস ৫০ টাকা (পয়েন্ট হিসেবে)
                totalViews: 0,
                lastAdTime: 0
            });
        }
    });
}

function updateUI() {
    document.getElementById('userName').textContent = userData.name;
    document.getElementById('avatarLetter').textContent = userData.name.charAt(0).toUpperCase();
    document.getElementById('balance').textContent = (userData.points).toFixed(2);
    // যদি আপনার ১ পয়েন্ট = ১ টাকা হয়, তবে সরাসরি লিখবেন।
}

// বিজ্ঞাপন দেখার ফাংশন
async function watchAd() {
    if (typeof show_10603637 === 'function') {
        show_10603637().then(() => {
            db.ref('users/' + userData.id).update({
                points: userData.points + 10,
                lastAdTime: Date.now()
            });
            alert("অভিনন্দন! ১০ টাকা যুক্ত হয়েছে।");
        });
    } else {
        alert("অ্যাড লোড হচ্ছে, কিছুক্ষণ পর চেষ্টা করুন।");
    }
}

// টাস্ক ক্লেইম ফাংশন
function claimTask(amount) {
    db.ref('users/' + userData.id).update({
        points: userData.points + amount
    });
    alert(amount + " টাকা আপনার ব্যালেন্সে যুক্ত হয়েছে!");
}

window.onload = initApp;
