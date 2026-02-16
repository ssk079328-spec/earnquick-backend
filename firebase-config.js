// Firebase configuration
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "earnbotdb.firebaseapp.com",
  databaseURL: "https://earnbotdb-default-rtdb.asia-southeast1.firebasedatabase.app/",
  projectId: "earnbotdb",
  storageBucket: "earnbotdb.appspot.com",
  messagingSenderId: "8320840106",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.database();
