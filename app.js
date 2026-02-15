const API = "https://earnquick-backend.onrender.com";

function join(id,name){
 fetch(API+"/join",{method:"POST",
 headers:{"Content-Type":"application/json"},
 body:JSON.stringify({telegram_id:id,name})})
 .then(r=>r.json()).then(d=>alert(d.msg));
}

function watch(id){
 fetch(API+"/watch",{method:"POST",
 headers:{"Content-Type":"application/json"},
 body:JSON.stringify({telegram_id:id})})
 .then(r=>r.json()).then(d=>alert(d.msg));
}

function withdraw(id){
 fetch(API+"/withdraw",{method:"POST",
 headers:{"Content-Type":"application/json"},
 body:JSON.stringify({telegram_id:id})})
 .then(r=>r.json()).then(d=>alert(d.msg));
}
