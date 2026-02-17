// ========== Initialize ==========
const tg = Telegram.WebApp;
tg.expand();
tg.ready();

// User Data
let userData = {
    id: '',
    name: '',
    points: 0,
    totalViews: 0,
    referrals: { level1: 0, level2: 0, level3: 0 },
    lastAdTime: 0
};

let currentMethod = '';

// ========== Load User ==========
async function loadUser() {
    try {
        if (tg.initDataUnsafe?.user) {
            const user = tg.initDataUnsafe.user;
            userData.id = user.id.toString();
            userData.name = user.first_name + (user.last_name ? ' ' + user.last_name : '');
            
            if (user.photo_url) {
                document.getElementById('profileImage').src = user.photo_url;
                document.getElementById('profileImage').style.display = 'block';
                document.getElementById('profileAvatar').style.display = 'none';
            } else {
                document.getElementById('profileAvatar').textContent = userData.name.charAt(0).toUpperCase();
            }
        } else {
            userData.id = 'local_' + Date.now();
            userData.name = 'Local User';
        }

        const snapshot = await db.ref('users/' + userData.id).once('value');
        if (snapshot.exists()) {
            userData = { ...userData, ...snapshot.val() };
        } else {
            await db.ref('users/' + userData.id).set(userData);
        }

        updateUI();
        checkTimer();

        db.ref('users/' + userData.id).on('value', (snap) => {
            if (snap.exists()) {
                userData = snap.val();
                updateUI();
            }
        });

    } catch (error) {
        showMessage('ডাটা লোড করতে সমস্যা', 'error');
    }
}

// ========== Update UI ==========
function updateUI() {
    document.getElementById('userName').textContent = userData.name;
    document.getElementById('userId').textContent = 'ID: ' + userData.id;
    
    document.getElementById('balanceAmount').textContent = '৳' + (userData.points / 200).toFixed(2);
    document.getElementById('balancePoints').textContent = userData.points + ' পয়েন্ট';
    
    document.getElementById('totalViews').textContent = userData.totalViews;
    document.getElementById('totalRefers').textContent = userData.referrals.level1;
    document.getElementById('totalEarned').textContent = '৳' + (userData.points / 200).toFixed(2);
    
    document.getElementById('level1Count').textContent = userData.referrals.level1;
    document.getElementById('level2Count').textContent = userData.referrals.level2;
    document.getElementById('level3Count').textContent = userData.referrals.level3;
    
    document.getElementById('referralLink').textContent = generateReferralLink();
}

// ========== Check Timer ==========
function checkTimer() {
    const now = Date.now();
    const lastAd = userData.lastAdTime || 0;
    const timeLeft = 30 - Math.floor((now - lastAd) / 1000);
    
    const btn = document.getElementById('watchAdBtn');
    
    if (timeLeft > 0 && timeLeft < 30) {
        btn.classList.add('disabled');
        btn.disabled = true;
        btn.innerHTML = `<i class="fas fa-hourglass-half"></i> অপেক্ষা করুন (${timeLeft}s)`;
        setTimeout(checkTimer, 1000);
    } else {
        btn.classList.remove('disabled');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-play-circle"></i> অ্যাড দেখুন (৫ পয়েন্ট)';
    }
}

// ========== Watch Ad ==========
async function watchRewardedAd() {
    const btn = document.getElementById('watchAdBtn');
    
    showMessage('অ্যাড লোড হচ্ছে...', 'info');
    
    try {
        if (typeof show_10603637 === 'function') {
            const event = await show_10603637();
            
            if (event && event.reward_event_type === 'valued') {
                userData.points += 5;
                userData.totalViews += 1;
                userData.lastAdTime = Date.now();
                
                await db.ref('users/' + userData.id).update({
                    points: userData.points,
                    totalViews: userData.totalViews,
                    lastAdTime: userData.lastAdTime
                });
                
                showMessage('+৫ পয়েন্ট!', 'success');
                checkTimer();
            } else {
                showMessage('অ্যাড সম্পূর্ণ হয়নি', 'error');
            }
        } else {
            // Fallback
            userData.points += 5;
            userData.totalViews += 1;
            userData.lastAdTime = Date.now();
            
            await db.ref('users/' + userData.id).update({
                points: userData.points,
                totalViews: userData.totalViews,
                lastAdTime: userData.lastAdTime
            });
            
            showMessage('+৫ পয়েন্ট (টেস্ট)!', 'success');
            checkTimer();
        }
    } catch (error) {
        showMessage('অ্যাড দেখাতে সমস্যা', 'error');
        btn.classList.remove('disabled');
        btn.disabled = false;
    }
}

// ========== Referral ==========
function generateReferralLink() {
    return `https://t.me/EarnQuick_Official_bot/app?startapp=ref_${userData.id}`;
}

async function copyReferral() {
    try {
        await navigator.clipboard.writeText(generateReferralLink());
        showMessage('কপি হয়েছে!', 'success');
    } catch (error) {
        showMessage('কপি করতে সমস্যা', 'error');
    }
}

// ========== Tab ==========
function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    if (tab === 'referral') {
        document.getElementById('referralTab').classList.add('active');
    } else {
        document.getElementById('withdrawTab').classList.add('active');
    }
}

// ========== Withdraw ==========
function openWithdrawModal(method) {
    currentMethod = method;
    
    const methods = {
        'bkash': { name: 'বিকাশ', min: 4000, taka: 20 },
        'nagad': { name: 'নগদ', min: 4000, taka: 20 },
        'rocket': { name: 'রকেট', min: 4000, taka: 20 },
        'recharge': { name: 'মোবাইল রিচার্জ', min: 2000, taka: 10 }
    };
    
    const m = methods[method];
    
    if (userData.points < m.min) {
        showMessage(`প্রয়োজন ${m.min} পয়েন্ট`, 'error');
        return;
    }
    
    document.getElementById('modalTitle').textContent = m.name;
    document.getElementById('modalInfo').textContent = `${m.min} পয়েন্ট = ${m.taka} টাকা`;
    document.getElementById('withdrawModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('withdrawModal').style.display = 'none';
    document.getElementById('withdrawPhone').value = '';
}

async function processWithdraw() {
    const phone = document.getElementById('withdrawPhone').value;
    
    if (!phone || phone.length < 11) {
        showMessage('সঠিক নম্বর দিন', 'error');
        return;
    }
    
    const methods = {
        'bkash': { min: 4000, taka: 20 },
        'nagad': { min: 4000, taka: 20 },
        'rocket': { min: 4000, taka: 20 },
        'recharge': { min: 2000, taka: 10 }
    };
    
    const m = methods[currentMethod];
    
    userData.points -= m.min;
    await db.ref('users/' + userData.id).update({ points: userData.points });
    
    showMessage('উইথড্র রিকোয়েস্ট জমা হয়েছে', 'success');
    closeModal();
    updateUI();
}

// ========== Message ==========
function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.className = 'message ' + type;
    msg.style.display = 'block';
    setTimeout(() => {
        msg.style.display = 'none';
    }, 2000);
}

// ========== Start ==========
window.onload = loadUser;
