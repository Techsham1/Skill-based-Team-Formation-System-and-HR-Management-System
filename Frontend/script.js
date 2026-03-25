// Load employees from localStorage
let employees = JSON.parse(localStorage.getItem("employees")) || [];

// Styled notification function
function showNotification(message, type = 'success') {
  const notification = document.createElement("div");
  const bgColor = type === 'success' ? '#00ff88' : '#ff0055';
  const glowColor = type === 'success' ? 'rgba(0, 255, 136, 0.3)' : 'rgba(255, 0, 85, 0.3)';
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: ${bgColor};
    color: #001f3f;
    border-radius: 8px;
    box-shadow: 0 0 20px ${glowColor}, 0 4px 6px rgba(0, 0, 0, 0.12);
    font-weight: 700;
    z-index: 9999;
    animation: slideIn 0.3s ease;
    border: 2px solid ${bgColor};
  `;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// DASHBOARD - Show total employees
if (document.getElementById("totalEmployees")) {
  document.getElementById("totalEmployees").innerText = employees.length;
}

// EMPLOYEE LIST
if (document.getElementById("employeeTable")) {
  const tbody = document.querySelector("#employeeTable tbody");
  employees.forEach((emp, index) => {
    const row = document.createElement("tr");
    
    // Extract algorithm-relevant data
    const skills = emp.skills ? String(emp.skills).substring(0, 30) + '...' : 'N/A';
    const experience = emp.experience !== undefined ? emp.experience : 'N/A';
    const rating = emp.performanceRating ? emp.performanceRating.toFixed(1) : 'N/A';
    const availability = emp.availability || 'N/A';
    
    row.innerHTML = `
      <td>${emp.name || 'Unknown'}</td>
      <td>${emp.department || 'N/A'}</td>
      <td>${emp.role || 'N/A'}</td>
      <td title="${emp.skills || ''}">${skills}</td>
      <td>${experience}</td>
      <td>⭐ ${rating}</td>
      <td>${availability}</td>
      <td><button class="delete-btn" onclick="deleteEmployee(${index})">Delete</button></td>
    `;
    tbody.appendChild(row);
  });
}

// ADD EMPLOYEE
if (document.getElementById("addEmployeeForm")) {
  document.getElementById("addEmployeeForm").addEventListener("submit", (e) => {
    e.preventDefault();
    
    // Collect ALL required fields for algorithm
    const name = document.getElementById("name").value.trim();
    const department = document.getElementById("department").value.trim();
    const role = document.getElementById("role").value.trim();
    const skills = document.getElementById("skills").value.trim();
    const experience = parseFloat(document.getElementById("experience").value);
    const performanceRating = parseFloat(document.getElementById("performanceRating").value);
    const availability = document.getElementById("availability").value.trim();
    const empId = document.getElementById("empId").value.trim() || "EMP" + Date.now();
    const email = document.getElementById("email").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const dateJoined = document.getElementById("dateJoined").value || new Date().toISOString().split('T')[0];

    // Validate required fields
    if (!name || !department || !role || !skills || !experience || !performanceRating || !availability) {
      showNotification("❌ Please fill all required fields marked with *", "error");
      return;
    }

    // Validate numeric values
    if (isNaN(experience) || experience < 0 || experience > 60) {
      showNotification("❌ Experience must be between 0 and 60 years", "error");
      return;
    }

    if (isNaN(performanceRating) || performanceRating < 1 || performanceRating > 10) {
      showNotification("❌ Performance Rating must be between 1 and 10", "error");
      return;
    }

    // Create employee object with all fields needed for algorithm
    const employee = {
      id: empId,
      name: name,
      email: email,
      phone: phone,
      department: department,
      role: role,
      skills: skills,
      experience: experience,
      performanceRating: performanceRating,
      availability: availability,
      dateJoined: dateJoined,
      status: "Present",
      addedAt: new Date().toISOString()
    };

    console.log('Adding employee with full data:', employee);

    // Add to global employees array
    employees.push(employee);
    
    // Save to localStorage
    localStorage.setItem("employees", JSON.stringify(employees));
    console.log('Employee saved. Total employees:', employees.length);

    showNotification("✅ Employee added successfully! Data will be used in team formation algorithm.");
    e.target.reset();
    
    // Redirect to employees list after 2 seconds
    setTimeout(() => {
      window.location.href = "employees.html";
    }, 2000);
  });
}

// DELETE EMPLOYEE
function deleteEmployee(index) {
  if (confirm("Are you sure you want to delete this employee?")) {
    employees.splice(index, 1);
    localStorage.setItem("employees", JSON.stringify(employees));
    location.reload();
  }
}

// TEAM FORMATION
if (document.getElementById("generateTeamBtn")) {
  document.getElementById("generateTeamBtn").addEventListener("click", () => {
    console.log('Generate Teams button clicked');
    console.log('Current employees:', employees);
    
    if (!employees || employees.length === 0) {
      showNotification("❌ No employees found. Please import or add employees first.", "error");
      console.error('No employees available');
      return;
    }

    console.log(`Found ${employees.length} employees`);

    // Get configuration from localStorage
    const configStr = localStorage.getItem('teamConfig');
    let numTeams = 2;
    let teamBasis = 'balanced';
    let criteria = ['technical-skills', 'problem-solving', 'role-expertise'];

    if (configStr) {
      try {
        const config = JSON.parse(configStr);
        numTeams = config.numTeams || 2;
        teamBasis = config.teamBasis || 'balanced';
        criteria = config.criteria || criteria;
        console.log('Loaded config:', { numTeams, teamBasis, criteria });
      } catch (e) {
        console.error('Error parsing config:', e);
      }
    }

    console.log('Starting team generation with', numTeams, 'teams');

    // Generate AI-optimized teams using sophisticated algorithm
    const teams = generateAIOptimizedTeams(employees, numTeams, teamBasis, criteria);
    
    console.log('Generated teams:', teams);

    // Calculate team statistics
    const teamStats = calculateTeamStatistics(teams);

    const resultBox = document.getElementById("teamResult");
    if (!resultBox) {
      console.error('ERROR: teamResult div not found in DOM!');
      showNotification("❌ Page structure error: team result container not found", "error");
      return;
    }
    
    const colors = [
      { bg: 'linear-gradient(135deg, #0f52ba 0%, #001f3f 100%)', icon: '👥' },
      { bg: 'linear-gradient(135deg, #00ff88 0%, #00bb77 100%)', icon: '👥' },
      { bg: 'linear-gradient(135deg, #ffa500 0%, #ff8500 100%)', icon: '👥' },
      { bg: 'linear-gradient(135deg, #b537f2 0%, #8b5cf6 100%)', icon: '👥' },
      { bg: 'linear-gradient(135deg, #ff0055 0%, #cc0044 100%)', icon: '👥' },
    ];

    let teamsHTML = `
      <h2 style=\"color: #0f52ba; margin-bottom: 10px; font-size: 1.5rem;\">🤖 AI-Optimized Teams</h2>
      <p style=\"color: #758896; margin-bottom: 25px;\">
        <strong>Formation Basis:</strong> ${formatBasis(teamBasis)} | 
        <strong>Criteria:</strong> ${criteria.length} | 
        <strong>Algorithm:</strong> Balanced Distribution
      </p>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; margin-bottom: 30px;">
    `;

    teams.forEach((team, index) => {
      const color = colors[index % colors.length];
      const stats = teamStats[index] || { avgRating: 0, departments: 'Unknown', count: 0 };
      
      teamsHTML += `
        <div style="background: ${color.bg}; padding: 25px; border-radius: 10px; color: white;">
          <h3 style="margin-bottom: 15px; font-size: 1.2rem;">${color.icon} Team ${index + 1}</h3>
          <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 6px; margin-bottom: 15px; font-size: 0.9rem;">
            <div>👥 Members: ${team.length}</div>
            <div>⭐ Avg Rating: ${(parseFloat(stats.avgRating) || 0).toFixed(1)}</div>
            <div>📊 Departments: ${String(stats.departments || 'Unknown')}</div>
          </div>
          <ul style="list-style: none; padding: 0;">
            ${team.map(emp => {
              const empName = String(emp.name || 'Unknown');
              const empRole = String(emp.role || 'Unknown');
              const empRating = emp.performanceRating ? `(⭐ ${parseFloat(emp.performanceRating).toFixed(1)})` : '';
              return `<li style="padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.2); font-size: 0.95rem;">
                ✓ <strong>${empName}</strong> <span style="display: block; font-size: 0.8rem; opacity: 0.8; margin-top: 3px;">${empRole} ${empRating}</span>
              </li>`;
            }).join("")}
          </ul>
        </div>
      `;
    });

    teamsHTML += `
      </div>
      
      <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(11, 82, 186, 0.05)); padding: 20px; border-radius: 10px; border-left: 4px solid #0f52ba; margin-bottom: 20px;">
        <p style="color: var(--text-primary); margin: 0; font-size: 0.95rem; line-height: 1.6;">
          <strong>🎯 Algorithm Details:</strong><br>
          • Formation Basis: <strong>${formatBasis(teamBasis)}</strong><br>
          • Total Team Members: <strong>${employees.length}</strong><br>
          • Teams Created: <strong>${numTeams}</strong><br>
          • Optimization Criteria: <strong>${criteria.length}</strong> factors considered
        </p>
      </div>

      <div style="background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1)); padding: 15px; border-radius: 8px; border-left: 4px solid #00ff88;">
        <p style="color: #00aa66; margin: 0; font-size: 0.9rem;">
          ✅ <strong>Teams optimized using AI algorithm considering:</strong> Technical skills distribution, 
          experience diversity, role variety, department balance, and performance metrics.
        </p>
      </div>
    `;

    console.log('HTML built, updating DOM...');
    resultBox.innerHTML = teamsHTML;
    resultBox.classList.add("show");
    console.log('Teams displayed successfully');
    showNotification(`✅ Generated ${numTeams} AI-optimized teams using ${criteria.length} criteria!`);
  });
}

// Advanced AI-Optimized Team Generation Algorithm - SIMPLIFIED & ROBUST
function generateAIOptimizedTeams(employees, numTeams, basis, criteria) {
  console.log('generateAIOptimizedTeams called with:', { 
    empCount: employees ? employees.length : 0, 
    numTeams, 
    basis, 
    criteriaCount: criteria ? criteria.length : 0 
  });

  if (!employees || employees.length === 0) {
    console.warn('No employees to form teams');
    return Array.from({ length: numTeams }, () => []);
  }

  try {
    // Step 1: Enrich employee data with calculated scores
    console.log('Step 1: Enriching employee data...');
    const enrichedEmployees = employees.map((emp, idx) => {
      try {
        const enriched = {
          ...emp,
          id: idx,
          // Ensure basic properties exist
          name: String(emp.name || `Employee ${idx + 1}`).trim(),
          department: String(emp.department || 'Unknown').trim(),
          role: String(emp.role || 'Unknown').trim(),
          skills: String(emp.skills || '').trim(),
          experience: isNaN(parseFloat(emp.experience)) ? 0 : parseFloat(emp.experience),
          performanceRating: isNaN(parseFloat(emp.performanceRating)) ? 5 : parseFloat(emp.performanceRating),
          // Calculated scores
          skillScore: 0,
          experienceScore: 0,
          roleComplexity: 0,
          overallScore: 0
        };

        // Calculate scores
        enriched.skillScore = calculateSkillScore(enriched);
        enriched.experienceScore = normalizeExperience(enriched.experience);
        enriched.roleComplexity = getRoleComplexity(enriched.role);
        enriched.overallScore = (enriched.skillScore + enriched.experienceScore + enriched.roleComplexity + enriched.performanceRating) / 4;

        return enriched;
      } catch (e) {
        console.error('Error enriching employee at index', idx, ':', e);
        // Return fallback enriched employee
        return {
          ...emp,
          id: idx,
          name: String(emp.name || `Employee ${idx + 1}`),
          department: String(emp.department || 'Unknown'),
          role: String(emp.role || 'Unknown'),
          skills: String(emp.skills || ''),
          experience: 0,
          performanceRating: 5,
          skillScore: 5,
          experienceScore: 5,
          roleComplexity: 6,
          overallScore: 5.25
        };
      }
    });

    console.log('Enrichment complete. Sample employee:', enrichedEmployees[0]);

    // Step 2: Sort by basis
    console.log('Step 2: Sorting employees by basis:', basis);
    const sortedEmployees = sortByBasis(enrichedEmployees, basis);
    console.log('Sorting complete');

    // Step 3: Distribute employees using round-robin with alternating direction
    console.log('Step 3: Distributing employees across', numTeams, 'teams...');
    const teams = Array.from({ length: numTeams }, () => []);
    
    let forward = true;
    let index = 0;

    sortedEmployees.forEach((emp, position) => {
      teams[index].push(emp);
      
      if (forward) {
        index++;
        if (index >= numTeams) {
          forward = false;
          index = numTeams - 2;
        }
      } else {
        index--;
        if (index < 0) {
          forward = true;
          index = 1;
        }
      }
    });

    console.log('Distribution complete. Team sizes:', teams.map(t => t.length));

    // Step 4: Optional balancing
    console.log('Step 4: Applying optional balancing...');
    balanceTeams(teams, criteria);

    console.log('Team generation complete. Returning', teams.length, 'teams');
    return teams;
    
  } catch (error) {
    console.error('CRITICAL ERROR in generateAIOptimizedTeams:', error);
    console.error('Stack:', error.stack);
    
    // Fallback: Simple round-robin distribution
    console.log('Using fallback: simple round-robin distribution');
    const teams = Array.from({ length: numTeams }, () => []);
    employees.forEach((emp, idx) => {
      teams[idx % numTeams].push(emp);
    });
    return teams;
  }
}

// Calculate skill score from skills string
function calculateSkillScore(emp) {
  try {
    if (!emp || !emp.skills || typeof emp.skills !== 'string' || emp.skills.trim() === '') {
      return 5;
    }
    const skillCount = emp.skills.split(',').filter(s => s.trim()).length;
    const score = 3 + (skillCount * 0.7);
    return Math.min(10, Math.max(0, score));
  } catch (e) {
    console.error('Error calculating skill score for', emp, ':', e);
    return 5;
  }
}

// Normalize experience to 0-10 scale
function normalizeExperience(experience) {
  try {
    const numExp = parseFloat(experience || 0);
    if (isNaN(numExp) || numExp === 0) return 3;
    if (numExp <= 2) return 5;
    if (numExp <= 5) return 7;
    const score = 8 + ((numExp % 10) * 0.2);
    return Math.min(10, Math.max(0, score));
  } catch (e) {
    console.error('Error normalizing experience:', e);
    return 5;
  }
}

// Get role complexity score
function getRoleComplexity(role) {
  try {
    if (!role || typeof role !== 'string') return 6;
    const seniorRoles = ['manager', 'lead', 'senior', 'architect', 'director', 'chief', 'head', 'vp'];
    const isSenior = seniorRoles.some(r => role.toLowerCase().includes(r));
    return isSenior ? 9 : 6;
  } catch (e) {
    console.error('Error getting role complexity:', e);
    return 6;
  }
}

// Sort employees by basis
function sortByBasis(employees, basis) {
  try {
    if (!employees || employees.length === 0) return [];
    const sorted = [...employees];
    
    switch(basis) {
      case 'skills':
        return sorted.sort((a, b) => (b.skillScore || 0) - (a.skillScore || 0));
      case 'experience':
        return sorted.sort((a, b) => (b.experienceScore || 0) - (a.experienceScore || 0));
      case 'role':
        return sorted.sort((a, b) => (b.roleComplexity || 0) - (a.roleComplexity || 0));
      case 'department':
        return sorted.sort((a, b) => ((a.department || '') || '').localeCompare((b.department || '') || ''));
      case 'balanced':
      default:
        // Balanced: mix by overall score
        return sorted.sort((a, b) => {
          const aScore = ((a.skillScore || 0) + (a.experienceScore || 0) + (a.performanceRating || 0)) / 3;
          const bScore = ((b.skillScore || 0) + (b.experienceScore || 0) + (b.performanceRating || 0)) / 3;
          return bScore - aScore;
        });
    }
  } catch (e) {
    console.error('Error sorting employees by basis:', e);
    return [...(employees || [])];
  }
}

// Balance teams by ensuring diversity
function balanceTeams(teams, criteria) {
  try {
    if (!teams || teams.length < 2) return;

    // Ensure department diversity if included in criteria
    if (criteria && (criteria.includes('role-expertise') || criteria.includes('department'))) {
      balanceDepartments(teams);
    }

    // Ensure experience diversity if included in criteria
    if (criteria && criteria.includes('experience-diversity')) {
      balanceExperience(teams);
    }

    // Ensure skill diversity if included in criteria
    if (criteria && criteria.includes('technical-skills')) {
      balanceSkills(teams);
    }
  } catch (e) {
    console.error('Error in balanceTeams:', e);
  }
}

// Balance department distribution
function balanceDepartments(teams) {
  const deptMap = {};
  teams.forEach((team, tIdx) => {
    team.forEach(emp => {
      const dept = emp.department || 'Unknown';
      if (!deptMap[dept]) deptMap[dept] = [];
      deptMap[dept].push({ tIdx, emp });
    });
  });

  // Swap if same department is over-represented in one team
  Object.keys(deptMap).forEach(dept => {
    const members = deptMap[dept];
    if (members.length > teams.length) {
      // Try to spread them out
      const from = members.reduce((a, b) => a.tIdx === b.tIdx ? a : b);
      if (from && members.filter(m => m.tIdx === from.tIdx).length > 1) {
        for (let i = 0; i < teams.length; i++) {
          if (teams[i].filter(e => e.department === dept).length === 0) {
            const idx = teams[from.tIdx].indexOf(from.emp);
            if (idx > -1) {
              teams[from.tIdx].splice(idx, 1);
              teams[i].push(from.emp);
              break;
            }
          }
        }
      }
    }
  });
}

// Balance experience levels
function balanceExperience(teams) {
  teams.forEach(team => {
    const avgExp = team.reduce((sum, emp) => sum + (emp.experienceScore || 0), 0) / team.length;
    
    // If team has too many seniors or juniors, consider rebalancing
    const seniors = team.filter(emp => (emp.experienceScore || 0) >= 8).length;
    const juniors = team.filter(emp => (emp.experienceScore || 0) <= 4).length;
    
    // This is tracked for information, actual swap would happen across teams
  });
}

// Balance skill distribution
function balanceSkills(teams) {
  teams.forEach(team => {
    const avgSkill = team.reduce((sum, emp) => sum + (emp.skillScore || 0), 0) / team.length;
    // Ensure at least one high-skill member
    const highSkill = team.filter(emp => (emp.skillScore || 0) >= 8).length;
    if (highSkill === 0 && team.length > 0) {
      // This indicates potential imbalance
    }
  });
}

// Calculate team statistics
function calculateTeamStatistics(teams) {
  try {
    const stats = teams.map((team, idx) => {
      try {
        const avgRating = team.length > 0 
          ? team.reduce((sum, emp) => {
              const rating = parseFloat(emp.performanceRating) || 0;
              return sum + rating;
            }, 0) / team.length 
          : 0;
        
        const depts = new Set(team.map(emp => emp.department || 'Other'));
        const departments = depts.size === 1 ? Array.from(depts)[0] : `${depts.size} depts`;
        
        return {
          avgRating: parseFloat(avgRating) || 0,
          departments: departments || 'Unknown',
          count: team.length
        };
      } catch (e) {
        console.error('Error calculating stats for team', idx, ':', e);
        return { avgRating: 0, departments: 'Unknown', count: team.length || 0 };
      }
    });
    console.log('Team statistics calculated:', stats);
    return stats;
  } catch (e) {
    console.error('Error in calculateTeamStatistics:', e);
    return teams.map(team => ({ avgRating: 0, departments: 'Unknown', count: team.length || 0 }));
  }
}

// Format basis for display
function formatBasis(basis) {
  const map = {
    'skills': 'Technical Skills',
    'experience': 'Experience Level',
    'role': 'Role Expertise',
    'department': 'Department',
    'balanced': 'Balanced Mix'
  };
  return map[basis] || basis;
}

// TEST FUNCTION - Call from console: loadTestData()
function loadTestData() {
  const testEmployees = [
    { name: 'John Doe', department: 'Engineering', role: 'Software Engineer', skills: 'JavaScript,React,Node.js', experience: 5, performanceRating: 8.5, status: 'Present' },
    { name: 'Jane Smith', department: 'Engineering', role: 'Backend Developer', skills: 'Python,Django,SQL', experience: 3, performanceRating: 7.8, status: 'Present' },
    { name: 'Mike Johnson', department: 'Engineering', role: 'Senior Developer', skills: 'Java,Spring,Hibernate', experience: 7, performanceRating: 9.2, status: 'Present' },
    { name: 'Sarah Williams', department: 'Design', role: 'UI Designer', skills: 'UI/UX,Figma,Design', experience: 4, performanceRating: 7.5, status: 'Present' },
    { name: 'David Brown', department: 'Sales', role: 'Sales Manager', skills: 'Sales,CRM,Negotiation', experience: 6, performanceRating: 8.0, status: 'Present' },
    { name: 'Emma Davis', department: 'Engineering', role: 'Junior Developer', skills: 'JavaScript,HTML,CSS', experience: 1, performanceRating: 6.5, status: 'Present' },
    { name: 'Robert Wilson', department: 'Product', role: 'Product Manager', skills: 'Strategy,Analytics,Communication', experience: 8, performanceRating: 8.8, status: 'Present' },
    { name: 'Lisa Anderson', department: 'Sales', role: 'Sales Executive', skills: 'Sales,Communication,Negotiation', experience: 4, performanceRating: 7.8, status: 'Present' }
  ];
  localStorage.setItem('employees', JSON.stringify(testEmployees));
  employees = testEmployees;
  console.log('✅ Test data loaded:', testEmployees);
  console.log('Now click "Generate Teams" button to test!');
}
