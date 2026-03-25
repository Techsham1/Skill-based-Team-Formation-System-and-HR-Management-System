import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateTeamWithAI, getEmployees } from '../utils/api';

const LOCAL_CONFIG_KEY = 'team_algorithm_config';

const CRITERIA_OPTIONS = [
  {
    id: 'technical_skills',
    title: 'Technical Skills',
    description: 'Distribute programming and technical expertise evenly',
    defaultChecked: true,
  },
  {
    id: 'problem_solving',
    title: 'Problem-Solving Ability',
    description: 'Mix analytical and creative problem solvers',
    defaultChecked: true,
  },
  {
    id: 'role_expertise',
    title: 'Role-Based Expertise',
    description: 'Include diverse roles (Dev, QA, Designer, etc.)',
    defaultChecked: true,
  },
  {
    id: 'adaptability',
    title: 'Adaptability',
    description: 'Balance employees who are flexible and learning-oriented',
    defaultChecked: false,
  },
  {
    id: 'communication',
    title: 'Communication Skills',
    description: 'Promote collaboration and team communication',
    defaultChecked: false,
  },
];

const BASIS_TO_SKILLS = {
  'Technical Skills': 'frontend,backend,database,devops',
  'Problem Solving': 'analytics,data_science,testing',
  'Role Balance': 'leadership,communication,project_management',
  'Experience Mix': 'experience,leadership,communication',
};

