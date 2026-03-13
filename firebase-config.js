<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>EarnQuick - Task Rain Style</title>
    <script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-database-compat.js"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: linear-gradient(to bottom, #FFD194, #FFFBDA); min-height: 100vh; padding-bottom: 70px; }
        .profile-card { background: rgba(255, 255, 255, 0.3); margin: 15px; padding: 15px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.5); }
        .user-info { display: flex; align-items: center; gap: 10px; }
        .avatar { width: 45px; height: 45px; background: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #f39c12; }
        .balance { font-weight: bold; font-size: 18px; color: #333; }
        .section { display: none; padding: 10px; }
        .active-section { display: block; animation: fadeIn 0.5s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .card { background: #FFE8C5; margin-bottom: 15px; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid #FFD194; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .reward-badge { background: #fff; display: inline-block; padding: 5px 15px; border-radius: 20px; color: #d35400; font-weight: bold; margin: 10px 0; }
        .btn { padding: 12px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; width: 100%; margin-top: 10px; }
        .btn-claim { background: #27ae60; color: white; }
        .btn-blue { background: #3498db; color: white; }
        .navbar { position: fixed; bottom: 0; width: 100%; background: #fff; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); border-radius: 15px 15px 0 0; }
        .nav-item { text-align: center; color: #7f8c8d; font-size: 11px; flex: 1; }
        .nav-item i { font-size: 20px; display: block; margin-bottom: 3px; }
        .nav-item.active { color: #5D3FD3; }
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-content { background: #fff; width: 85%; padding: 20px; border-radius: 20px; text-align: center; }
    </style>
</head>
<body>
    <div id="welcomeModal" class="modal">
        <div class="modal-content">
            <h2>📢 নোটিস</h2>
            <p style="margin: 15px 0; color: #555;">স্বাগতম! জয়েন বোনাস ৫০ টাকা। প্রতি রেফারে ৬০ টাকা। ১০০% পেমেন্ট গ্যারান্টি।</p>
            <button class="btn btn-blue" onclick="document.getElementById('welcomeModal').style.display='none'">বুঝেছি</button>
        </div>
    </div>

    <div class="profile-card">
        <div class="user-info">
            <div class="avatar" id="avatar">U</div>
            <div>
                <h3 id="userName">Loading... <i class="fas fa-check-circle" style="color:#1da1f2"></i></h3>
                <p style="font-size:12px">রেফার: <span id="refCount">0</span></p>
            </div>
        </div>
        <div class="balance"><span id="balance">0.00</span> BDT</div>
    </div>

    <div id="homeSec" class="section active-section">
        <div class="card">
            <i class="fab fa-youtube" style="font-size:40px; color:red"></i>
            <h4>YouTube Task</h4>
            <div class="reward-badge">🎁 ১৫.০০ BDT</div>
            <button class="btn btn-blue" onclick="window.open('https://youtube.com', '_blank')">ওপেন লিঙ্ক</button>
            <button class="btn btn-claim" onclick="addMoney(15)">ভেরিফাই ও ক্লেইম</button>
        </div>
        <div class="card">
            <i class="fas fa-video" style="font-size:40px; color:#3498db"></i>
            <h4>বিজ্ঞাপন দেখুন</h4>
            <div class="reward-badge">💵 ১০.০০ BDT</div>
            <button class="btn btn-blue" onclick="watchAd()">প্লে বিজ্ঞাপন</button>
        </div>
    </div>

    <div id="withdrawSec" class="section">
        <div class="card">
            <h3>টাকা উত্তোলন</h3>
            <p style="margin:10px 0">মিনিমাম উইথড্র: ১০০০ টাকা</p>
            <input type="number" id="amount" placeholder="পরিমাণ" style="width:100%; padding:10px; margin-bottom:10px; border-radius:8px; border:1px solid #ccc">
            <button class="btn btn-claim">রিকোয়েস্ট পাঠান</button>
        </div>
    </div>

    <div class="navbar">
        <div class="nav-item active" onclick="switchTab('homeSec', this)"><i class="fas fa-home"></i>হোম</div>
        <div class="nav-item" onclick="switchTab('taskSec', this)"><i class="fas fa-tasks"></i>টাস্ক</div>
        <div class="nav-item" onclick="switchTab('withdrawSec', this)"><i class="fas fa-wallet"></i>উইথড্র</div>
        <div class="nav-item" onclick="switchTab('supportSec', this)"><i class="fas fa-headset"></i>সাপোর্ট</div>
    </div>

    <script src="firebase-config.js"></script>
    <script src="app.js"></script>
    <script src="//libtl.com/sdk.js" data-zone="10603637" data-sdk="show_10603637" async></script>
</body>
</html>
