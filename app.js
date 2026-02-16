const API = "https://earnquick-backend.onrender.com";

async function join(){
  const tgId = document.getElementById("tgId").value;
  const name = document.getElementById("name").value;

  const res = await fetch(API + "/join", {
    method:"POST",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ telegram_id: tgId, name: name })
  });

  document.getElementById("msg").innerText = "Joined!";
  loadProfile(tgId);
}

async function watchAd(){
  const tgId = document.getElementById("tgId").value;

  // AD SCRIPT
  var s = document.createElement("script");
  s.src = "https://5gvci.com/act/files/tag.min.js";
  document.body.appendChild(s);

  const res = await fetch(API + "/watch", {
    method:"POST",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ telegram_id: tgId })
  });

  const data = await res.json();
  document.getElementById("balance-btn").innerText = "Balance: " + data.points;
}

async function withdraw(){
  const tgId = document.getElementById("tgId").value;

  const res = await fetch(API + "/withdraw", {
    method:"POST",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ telegram_id: tgId })
  });

  const data = await res.json();
  document.getElementById("msg").innerText = data.message;
}

async function loadProfile(id){
  const res = await fetch(API + "/user/" + id);
  const data = await res.json();
  document.getElementById("balance-btn").innerText = "Balance: " + data.points;
}