const TeamFormation = () => {
  const navigate = useNavigate();
  const [numberOfTeams, setNumberOfTeams] = useState(2);
  const [preferredTeamSize, setPreferredTeamSize] = useState(5);
  const [primaryBasis, setPrimaryBasis] = useState('Technical Skills');
  const [requiredRole, setRequiredRole] = useState('');
  const [criteriaState, setCriteriaState] = useState(
    CRITERIA_OPTIONS.reduce((acc, c) => ({ ...acc, [c.id]: c.defaultChecked }), {})
  );
  const [candidateCount, setCandidateCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadCandidates = async () => {
      try {
        const candidates = await getEmployees();
        setCandidateCount(candidates.length);
      } catch (loadError) {
        setCandidateCount(0);
      }
    };
    loadCandidates();
  }, []);

  const selectedCriteria = useMemo(
    () => CRITERIA_OPTIONS.filter((c) => criteriaState[c.id]).map((c) => c.title),
    [criteriaState]
  );

  const previewText = useMemo(() => {
    const teamSize = Number(preferredTeamSize || 0);
    const teamCount = Number(numberOfTeams || 0);
    const plannedPeople = teamSize * teamCount;
    return `${teamCount} teams x ${teamSize} members = ${plannedPeople} planned`;
  }, [preferredTeamSize, numberOfTeams]);

  const toggleCriteria = (id) => {
    setCriteriaState((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const fallbackGenerateTeam = async () => {
    const candidates = await getEmployees();
    if (!candidates || candidates.length === 0) {
      throw new Error('No candidates available for team generation.');
    }
    const requiredRoleNormalized = String(requiredRole || '').trim().toLowerCase();

    const selected = CRITERIA_OPTIONS.filter((c) => criteriaState[c.id]).map((c) =>
      c.title.toLowerCase()
    );
    const primarySkills = (BASIS_TO_SKILLS[primaryBasis] || '')
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean);

    const roleFilteredCandidates = requiredRoleNormalized
      ? candidates.filter((candidate) => {
          const roleText = String(candidate.role || '').toLowerCase();
          const deptText = String(candidate.department || '').toLowerCase();
          return roleText.includes(requiredRoleNormalized) || deptText.includes(requiredRoleNormalized);
        })
      : candidates;

    if (roleFilteredCandidates.length === 0) {
      throw new Error(`No candidates match the requested role: ${requiredRole}`);
    }

    const scored = roleFilteredCandidates
      .map((candidate) => {
        const skillsText = String(candidate.skills || '').toLowerCase();
        const skillHits = primarySkills.filter((sk) => skillsText.includes(sk)).length;
        const skillScore = primarySkills.length > 0 ? (skillHits / primarySkills.length) * 100 : 60;
        const exp = Number(candidate.experience || 0);
        const expScore = Math.min(100, exp * 10);
        const perfScore = Math.min(100, Number(candidate.performanceRating || candidate.score || 0) * 10);
        const availabilityScore =
          String(candidate.availability || 'Available').toLowerCase() === 'available' ? 100 : 60;

        let criteriaBonus = 0;
        if (selected.includes('technical skills') && skillScore >= 50) criteriaBonus += 8;
        if (selected.includes('problem-solving ability') && perfScore >= 60) criteriaBonus += 6;
        if (selected.includes('role-based expertise') && candidate.role) criteriaBonus += 5;
        if (selected.includes('adaptability')) criteriaBonus += 3;
        if (selected.includes('communication skills') && skillsText.includes('communication')) criteriaBonus += 4;

        const finalScore = (0.45 * skillScore) + (0.2 * expScore) + (0.25 * perfScore) + (0.1 * availabilityScore) + criteriaBonus;
        return {
          ...candidate,
          matchScore: Math.min(100, Number(finalScore.toFixed(2))),
        };
      })
      .sort((a, b) => b.matchScore - a.matchScore);

    const uniqueRanked = [];
    const seen = new Set();
    scored.forEach((c) => {
      const key = String(c.employeeId || c.id || `${c.name}-${c.role}`).toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      uniqueRanked.push(c);
    });

    const teamCount = Math.max(1, Number(numberOfTeams) || 1);
    const teamSize = Math.max(1, Number(preferredTeamSize) || 1);
    const totalRequired = teamCount * teamSize;
    const pool = uniqueRanked.slice(0, Math.min(totalRequired, uniqueRanked.length));
    const teams = Array.from({ length: teamCount }, (_, i) => ({
      teamName: `Team ${i + 1}`,
      members: [],
    }));
    pool.forEach((member, idx) => {
      teams[idx % teamCount].members.push(member);
    });
    const members = teams.flatMap((t) => t.members);
    const avg = (arr) =>
      arr.length ? Number((arr.reduce((s, v) => s + Number(v || 0), 0) / arr.length).toFixed(2)) : 0;

    return {
      teamName: `${primaryBasis} Team`,
      projectName: `${primaryBasis} Formation`,
      projectPriority: 'Medium',
      algorithm: 'frontend-fallback-ranking',
      numberOfTeams: teamCount,
      kmeans: {
        selectedK: teamCount,
        minK: 1,
        maxK: 10,
        selectedCluster: 1,
      },
      statistics: {
        avgExperience: avg(members.map((m) => m.experience)),
        avgSkillLevel: avg(members.map((m) => m.skillLevel || 0)),
        avgPerformance: avg(members.map((m) => m.performanceRating || m.score || 0)),
        avgMatchScore: avg(members.map((m) => m.matchScore)),
        totalMembers: members.length,
      },
      teams,
      members,
    };
  };

  const generateTeam = async (e) => {
    e.preventDefault();
    setError('');

    if (!preferredTeamSize || preferredTeamSize < 2) {
      setError('Preferred Team Size must be at least 2.');
      return;
    }

    if (!numberOfTeams || numberOfTeams < 1) {
      setError('Number of Teams must be at least 1.');
      return;
    }

    setLoading(true);
    try {
      const employees = await getEmployees();
      if (!employees || employees.length === 0) {
        throw new Error('No employees available. Add HR data before generating teams.');
      }

      const storedConfig = localStorage.getItem(LOCAL_CONFIG_KEY);
      const payload = {
        criteria: {
          teamName: `${primaryBasis} Team`,
          projectName: `${primaryBasis} Formation`,
          projectPriority: 'Medium',
          teamSize: Number(preferredTeamSize),
          minExperience: criteriaState.experience ? 2 : 0,
          primarySkills: BASIS_TO_SKILLS[primaryBasis] || BASIS_TO_SKILLS['Technical Skills'],
          secondarySkills: selectedCriteria.join(','),
          requiredRole: requiredRole.trim(),
          employeeCategory: '',
          numberOfTeams: Number(numberOfTeams),
          formationBasis: primaryBasis,
        },
        config: storedConfig ? JSON.parse(storedConfig) : null,
        employees,
      };

      let team;
      try {
        team = await generateTeamWithAI(payload);
      } catch (apiError) {
        team = await fallbackGenerateTeam();
      }
      localStorage.setItem('last_generated_team', JSON.stringify(team));
      const generationCount = Number(localStorage.getItem('team_generation_count') || 0) + 1;
      localStorage.setItem('team_generation_count', String(generationCount));
      navigate('/results', { state: { team } });
    } catch (error) {
      setError(error?.message || 'Team generation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="header">
        <h1>Team Formation</h1>
        <div className="user">Admin User</div>
      </header>

      {error && <div className="message error">{error}</div>}

      <form onSubmit={generateTeam}>
        <section className="formation-layout">
          <article className="panel panel-strong">
            <h2 className="formation-title">Basic Settings</h2>

            <label htmlFor="numberOfTeams">Number Of Teams</label>
            <div className="inline-field">
              <input
                id="numberOfTeams"
                type="number"
                min="1"
                max="10"
                value={numberOfTeams}
                onChange={(e) => setNumberOfTeams(Number(e.target.value))}
              />
              <span>Teams</span>
            </div>
            <p className="helper-text">Divide employees into 1-10 teams</p>

            <label htmlFor="preferredTeamSize">Preferred Team Size</label>
            <div className="inline-field">
              <input
                id="preferredTeamSize"
                type="number"
                min="2"
                max="15"
                value={preferredTeamSize}
                onChange={(e) => setPreferredTeamSize(Number(e.target.value))}
              />
              <span>Members per team</span>
            </div>
            <p className="helper-text">Auto-adjust if total does not divide evenly</p>

            <label htmlFor="primaryFormationBasis">Primary Formation Basis</label>
            <select
              id="primaryFormationBasis"
              value={primaryBasis}
              onChange={(e) => setPrimaryBasis(e.target.value)}
            >
              <option>Technical Skills</option>
              <option>Problem Solving</option>
              <option>Role Balance</option>
              <option>Experience Mix</option>
            </select>
            <p className="helper-text">How should teams be primarily organized?</p>

            <label htmlFor="requiredRole">Required Role (Optional)</label>
            <input
              id="requiredRole"
              type="text"
              placeholder="e.g. Backend, QA, DevOps, Designer"
              value={requiredRole}
              onChange={(e) => setRequiredRole(e.target.value)}
            />
            <p className="helper-text">Only include candidates matching this role/department</p>

            <div className="config-preview">
              <h3>Configuration Preview</h3>
              <p>{previewText}</p>
              <p>Candidates Available: {candidateCount}</p>
              <p>Primary Basis: {primaryBasis}</p>
              <p>Required Role: {requiredRole.trim() || 'Any'}</p>
            </div>
          </article>

          <article className="panel panel-strong">
            <h2 className="formation-title">Formation Criteria</h2>
            <p className="helper-text">Select criteria for balanced team formation:</p>

            <div className="criteria-list">
              {CRITERIA_OPTIONS.map((criterion) => (
                <label key={criterion.id} className="criteria-item">
                  <input
                    type="checkbox"
                    checked={criteriaState[criterion.id]}
                    onChange={() => toggleCriteria(criterion.id)}
                  />
                  <div>
                    <strong>{criterion.title}</strong>
                    <p>{criterion.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </article>
        </section>

        <div className="formation-action">
          <button type="submit" disabled={loading}>
            {loading ? (
              <>
                <span className="loading-spinner" />
                Generating optimal team...
              </>
            ) : (
              'Generate Team'
            )}
          </button>
        </div>
      </form>
    </>
  );
};

export default TeamFormation;
