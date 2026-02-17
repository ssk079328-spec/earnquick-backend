// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyBTTbaQel2ih7-znAv1t8lDRZYjPfkASYY",
    authDomain: "earnbotdb.firebaseapp.com",
    databaseURL: "https://earnbotdb-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "earnbotdb",
    storageBucket: "earnbotdb.firebasestorage.app",
    messagingSenderId: "873493967952",
    appId: "1:873493967952:web:5a2ce9d5ee213a748d0d55"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Export for use
window.db = database;
