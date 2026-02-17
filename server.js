const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 10000;

// স্ট্যাটিক ফাইল সার্ভ করুন
app.use(express.static(path.join(__dirname, './')));

// API রাউট (ভবিষ্যতে যোগ করতে পারবেন)
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'Server is running' });
});

// সব রিকোয়েস্ট index.html-এ রিডাইরেক্ট (SPA সাপোর্ট)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
