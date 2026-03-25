import React from 'react';
import { useLocation, Link } from 'react-router-dom';

const TeamResults = () => {
  const location = useLocation();
  const fromState = location.state?.team;
  const saved = localStorage.getItem('last_generated_team');
  const team = fromState || (saved ? JSON.parse(saved) : null);

  const getSelectionReason = (member) => {
    const reasons = [];
    const score = Number(member.matchScore || member.Overall_Score || 0);
    if (score >= 80) reasons.push('High skill-to-project match');
    if ((member.availability || '').toLowerCase() === 'available') reasons.push('Currently available');
    if (Number(member.experience || member.Experience || 0) >= 3) reasons.push('Strong experience level');
    return reasons.length > 0 ? reasons.join(' | ') : 'Selected by K-Means cluster and attention score.';
  };

  const getTeams = () => {
    if (!team) return [];
    if (Array.isArray(team.teams) && team.teams.length > 0) {
      return team.teams;
    }
    const members = Array.isArray(team.members) ? team.members : [];
    if (members.length === 0) return [];
    const fallbackTeamCount = Math.max(1, Number(team.numberOfTeams || team?.kmeans?.selectedK || 2));
    const grouped = Array.from({ length: fallbackTeamCount }, (_, i) => ({
      teamName: `Team ${i + 1}`,
      members: [],
    }));
    members.forEach((m, i) => grouped[i % fallbackTeamCount].members.push(m));
    return grouped;
  };

  const teams = getTeams();

  return (
    <>
      <header className="header">
        <h1>Team Results</h1>
        <div className="header-actions">
          <Link className="btn btn-neutral" to="/team">
            Back To Formation
          </Link>
        </div>
      </header>

      {!team ? (
        <div className="empty-state">
          <h3>No results available</h3>
          <p>Generate a team first from the AI Team Formation page.</p>
        </div>
      ) : (
        <section className="result-box">
          <div className="result-top">
            <h2>{team.teamName || 'Generated Team'}</h2>
            <div className="user">{team.projectName || 'AI Project'}</div>
          </div>
          {teams.map((group, groupIndex) => (
            <section key={`${group.teamName}-${groupIndex}`} style={{ marginBottom: '18px' }}>
              <h3 style={{ marginBottom: '10px' }}>{group.teamName}</h3>
              <div className="team-grid">
                {(group.members || []).map((member, index) => (
                  <article className="team-card profile-card" key={`${group.teamName}-${member.id || index}`}>
                    <h3>{member.name || member['First Name']}</h3>
                    <div className="team-member">
                      <div>
                        <strong>Role:</strong> {member.role || '-'}
                      </div>
                      <div>
                        <strong>Skills:</strong> {member.skills || '-'}
                      </div>
                      <div>
                        <strong>Experience:</strong> {member.experience || member.Experience || 0} years
                      </div>
                      <div>
                        <strong>Score:</strong> {Number(member.matchScore || member.Overall_Score || 0).toFixed(0)}%
                      </div>
                      <div className="selection-reason">
                        <strong>Selection Reason:</strong> {getSelectionReason(member)}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </section>
      )}
    </>
  );
};

export default TeamResults;
