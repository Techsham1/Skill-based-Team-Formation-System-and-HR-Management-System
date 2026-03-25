import React, { useState, useEffect } from 'react';
import { getEmployees } from '../utils/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCandidates: 0,
    clustersCreated: 0,
    teamsGenerated: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const candidates = await getEmployees();
        const lastTeamRaw = localStorage.getItem('last_generated_team');
        const historyRaw = localStorage.getItem('team_generation_count');

        let clustersCreated = 0;
        if (lastTeamRaw) {
          const lastTeam = JSON.parse(lastTeamRaw);
          clustersCreated = Number(lastTeam?.kmeans?.selectedK || 0);
        }

        setStats({
          totalCandidates: candidates.length,
          clustersCreated,
          teamsGenerated: Number(historyRaw || 0),
        });
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="header">
        <h1>Dashboard</h1>
        <div className="user">AI Team Workspace</div>
      </header>

      <div className="cards">
        <div className="card blue">
          <h3>Total Candidates</h3>
          <p>{loading ? '...' : stats.totalCandidates}</p>
        </div>
        <div className="card green">
          <h3>Clusters Created</h3>
          <p>{loading ? '...' : stats.clustersCreated}</p>
        </div>
        <div className="card orange">
          <h3>Teams Generated</h3>
          <p>{loading ? '...' : stats.teamsGenerated}</p>
        </div>
      </div>

      <section className="welcome">
        <h2>AI Candidate Intelligence</h2>
        <p>Manage candidate profiles, form optimal teams, and inspect selection logic in one flow.</p>
      </section>
    </>
  );
};

export default Dashboard;
