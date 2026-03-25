// ✅ LOAD
function loadEmployees(){
  return JSON.parse(localStorage.getItem("employees")) || [];
}

let employees = loadEmployees();

function refreshEmployees(){
  employees = loadEmployees();
}


// ✅ DYNAMIC SKILL LIST
function getAllSkills(){
  let set = new Set();
  employees.forEach(e=>{
    (e.skills || "").split(",").forEach(s=>set.add(s.trim()));
  });
  return Array.from(set);
}


// ✅ VECTOR
function getVector(skills, allSkills){
  return allSkills.map(skill => skills.includes(skill) ? 1 : 0);
}


// ✅ COSINE
function cosine(A,B){
  let dot=0,a=0,b=0;

  for(let i=0;i<A.length;i++){
    dot += A[i]*B[i];
    a += A[i]*A[i];
    b += B[i]*B[i];
  }

  if(a===0 || b===0) return 0;

  return dot / (Math.sqrt(a)*Math.sqrt(b));
}


// ✅ PARSE SKILL PRIORITY (java:10,react:5)
function parseSkillPriority(input){

  let obj = {};

  input.split(",").forEach(item=>{
    let [skill,weight] = item.split(":");
    obj[skill.trim()] = parseFloat(weight) || 5;
  });

  return obj;
}


// ✅ FINAL AI SCORE (ADVANCED 🔥)
function calculateScore(emp, projSkills, weights){

  let empSkills = (emp.skills || "").toLowerCase().split(",");
  let allSkills = getAllSkills();

  let empVector = getVector(empSkills, allSkills);
  let projVector = getVector(projSkills, allSkills);

  let skillScore = cosine(empVector, projVector);

  // 🔥 weighted skill boost
  let weighted = 0;
  projSkills.forEach(s=>{
    if(empSkills.includes(s)){
      weighted += weights[s] || 5;
    }
  });

  let maxWeight = Object.values(weights).reduce((a,b)=>a+b,0) || 1;
  let weightedScore = weighted / maxWeight;

  let exp = Math.min((emp.experience||0)/10,1);
  let perf = (emp.performanceRating||5)/10;
  let comm = (emp.communication||5)/10;

  return (skillScore*0.4) + (weightedScore*0.2) + (exp*0.2) + (perf*0.1) + (comm*0.1);
}


// ✅ MATCH FUNCTION (PREMIUM UI)
function matchEmployees(){

  refreshEmployees();

  let input = document.getElementById("skillsInput").value.toLowerCase();
  let list = document.getElementById("resultList");

  if(!input){
    alert("Enter skills ❌");
    return;
  }

  let weights = parseSkillPriority(input);
  let projSkills = Object.keys(weights);

  let results = employees.map(emp=>{
    return {
      name: emp.name,
      score: calculateScore(emp, projSkills, weights)
    };
  });

  // SORT
  results.sort((a,b)=>b.score-a.score);

  list.innerHTML="";

  results.slice(0,10).forEach((emp,index)=>{

    let percent = (emp.score*100).toFixed(1);

    let statusClass =
      emp.score>=0.8 ? "best" :
      emp.score>=0.5 ? "mid" : "low";

    let div = document.createElement("div");
    div.className="result-card";

    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;">
        <strong>#${index+1} ${emp.name}</strong>
        <span>${percent}%</span>
      </div>

      <div class="bar">
        <div class="fill" style="width:${percent}%"></div>
      </div>

      <span class="tag ${statusClass}">
        ${statusClass.toUpperCase()}
      </span>
    `;

    list.appendChild(div);
  });
}